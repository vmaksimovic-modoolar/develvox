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
from odoo.exceptions import Warning
from pdb import set_trace as bp

from itertools import groupby
from operator import itemgetter

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)  # Need for message in console.


class ProjectTaskDetailPlan(models.Model):
    _name = 'project.task.detail.plan'

    @api.model
    def _get_type(self):
        value = [
            ('cut', _('Cut of DateTime')),
            ('attendance', _('Attendance')),]
        return value

    name = fields.Char("Name",  readonly=True,)
    task_id = fields.Many2one('project.task', 'Task', ondelete='cascade',  readonly=True,)
    type_level = fields.Selection('_get_type',
                                  string='Type',
                                  readonly=True, )

    data_from = fields.Datetime("Date From",  readonly=True,)
    data_to = fields.Datetime("Date To",  readonly=True,)
    duration = fields.Integer(string='Duration',  readonly=True,)
    iteration = fields.Integer(string='iteration',  readonly=True,)

    color_gantt_set = fields.Boolean("Set Color Task", default=True)
    color_gantt = fields.Char(
        string="Color",
        Store=True,
        default="rgba(170,170,13,0.53)",
        compute='_compute_color_gantt'
    )

    schedule_mode = fields.Selection([ ('auto', 'Auto'), ('manual', 'Manual')],
                                     string='Schedule Mode',
                                     default='auto',  readonly=True,)

    @api.depends('type_level')
    def _compute_color_gantt(self):
        for plan in self:
            if plan.type_level == "cut":
                plan.color_gantt ="rgba(190,170,23,0.53)"



class ProjectTask(models.Model):
    _name = 'project.task'
    _inherit = 'project.task'




    @api.depends("detail_plan_ids")
    def _compute_detail_plan_count(self):

        for task in self:
            task.update({
                'detail_plan_count': len(task.detail_plan_ids),
            })

    detail_plan_count = fields.Integer(compute='_compute_detail_plan_count', string='Detail plan Count', store=True)

    detail_plan_ids = fields.One2many('project.task.detail.plan', 'task_id', 'Detail Plan')



