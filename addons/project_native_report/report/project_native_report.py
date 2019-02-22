# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import models, fields, api, _
import json


from dateutil.relativedelta import relativedelta

class ProjectNativeGanttReport(models.AbstractModel):
    _name = 'report.project_native_report.project_native_gantt_report'

    def first_date_of_month(self, dt):

        first = dt.replace(day=1, hour=0, minute=0, second=0)
        return first

    def last_date_of_month(self, dt):


        if dt.month == 12:
            dt_year = dt.year+1
            dt_month = 1
        else:
            dt_year = dt.year
            dt_month = dt.month + 1

        last = datetime(dt_year, dt_month, day=1, hour=23, minute=59, second=59) - timedelta(1)
        return last

    def min_max_range(self, task_ids):

        f_date_start = "date_start"
        f_date_end = "date_end"

        date_start_range = []
        date_end_range = []

        for item in task_ids:

            r_date_start = fields.Datetime.from_string(item[f_date_start])
            r_date_end = fields.Datetime.from_string(item[f_date_end])

            if not r_date_start:
                r_date_start = r_date_end
            if not r_date_end:
                r_date_end = r_date_start

            if r_date_start and r_date_end:
                date_start_range.append(r_date_start)
                date_end_range.append(r_date_end)


        date_start_range = min(date_start_range)
        date_end_range = max(date_end_range)

        date_start = self.first_date_of_month(date_start_range)
        date_end = self.last_date_of_month(date_end_range)

        return date_start, date_end

    def get_scale(self,date_start, date_end, cell_scale ):

        first_day_scale = date_start.timestamp()
        time_scale = date_end.timestamp() - date_start.timestamp()

        timeline_width = cell_scale * (date_end-date_start).days
        px_scale = time_scale / timeline_width

        return first_day_scale, px_scale



    def get_bar_position(self, date_start, date_end, first_day_scale, px_scale):
        start_time = date_start.timestamp()
        stop_time = date_end.timestamp()
        start_pxscale = round((start_time - first_day_scale) / px_scale)
        stop_pxscale = round((stop_time - first_day_scale) / px_scale)
        bar_left = start_pxscale
        bar_width = stop_pxscale - start_pxscale

        return bar_left, bar_width

    def recalc_bar_page(self, els_page, page_start, page_end, first_day_scale, px_scale, step):
        els_page_return = []
        for el_on in els_page:
            bar_date_start = el_on["bar_date_start"]
            bar_date_end = el_on["bar_date_end"]
            gantt_bar = el_on["gantt_bar"]

            if not bar_date_start:
                bar_date_start = page_start

            if bar_date_start and bar_date_end and page_start <= bar_date_start <= page_end:

                new_date_bar_end = False

                if bar_date_end > page_end:
                    new_date_bar_end = bar_date_end

                    date_bar_delta = bar_date_end - page_end
                    bar_date_end = bar_date_end - date_bar_delta

                el_on["bar_date_start"] = False
                el_on["bar_date_end"] = new_date_bar_end

                bar_left, bar_width = self.get_bar_position(date_start=bar_date_start, date_end=bar_date_end,
                                                            first_day_scale=first_day_scale, px_scale=px_scale)

                bar_css = "col_gantt_plan"


                if el_on["color_gantt_set"]:
                    color_gantt = el_on["color_gantt"]
                    bar_style = 'width:{}px; left:{}px; background:{}'.format(bar_width, bar_left, color_gantt )
                else:

                    if el_on["schedule_mode"] == "auto":
                        bar_css = '{} {}'.format(bar_css, "task-gantt-bar-plan-auto")

                    if el_on["schedule_mode"] == "auto" and el_on["constrain_type"] != "asap":
                        bar_css = '{} {}'.format(bar_css, "task-gantt-bar-plan-constrain")

                    bar_style = 'width:{}px; left:{}px;'.format(bar_width, bar_left)



                if el_on["date_deadline"]:
                    bar_css = '{}'.format("col-gantt-deadline-slider")

                if el_on["is_milestone"]:
                    bar_css = '{} {}'.format(bar_css, "fa fa-flag fa-1x")
                    bar_style = 'width:{}px; left:{}px; background:{}'.format(bar_width, bar_left, "rgba(242, 197, 116, 0.1)")




                bar_name = el_on["name"]
                is_group = el_on["is_group"]


                gantt_bar.append({
                    "bar_name": bar_name,
                    "bar_css": bar_css,
                    "bar_style": bar_style,
                    "step": step,
                    "bar_left": bar_left,
                    "bar_width": bar_width,
                    "is_group": is_group,

                })

                el_on["gantt_bar"] = gantt_bar

            els_page_return.append(el_on)

        return els_page_return



    def get_range_factor0(self, date_string):

        year = date_string.year
        month_str = date_string.strftime("%b")
        result = ("{0}-{1}".format(month_str, str(year)[-2:]))

        return result


    def get_range_primary(self, start_date, end_date, factor, scale, page):

        range_factor0 = []
        date_factor = start_date
        cell_x_factor = factor
        cell_x_scale = scale
        i_factor = 1

        for x_factor in range(1, cell_x_factor):
            add_to = False
            date_factor = date_factor + relativedelta(days=1)

            if date_factor > end_date:
                break

            f_string = self.get_range_factor0(date_factor)
            span = cell_x_scale * i_factor

            if date_factor.day == 1:
                f_string = self.get_range_factor0(date_factor - relativedelta(days=1))
                if i_factor < 6:
                    f_string = '<>'

                add_to = True
                i_factor = 0


            if x_factor == cell_x_factor-1:
                add_to = True
                if page > 0:
                    span = span + cell_x_scale

            if add_to:
                range_factor0.append({
                    'string': f_string,
                    'span': span
                })


            i_factor = i_factor + 1

        return range_factor0



    def find_list(self, fe, seq):
        for item in seq:
            if fe == item["id"]:
                ritem={}
                ritem["index"] = seq.index(item)
                ritem["id"] = item["id"]


                bar_left, bar_width, is_group, step = False, False, False, False

                if item["gantt_bar"]:
                    gantt_bar = item["gantt_bar"]
                    bar_left = gantt_bar[0]["bar_left"]
                    bar_width = gantt_bar[0]["bar_width"]
                    is_group = gantt_bar[0]["is_group"]
                    step = gantt_bar[0]["step"]

                ritem["bar_left"] = bar_left
                ritem["bar_width"] = bar_width
                ritem["is_group"] = is_group
                ritem["step"] = step


                return ritem

    def get_link_list(self, els):

        arrows = []
        ids = []
        for el in els:
            if el["gantt_bar"]:
                ids.append(el["id"])

        predecessor_records = self.env['project.task.predecessor'].search(
            [('parent_task_id', 'in', ids)])

        for predecessor in predecessor_records:

            pred = {}

            from_id = predecessor.parent_task_id.id
            to_id = predecessor.task_id.id

            from_obj = self.find_list(from_id, els)
            to_obj = self.find_list(to_id, els)


            pred["from_id"] = from_id
            pred["to_id"] = to_id
            pred["from_obj"] = json.dumps(from_obj)
            pred["to_obj"] = json.dumps(to_obj)
            pred["type"] = predecessor.type



            arrows.append(pred)

        return arrows


    def get_gantt(self, parent, y_size_mm=0, x_size_m=0 ):



        x_size_mm = 297
        y_size_mm = 210

        x_size = 1000 # -300
        y_size = 542


        page_x_size = x_size  # shirina gantt
        page_y_size = y_size # v dlinu lista

        pages = []

        el_x_sum = 0 #page sum elements
        el_on_page = []
        el_size_y = 25

        cell_x_scale = 26 # elemt vtoroj
        cell_x_factor = int(page_x_size/cell_x_scale) #600/26 = 23
        page_x_size = cell_x_scale * cell_x_factor # 598

        page_x_item = 300 #shirina items
        page_x_full = page_x_item + page_x_size #shirina items plus gantt 250+598 = 848
        page_x_factor = int(page_x_full / cell_x_scale)  # skolko listov = 32
        page_x_full = cell_x_scale * page_x_factor


        f_date_start = "date_start"
        f_date_end = "date_end"
        f_date_deadline = "date_deadline"

        date_start, date_end = self.min_max_range(parent.task_ids)

        # tasks_list = parent.tasks.sorted(key=lambda x: x.sorting_seq)
        domain = [('project_id', '=', parent.id), '|', ('active','=',True),('active','=',False)]
        arch_tasks = self.env['project.task'].sudo().search(domain)
        tasks_list = arch_tasks.sorted(key=lambda x: x.sorting_seq)

        tasks_list_len = len(tasks_list)
        tasks_list_int = 0
        for item in tasks_list:
            tasks_list_int = tasks_list_int + 1
            el_x_sum = el_x_sum + el_size_y
            item_dict = {}
            item_dict["id"] = item.id
            item_dict["name"] = item.name

            duration = "-"
            if item.duration:
                m, s = divmod(item.duration, 60)
                h, m = divmod(m, 60)

                duration = '{:d}:{:02d}:{:02d}'.format(h, m, s)

            item_dict["duration"] = duration
            item_dict["id"] = item.id

            item_dict["gantt_bar"] = []

            item_dict["bar_date_start"] = False
            if item[f_date_start]:
                item_dict["bar_date_start"] = fields.Datetime.from_string(item[f_date_start])

            item_dict["bar_date_end"] = False
            if item[f_date_end]:
                item_dict["bar_date_end"] = fields.Datetime.from_string(item[f_date_end])

            item_dict["date_deadline"] = False
            if item[f_date_deadline]:

                item_dict["date_deadline"] = fields.Datetime.from_string(item[f_date_deadline])

                if item_dict["bar_date_start"] and item_dict["date_deadline"] < item_dict["bar_date_start"]:
                    item_dict["bar_date_start"] = item_dict["date_deadline"]

                if item_dict["bar_date_end"] and item_dict["date_deadline"] > item_dict["bar_date_end"]:
                    item_dict["bar_date_end"] = item_dict["date_deadline"]





            item_dict["color_gantt_set"] = item.color_gantt_set
            item_dict["color_gantt"] = item.color_gantt

            item_dict["is_milestone"] = item.is_milestone

            item_dict["on_gantt"] = item.on_gantt

            item_dict["schedule_mode"] = item.schedule_mode
            item_dict["constrain_type"] = item.constrain_type



            padding_depth = 15
            paddepth = 0
            name_css = "col_gantt_name"
            is_group = False
            if item.subtask_count > 0:
                name_css = "col_gantt_name task-gantt-items-group"
                is_group = True

            level = item.sorting_level
            paddepth = padding_depth * (level)




            item_dict["paddepth"] = paddepth
            item_dict["name_css"] = name_css
            item_dict["is_group"] = is_group


            if el_x_sum < page_y_size and tasks_list_int != tasks_list_len:

                el_on_page.append(item_dict)

            else:

                if tasks_list_int == tasks_list_len:
                    el_on_page.append(item_dict)

                range_factor = []
                date_factor = date_start

                for x_factor in range(1, cell_x_factor):
                    range_factor.append('{:02d}'.format(date_factor.day))
                    date_factor = date_factor + relativedelta(days=1)



                rt = {}
                rt["date0"] = self.get_range_primary(date_start, date_factor, cell_x_factor, cell_x_scale, 0)
                rt["date"] = range_factor
                rt["page_step"] = 0
                rt["date_start"] = date_start
                rt["date_end"] = date_factor

                first_day_scale, px_scale = self.get_scale(date_start=date_start,
                                                           date_end=date_factor, cell_scale=cell_x_scale)

                first_day_scale = first_day_scale-(page_x_item*px_scale)

                el_on_page_new = self.recalc_bar_page(els_page=el_on_page,
                                                      page_start=date_start,
                                                      page_end=date_factor,
                                                      first_day_scale=first_day_scale,
                                                      px_scale=px_scale, step=0)

                x_width_factor = len(range_factor)
                y_hight_factor = len(el_on_page_new)
                rt["elements"] = el_on_page_new
                rt["elements_gantt"] = None
                rt["gantt_y_size"] = y_hight_factor * el_size_y
                rt["gantt_x_size"] = cell_x_scale * x_width_factor
                rt["gantt_x1_size"] = None
                rt["row_gantt_width"] = page_x_item + (cell_x_scale * x_width_factor)
                rt["page_x_item"] = page_x_item


                link_list = self.get_link_list(el_on_page_new)
                rt["link_list"] = link_list



                pages.append(rt)


                range_date = []
                current = date_factor
                ix = 0
                j = 1
                current_start = current
                while current <= date_end:
                    range_date.append('{:02d}'.format(current.day))
                    current += relativedelta(days=1)
                    ix = ix + 1
                    if ix == page_x_factor or current >= date_end: #every gantt page


                        rtx = {}
                        rtx["date"] = range_date
                        range_date = []
                        rtx["page_step"] = j
                        rtx["date_start"] = current_start
                        rtx["date_end"] = current

                        rtx["date0"] = self.get_range_primary(current_start, current, page_x_factor, cell_x_scale, j)


                        first_day_scale, px_scale = self.get_scale(date_start=current_start,
                                                                   date_end=current,
                                                                   cell_scale=cell_x_scale)

                        el_on_page_new = self.recalc_bar_page(els_page=el_on_page,
                                                              page_start=current_start,
                                                              page_end=current,
                                                              first_day_scale=first_day_scale,
                                                              px_scale=px_scale, step=j)

                        y_hight_factor = len(el_on_page_new)
                        rtx["elements"] = None
                        rtx["elements_gantt"] = el_on_page_new
                        rtx["gantt_y_size"] = y_hight_factor * el_size_y
                        rtx["gantt_x_size"] = None
                        rtx["gantt_x1_size"] =cell_x_scale * ix
                        rtx["row_gantt_width"] = cell_x_scale * ix

                        link_list = self.get_link_list(el_on_page_new)
                        rtx["link_list"] = link_list
                        rtx["page_x_item"] = 0

                        current_start = current
                        pages.append(rtx)
                        j = j + 1
                        ix = 0



                el_on_page = []
                el_on_page.append(item_dict)

                el_x_sum = 0


        result = {}

        result["global_date_start"] = date_start
        result["global_date_end"] = date_end

        result["pages"] = pages

        return result


    @api.multi
    def get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'project.project',
            'docs': self.env['project.project'].browse(docids),
            'get_gantt': self.get_gantt,
            'data': data,
        }

