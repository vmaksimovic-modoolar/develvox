# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
from lxml import etree

import datetime
from dateutil import tz
import pytz
import time
from string import Template
from datetime import datetime, timedelta
from odoo.exceptions import  Warning
from pdb import set_trace as bp

from itertools import groupby
from operator import itemgetter

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)  # Need for message in console.




class ProjectTaskNativeCalendar(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'


    #Tools
    def get_sec(self, from_time):
        h = from_time.hour
        m = from_time.minute
        s = from_time.second
        return int(h) * 3600 + int(m) * 60 + int(s)

    def to_tz(self, datetime, tz_name):
        tz = pytz.timezone(tz_name)
        return pytz.UTC.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(tz).replace(tzinfo=None)

    def to_naive_user_tz(self, datetime, tz_name):
        tz = tz_name and pytz.timezone(tz_name) or pytz.UTC
        return pytz.UTC.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(tz).replace(tzinfo=None)

    def to_naive_utc(self, datetime, tz_name):
        tz = tz_name and pytz.timezone(tz_name) or pytz.UTC
        return tz.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(pytz.UTC).replace(tzinfo=None)


    def _get_calendar_level(self, task_id, date_in, diff, direction="normal"):
        if task_id.project_id and task_id.project_id.use_calendar:
            return self._get_calendar_interval(task=task_id, date_in=date_in, diff=diff, direction=direction )
        else:
            return False


    def _get_date_from_level(self, levels, value=None, type_op=None):
        """
        :param levels: list of calendar level with leavs and attendance
        :param value: get to_Datetime or from_Datetime
        :param type_op: what return max,min or list
        :return:
        """

        obj_list = []
        for level in levels:
            if level["type"] == "attendance":
                obj_list.append(level[value])

        if type_op == "max" and obj_list:
            return fields.Datetime.to_string(max(obj_list))
        elif type_op == "min" and obj_list:
            return fields.Datetime.to_string(min(obj_list))
        elif type_op == "list" and obj_list:
            return obj_list
        else:
            return False

    def _get_calendar_interval(self, task, date_in, diff, direction=None):
        """
        :param task: Task obj for
        :param date_in: detetime start date or end date
        :param diff: timedelta
        :param direction: norma or revers mode: from start date or end date
        :return: list of leves calendar
        """

        attendance_ids = task.project_id.resource_calendar_id.attendance_ids
        global_leave_ids = task.project_id.resource_calendar_id.global_leave_ids
        ### tz
        tz_name = task.project_id.tz
        if tz_name:
            date_in = self.to_tz(date_in, tz_name)

        #normal
        if direction == "normal" and attendance_ids:
            return self._get_planned_interval(attendance_ids=attendance_ids,
                                              global_leave_ids=global_leave_ids,
                                              start_date=date_in, diff=diff,
                                              level=[], tz_name=tz_name, iteration=0)
        #revers
        if direction == "revers" and attendance_ids:
            return self._get_planned_interval_revers(attendance_ids=attendance_ids,
                                                     global_leave_ids=global_leave_ids,
                                                     end_date=date_in, diff=diff,
                                                     level=[], tz_name=tz_name, iteration=0)


    def _check_leave(self, global_leave_ids, dt_work_from, dt_work_to, tz_name):
        """

        :param global_leave_ids:leaves for calendar
        :param dt_work_from: working from datetime
        :param dt_work_to: working to datetime
        :param tz_name: timezone
        :return:
            True, False = Datetime period in leaves totaly
            False, list of new from and to Datetime = if need cut of from or to
            False, False = nothing need do, no leaves and cut of.
        """
        if tz_name:
            for global_leave_id in global_leave_ids:
                dt_leave_from = fields.Datetime.from_string(global_leave_id.date_from)
                dt_leave_to = fields.Datetime.from_string(global_leave_id.date_to)

                dt_leave_from = self.to_tz(dt_leave_from, tz_name)
                dt_leave_to = self.to_tz(dt_leave_to, tz_name)

                global_leave = not dt_leave_from > dt_work_from and not dt_leave_to < dt_work_to
                # _logger.warning("-----------||-----------------")
                # _logger.warning("")
                # _logger.warning("is leave = {}".format(global_leave))

                if not global_leave:
                    # result1 = dt_leave_from <= dt_work_from and dt_leave_to.date() == dt_work_from.date()
                    # result2 = dt_leave_to >= dt_work_to and dt_leave_from.date() == dt_work_to.date()

                    # _logger.warning("dt_leave_from {} <= dt_work_from {} = {}".format(dt_leave_from, dt_work_from, result1))
                    # _logger.warning("dt_leave_to {} == dt_work_from {}".format(dt_leave_to.date(), dt_work_from.date()))
                    # _logger.warning("")
                    # _logger.warning("dt_leave_to {} >= dt_work_to {} = {}".format(dt_leave_to, dt_work_to, result2))
                    # _logger.warning("dt_leave_from {} == dt_work_to {}".format(dt_leave_from.date(), dt_work_to.date()))

                    #change from
                    new_dt_work_from = dt_work_from
                    if dt_leave_from <= dt_work_from and dt_leave_to.date() == dt_work_from.date():
                        td_from = dt_leave_to - dt_work_from
                        if td_from.days == 0:
                            new_dt_work_from = dt_work_from + td_from
                            # _logger.warning("{} = {}".format(type(td_from), td_from))

                    #change to
                    new_dt_work_to = dt_work_to
                    if dt_leave_to >= dt_work_to and dt_leave_from.date() == dt_work_to.date():
                        td_to = dt_work_to - dt_leave_from
                        if td_to.days == 0:
                            new_dt_work_to = dt_work_to - td_to
                            # _logger.warning("{} = {}".format(type(td_to), td_to))

                    if new_dt_work_from != dt_work_from or new_dt_work_to != dt_work_to:
                        # _logger.warning("-- --")
                        # _logger.warning(new_dt_work_from)
                        # _logger.warning(new_dt_work_to)

                        return False,   {
                                            "name": global_leave_id.name,
                                            "from": new_dt_work_from,
                                            "to": new_dt_work_to
                                        }
                else:
                    return True, False

        return False, False


    def _get_planned_interval(self, attendance_ids, global_leave_ids, start_date, diff,
                              diff_e=None, level=None, tz_name=None, iteration=None ):
        """
         From Start to End DateTime , Get recusrsive working hour while duration > 0.
        :param attendance_ids:
        :param global_leave_ids:
        :param start_date:
        :param diff:
        :param diff_e:
        :param level:
        :param tz_name:
        :return:
        """


        weekday = start_date.weekday()
        attendances = attendance_ids.filtered(lambda att:
                                int(att.dayofweek) == weekday
                                and not (att.date_from and fields.Date.from_string(att.date_from) > start_date.date())
                                and not (att.date_to and fields.Date.from_string(att.date_to) < start_date.date())
                                )

        # _logger.warning("WeekDay: {}".format(weekday))

        if not diff_e:
            diff_e = diff

        date_to = False
        for attendance in attendances:
            hour_from = timedelta(hours=float(attendance.hour_from))
            hour_to = timedelta(hours=float(attendance.hour_to))

            hour_from_date = start_date.replace(hour=0, minute=0, second=0) + hour_from
            hour_to_date = start_date.replace(hour=0, minute=0, second=0) + hour_to

            #check global leave for calendar

            global_leave, cut_hour = self._check_leave(global_leave_ids,
                                                       dt_work_from=hour_from_date,
                                                       dt_work_to=hour_to_date, tz_name=tz_name)

            if cut_hour:

                hour_from_date = cut_hour["from"]
                hour_to_date = cut_hour["to"]

                hour_from = timedelta(seconds = self.get_sec(hour_from_date.time()))
                hour_to = timedelta(seconds = self.get_sec(hour_to_date.time()))

            if not global_leave:
                date_from = False
                summ_hours = timedelta(hours=0)

                if start_date <= hour_from_date:
                    date_from = hour_from_date
                    summ_hours = hour_to - hour_from
                elif hour_from_date <= start_date < hour_to_date:
                    date_from = start_date
                    summ_hours = hour_to_date - date_from

                if diff_e <= summ_hours:
                    summ_hours = diff_e

                if date_from and summ_hours > timedelta(hours=0):
                    diff_e = diff_e - summ_hours
                    date_to = date_from + summ_hours

                    if cut_hour:
                        cut_hour_from = self.to_naive_utc(cut_hour["from"], tz_name)
                        cut_hour_to = self.to_naive_utc(cut_hour["to"], tz_name)

                        level.append({"name": cut_hour["name"],
                                      "type": "cut",
                                      "date_from": cut_hour_from,
                                      "date_to": cut_hour_to,
                                      "interval": (cut_hour_to - cut_hour_from),
                                      "iteration": iteration
                                      })


                    date_from = self.to_naive_utc(date_from, tz_name)
                    date_to = self.to_naive_utc(date_to, tz_name)

                    level.append({  "name" : attendance.display_name,
                                    "type": "attendance",
                                    "date_from" : date_from,
                                    "date_to"   : date_to,
                                    "interval"  :(date_to - date_from),
                                    "iteration": iteration
                                  })




        if diff_e > timedelta(hours=0) and iteration < 2000:
            iteration += 1
            if not date_to:
                date_to = start_date

            date_to = (date_to + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            self._get_planned_interval(attendance_ids, global_leave_ids,date_to, diff,
                                       diff_e=diff_e, level=level, tz_name=tz_name, iteration=iteration)

        return level


    def _get_planned_interval_revers(self, attendance_ids, global_leave_ids, end_date, diff,
                                     diff_e=None, level=None,  tz_name=None, iteration=None ):
        """
         From Start to End DateTime , Get recusrsive working hour while duration > 0.
        :param attendance_ids:
        :param global_leave_ids:
        :param start_date:
        :param diff:
        :param diff_e:
        :param level:
        :param tz_name:
        :return:
        """

        weekday = end_date.weekday()
        attendances = attendance_ids.filtered(lambda att:
                        int(att.dayofweek) == weekday
                        and not (att.date_from and fields.Date.from_string(att.date_from) > end_date.date())
                        and not (att.date_to and fields.Date.from_string(att.date_to) < end_date.date())
                        )

        if not diff_e:
            diff_e = diff

        date_from = False
        for attendance in reversed(attendances):

            hour_from = timedelta(hours=float(attendance.hour_from))
            hour_to = timedelta(hours=float(attendance.hour_to))

            hour_from_date = end_date.replace(hour=0, minute=0, second=0) + hour_from
            hour_to_date = end_date.replace(hour=0, minute=0, second=0) + hour_to

            #check global leave for calendar

            global_leave, cut_hour = self._check_leave(global_leave_ids,
                                                       dt_work_from=hour_from_date,
                                                       dt_work_to=hour_to_date, tz_name=tz_name)

            if cut_hour:

                hour_from_date = cut_hour["from"]
                hour_to_date = cut_hour["to"]

                hour_from = timedelta(seconds = self.get_sec(hour_from_date.time()))
                hour_to = timedelta(seconds = self.get_sec(hour_to_date.time()))

            if not global_leave:

                date_to = False
                summ_hours = timedelta(hours=0)

                if end_date >= hour_to_date:
                    date_to = hour_to_date
                    summ_hours = hour_to - hour_from
                elif hour_from_date < end_date <= hour_to_date:
                    date_to = end_date
                    summ_hours = date_to - hour_from_date
                if diff_e <= summ_hours:
                    summ_hours = diff_e

                if date_to and summ_hours > timedelta(hours=0):
                    diff_e = diff_e - summ_hours
                    date_from = date_to - summ_hours

                    if cut_hour:
                        cut_hour_from = self.to_naive_utc(cut_hour["from"], tz_name)
                        cut_hour_to = self.to_naive_utc(cut_hour["to"], tz_name)

                        level.append({"name": cut_hour["name"],
                                      "type": "cut",
                                      "date_from": cut_hour_from,
                                      "date_to": cut_hour_to,
                                      "interval": (cut_hour_to - cut_hour_from),
                                      "iteration": iteration
                                      })


                    date_from = self.to_naive_utc(date_from, tz_name)
                    date_to = self.to_naive_utc(date_to, tz_name)

                    level.append({  "name" : attendance.display_name,
                                    "type": "attendance",
                                    "date_from" : date_from,
                                    "date_to"   : date_to,
                                    "interval"  :(date_to - date_from),
                                    "iteration": iteration
                                  })




        if diff_e > timedelta(hours=0) and iteration < 2000:
            iteration += 1
            if not date_from:
                date_from = end_date

            date_to = (date_from - timedelta(days=1)).replace(hour=23, minute=59, second=59)
            self._get_planned_interval_revers(attendance_ids,
                                              global_leave_ids,
                                              date_to, diff,
                                              diff_e=diff_e, level=level, tz_name=tz_name, iteration=iteration)

        return level




