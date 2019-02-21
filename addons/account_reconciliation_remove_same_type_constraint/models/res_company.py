# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):

    _inherit = 'res.company'

    allow_different_account_type_reconciliation = fields.Boolean(
        string='Allow different account type on reconciliation',
        help=''
    )
