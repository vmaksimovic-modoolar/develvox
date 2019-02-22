# -*- coding: utf-8 -*-

from odoo import fields, models

class CoreCompetency(models.Model):
    _name = 'core.competency'

    name = fields.Char(string='Competency Name', required=True)
