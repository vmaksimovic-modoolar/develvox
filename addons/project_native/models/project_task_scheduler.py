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

_logger = logging.getLogger(__name__) # Need for message in console.




class ProjectTaskNativeScheduler(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'


    def _predecessor_lag_timedelta(self, parent_date, lag_qty, lag_type, parent_date_two, plan_type='forward'):

        diff = timedelta(days=0)

        if plan_type == 'backward':
            lag_qty = lag_qty * -1

        if lag_type == "day":
            diff = timedelta(days=lag_qty)
            return parent_date+diff

        if lag_type == "hour":
            diff = timedelta(seconds=lag_qty*3600)

        if lag_type == "minute":
            diff = timedelta(seconds=lag_qty*60)

        if lag_type == "percent":
            diff = parent_date - parent_date_two
            duration = diff.total_seconds()
            percent_second = (duration*abs(lag_qty))/100

            diff = timedelta(seconds=percent_second)

        if lag_qty > 0:
            return parent_date + diff
        else:
            return parent_date - diff



    def _add_detail_plan(self, task, calendar_level):
        task.detail_plan_ids.unlink()
        if calendar_level:
            task_detail_lines = []
            for level in calendar_level:
                value = {
                    "name": level["name"],
                    "type_level": level["type"],
                    "data_from": level["date_from"],
                    "data_to": level["date_to"],
                    "duration": level["interval"].total_seconds(),
                    "iteration": level["iteration"],
                }

                task_detail_lines.append((0, 0, value), )

            if task_detail_lines:
                task.write({'detail_plan_ids': task_detail_lines})


    def _before_scheduler_work(self, task, scheduling_type):


        if task.schedule_mode == "auto" and not task.child_ids: #(auto mode and task not group.)


            #Project Star and End Date

            date_start = fields.Datetime.from_string(task.project_id.date_start)
            date_end = fields.Datetime.from_string(task.project_id.date_end)

            #forward
            if scheduling_type == "forward":
                if not date_start:
                    pvals = {}
                    date_start = fields.datetime.now()
                    pvals['date_start'] = date_start
                    pvals['date_end'] = date_start + timedelta(seconds=86400)  # +1day

                    task.project_id.write(pvals)

                #Task Start and End Date
                plan_duration = task.plan_duration
                if plan_duration == 0:
                    plan_duration = 86400 # 1 day

                diff = timedelta(seconds=plan_duration)
                vals = {}

                #Calendar
                calendar_level = self._get_calendar_level(task, date_start, diff, direction="normal")
                if calendar_level: #use calendar
                    new_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                    new_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                else: #not use calendar
                    new_date_end = fields.Datetime.to_string(date_start + diff)
                    new_date_start = fields.Datetime.to_string(date_start)

                vals['date_start'] = new_date_start
                vals['date_end'] = new_date_end

                #check constrain
                vals_new, calendar_level_new = self._scheduler_work_constrain(task, vals, diff)
                if vals_new:
                    vals = vals_new

                if calendar_level_new:
                    calendar_level = calendar_level_new

                task.write(vals)

                self._add_detail_plan(task, calendar_level)





            #backward
            if scheduling_type == "backward":
                if not date_end:
                    pvals = {}
                    date_end = fields.datetime.now()
                    pvals['date_start'] =  date_end + timedelta(seconds=86400)
                    pvals['date_end'] = date_end

                    task.project_id.write(pvals)

                # Task Start and End Date
                plan_duration = task.plan_duration
                if plan_duration == 0:
                    plan_duration = 86400  # +1day
                diff = timedelta(seconds=plan_duration)

                vals = {}

                #Calendar
                calendar_level = self._get_calendar_level(task, date_end, diff, direction="revers")
                if calendar_level: #use calendar
                    new_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                    new_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                else: #not use calendar
                    new_date_start = fields.Datetime.to_string(date_end - diff)
                    new_date_end = fields.Datetime.to_string(date_end)


                vals['date_start'] = new_date_start
                vals['date_end'] = new_date_end

                #check constrain
                vals_new, calendar_level_new = self._scheduler_work_constrain(task, vals, diff)
                if vals_new:
                    vals = vals_new

                if calendar_level_new:
                    calendar_level = calendar_level_new

                task.write(vals)

                self._add_detail_plan(task, calendar_level)







    def _scheduler_work_forward(self, task):

        search_objs = self.env['project.task.predecessor'].sudo().search([('parent_task_id', '=', task.id)])

        for obj in search_objs:
            vals = {}

            calendar_level = []

            plan_duration = obj.task_id.plan_duration
            if plan_duration == 0:
                plan_duration = 86400 # 1 day
            diff = timedelta(seconds=plan_duration)

            search_data_objs = self.env['project.task.predecessor'].sudo().search([('task_id', '=', obj.task_id.id)])
            # Schedule Mode
            # FS
            if obj.type == "FS":
                date_list = []

                for date_obj in search_data_objs:
                    if date_obj.type == "FS":
                        parent_date = fields.Datetime.from_string(date_obj.parent_task_id.date_end)
                        #lag
                        if date_obj.lag_qty != 0:
                            parent_date_two = fields.Datetime.from_string(date_obj.parent_task_id.date_start)
                            parent_date = self._predecessor_lag_timedelta(parent_date, date_obj.lag_qty, date_obj.lag_type, parent_date_two)

                        date_list.append(parent_date)

                if date_list:

                    new_date_start = max(date_list)
                    calendar_level = self._get_calendar_level(obj.task_id, new_date_start, diff, direction="normal")

                    if calendar_level:
                        new_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                        new_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                    else:
                        new_date_end = fields.Datetime.to_string(new_date_start + diff)
                        new_date_start = fields.Datetime.to_string(new_date_start)

                    vals['date_start'] = new_date_start
                    vals['date_end'] = new_date_end

            if obj.type == "SS":
                date_list = []

                for date_obj in search_data_objs:
                    if date_obj.type == "SS":

                        parent_date = fields.Datetime.from_string(date_obj.parent_task_id.date_start)
                        #lag
                        if date_obj.lag_qty != 0:
                            parent_date_two = fields.Datetime.from_string(date_obj.parent_task_id.date_end)
                            parent_date = self._predecessor_lag_timedelta(parent_date, date_obj.lag_qty, date_obj.lag_type, parent_date_two)

                        date_list.append(parent_date)

                if date_list:
                    new_date_start = min(date_list)
                    calendar_level = self._get_calendar_level(obj.task_id, new_date_start, diff, direction="normal")
                    if calendar_level:
                        new_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                        new_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                    else:
                        new_date_end = fields.Datetime.to_string(new_date_start + diff)
                        new_date_start = fields.Datetime.to_string(new_date_start)


                    vals['date_start'] = new_date_start
                    vals['date_end'] = new_date_end

            if obj.type == "FF":
                date_list = []
                for date_obj in search_data_objs:
                    if date_obj.type == "FF":
                        parent_date = fields.Datetime.from_string(date_obj.parent_task_id.date_end)
                        #lag
                        if date_obj.lag_qty != 0:
                            parent_date_two = fields.Datetime.from_string(date_obj.parent_task_id.date_start)
                            parent_date = self._predecessor_lag_timedelta(parent_date, date_obj.lag_qty, date_obj.lag_type, parent_date_two)

                        date_list.append(parent_date)

                if date_list:
                    new_date_end = max(date_list)
                    calendar_level = self._get_calendar_level(obj.task_id, new_date_end, diff, direction="revers")
                    if calendar_level:
                        new_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                        new_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                    else:
                        new_date_start = fields.Datetime.to_string(new_date_end - diff)
                        new_date_end = fields.Datetime.to_string(new_date_end)



                    vals['date_start'] = new_date_start
                    vals['date_end'] = new_date_end


            if obj.type == "SF":
                date_list = []

                for date_obj in search_data_objs:
                    if date_obj.type == "SF":
                        parent_date = fields.Datetime.from_string(date_obj.parent_task_id.date_start)

                        #lag
                        if date_obj.lag_qty != 0:
                            parent_date_two = fields.Datetime.from_string(date_obj.parent_task_id.date_end)
                            parent_date = self._predecessor_lag_timedelta(parent_date, date_obj.lag_qty, date_obj.lag_type, parent_date_two )

                        date_list.append(parent_date)
                if date_list:
                    new_date_end = max(date_list)
                    calendar_level = self._get_calendar_level(obj.task_id, new_date_end, diff, direction="revers")
                    if calendar_level:
                        new_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                        new_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                    else:
                        new_date_start = fields.Datetime.to_string(new_date_end - diff)
                        new_date_end = fields.Datetime.to_string(new_date_end)



                    vals['date_start'] = new_date_start
                    vals['date_end'] = new_date_end


            vals_new, calendar_level_new = self._scheduler_work_constrain(obj.task_id, vals, diff)
            if vals_new:
                vals = vals_new
            if calendar_level_new:
                calendar_level = calendar_level_new

            if obj.task_id.schedule_mode == "auto" and vals:

                obj.task_id.write(vals)

                self._add_detail_plan(task, calendar_level)

                self._scheduler_work_forward(obj.task_id)


    def _scheduler_work_backward(self, task):

        search_objs = self.env['project.task.predecessor'].sudo().search([('task_id', '=', task.id)])

        for obj in search_objs:
            vals = {}
            calendar_level = []

            plan_duration = obj.parent_task_id.plan_duration
            if plan_duration == 0:
                plan_duration = 86400 # 1 day
            diff = timedelta(seconds=plan_duration)

            search_data_objs = self.env['project.task.predecessor'].sudo().search([('parent_task_id', '=', obj.parent_task_id.id)])
            # Schedule Mode
            if obj.type == "FS":
                date_list = []

                for date_obj in search_data_objs:
                    if date_obj.type == "FS":
                        parent_date = fields.Datetime.from_string(date_obj.task_id.date_start)
                        #lag
                        if date_obj.lag_qty != 0:
                            parent_date_two = fields.Datetime.from_string(date_obj.task_id.date_start)
                            parent_date = self._predecessor_lag_timedelta(parent_date,
                                                                         date_obj.lag_qty,
                                                                         date_obj.lag_type,
                                                                         parent_date_two, plan_type='backward')

                        date_list.append(parent_date)

                if date_list:
                    new_date_end = min(date_list)

                    calendar_level = self._get_calendar_level(obj.task_id, new_date_end, diff, direction="revers")
                    #use calendar
                    if calendar_level:
                        new_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                        new_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                    #not use calendar
                    else:
                        new_date_start = fields.Datetime.to_string(new_date_end - diff)
                        new_date_end = fields.Datetime.to_string(new_date_end)

                    vals['date_start'] = new_date_start
                    vals['date_end'] = new_date_end


            if obj.type == "SS":
                date_list = []
                for date_obj in search_data_objs:
                    if date_obj.type == "SS":
                        parent_date = fields.Datetime.from_string(date_obj.task_id.date_start)
                        #lag
                        if date_obj.lag_qty != 0:
                            parent_date_two = fields.Datetime.from_string(date_obj.task_id.date_start)
                            parent_date = self._predecessor_lag_timedelta(parent_date,
                                                                         date_obj.lag_qty,
                                                                         date_obj.lag_type,
                                                                         parent_date_two, plan_type='backward')

                        date_list.append(parent_date)

                if date_list:
                    new_date_start = min(date_list)

                    calendar_level = self._get_calendar_level(obj.task_id, new_date_start, diff, direction="normal")
                    #use calendar
                    if calendar_level:
                        new_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                        new_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                    #not use calendar
                    else:
                        new_date_end = fields.Datetime.to_string(new_date_start + diff)
                        new_date_start = fields.Datetime.to_string(new_date_start)


                    vals['date_start'] = new_date_start
                    vals['date_end'] = new_date_end

            if obj.type == "FF":
                date_list = []
                for date_obj in search_data_objs:
                    if date_obj.type == "FF":
                        parent_date = fields.Datetime.from_string(date_obj.task_id.date_end)
                        #lag
                        if date_obj.lag_qty != 0:
                            parent_date_two = fields.Datetime.from_string(date_obj.task_id.date_end)
                            parent_date = self._predecessor_lag_timedelta(parent_date,
                                                                         date_obj.lag_qty,
                                                                         date_obj.lag_type,
                                                                         parent_date_two, plan_type='backward')

                        date_list.append(parent_date)

                if date_list:
                    new_date_end = max(date_list)

                    calendar_level = self._get_calendar_level(obj.task_id, new_date_end, diff, direction="revers")
                    #use calendar
                    if calendar_level:
                        new_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                        new_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                    #not use calendar
                    else:
                        new_date_start = fields.Datetime.to_string(new_date_end - diff)
                        new_date_end = fields.Datetime.to_string(new_date_end)

                    vals['date_start'] = new_date_start
                    vals['date_end'] = new_date_end



            if obj.type == "SF":
                date_list = []

                for date_obj in search_data_objs:
                    if date_obj.type == "SF":
                        parent_date = fields.Datetime.from_string(date_obj.task_id.date_end)
                        #lag
                        if date_obj.lag_qty != 0:
                            parent_date_two = fields.Datetime.from_string(date_obj.task_id.date_end)
                            parent_date = self._predecessor_lag_timedelta(parent_date,
                                                                         date_obj.lag_qty,
                                                                         date_obj.lag_type,
                                                                         parent_date_two, plan_type='backward')

                        date_list.append(parent_date)

                if date_list:
                    new_date_start = min(date_list)

                    calendar_level = self._get_calendar_level(obj.task_id, new_date_start, diff, direction="normal")
                    #use calendar
                    if calendar_level:
                        new_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                        new_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                    #not use calendar
                    else:
                        new_date_end = fields.Datetime.to_string(new_date_start + diff)
                        new_date_start = fields.Datetime.to_string(new_date_start)


                    vals['date_start'] = new_date_start
                    vals['date_end'] = new_date_end



            vals_new, calendar_level_new = self._scheduler_work_constrain(obj.parent_task_id, vals, diff)
            if vals_new:
                vals = vals_new

            if calendar_level_new:
                calendar_level = calendar_level_new

            if obj.parent_task_id.schedule_mode == "auto" and vals:

                obj.parent_task_id.write(vals)
                self._add_detail_plan(task, calendar_level)

                self._scheduler_work_backward(obj.parent_task_id)


    def _scheduler_work_constrain(self, task_id, vals, diff):

        calendar_level = []
        vals_new = {}
        if task_id.constrain_type not in "asap" and task_id.constrain_date and vals:

            constrain_date = fields.Datetime.from_string(task_id.constrain_date)


            # Finish No Early Than
            if task_id.constrain_type == "fnet":
                sheduled_task_data = fields.Datetime.from_string(vals['date_end'])
                if sheduled_task_data < constrain_date:

                    calendar_level = self._get_calendar_level(task_id, constrain_date, diff, direction="revers")
                    if calendar_level: #use calendar
                        new_date = self._get_date_from_level(calendar_level, "date_from", "min")
                        task_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                    else: #not use calendar
                        task_date_end = fields.Datetime.to_string(constrain_date)
                        new_date = fields.Datetime.to_string(constrain_date - diff)

                    vals_new['date_start'] = new_date
                    vals_new['date_end'] = task_date_end


            # Finish No Later Than
            if task_id.constrain_type == "fnlt":

                sheduled_task_data = fields.Datetime.from_string(vals['date_end'])

                if sheduled_task_data > constrain_date:

                    calendar_level = self._get_calendar_level(task_id, constrain_date, diff, direction="revers")
                    if calendar_level: #use calendar
                        new_date = self._get_date_from_level(calendar_level, "date_from", "min")
                        task_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                    else: #not use calendar
                        task_date_end = fields.Datetime.to_string(constrain_date)
                        new_date = fields.Datetime.to_string(constrain_date - diff)

                    vals_new['date_start'] = new_date
                    vals_new['date_end'] = task_date_end


            # Must Start On
            if task_id.constrain_type == "mso":

                calendar_level = self._get_calendar_level(task_id, constrain_date, diff, direction="normal")
                if calendar_level:  # use calendar
                    task_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                    new_date = self._get_date_from_level(calendar_level, "date_to", "max")
                else:  # not use calendar
                    task_date_start = fields.Datetime.to_string(constrain_date)
                    new_date = fields.Datetime.to_string(constrain_date + diff)


                vals_new['date_start'] = task_date_start
                vals_new['date_end'] = new_date

            # Must Finish On
            if task_id.constrain_type == "mfo":

                calendar_level = self._get_calendar_level(task_id, constrain_date, diff, direction="revers")
                if calendar_level:  # use calendar
                    new_date = self._get_date_from_level(calendar_level, "date_from", "min")
                    task_date_end = self._get_date_from_level(calendar_level, "date_to", "max")
                else:  # not use calendar
                    task_date_end = fields.Datetime.to_string(constrain_date)
                    new_date = fields.Datetime.to_string(constrain_date - diff)

                vals_new['date_start'] = new_date
                vals_new['date_end'] = task_date_end


            # Start No Earlier Than
            if task_id.constrain_type == "snet":

                sheduled_task_data = fields.Datetime.from_string(vals['date_start'])

                if sheduled_task_data < constrain_date:

                    calendar_level = self._get_calendar_level(task_id, constrain_date, diff, direction="normal")
                    if calendar_level:  # use calendar
                        task_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                        new_date = self._get_date_from_level(calendar_level, "date_to", "max")
                    else:  # not use calendar
                        task_date_start = fields.Datetime.to_string(constrain_date)
                        new_date = fields.Datetime.to_string(constrain_date + diff)

                    vals_new['date_start'] = task_date_start
                    vals_new['date_end'] = new_date


            # Start No Later Than
            if task_id.constrain_type == "snlt":

                sheduled_task_data = fields.Datetime.from_string(vals['date_start'])

                if sheduled_task_data > constrain_date:

                    calendar_level = self._get_calendar_level(task_id, constrain_date, diff, direction="normal")
                    if calendar_level:  # use calendar
                        task_date_start = self._get_date_from_level(calendar_level, "date_from", "min")
                        new_date = self._get_date_from_level(calendar_level, "date_to", "max")
                    else:  # not use calendar
                        task_date_start = fields.Datetime.to_string(constrain_date)
                        new_date = fields.Datetime.to_string(constrain_date + diff)

                    vals_new['date_start'] = task_date_start
                    vals_new['date_end'] = new_date



        return vals_new, calendar_level