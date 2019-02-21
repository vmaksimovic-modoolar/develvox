# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    analytic_id_obligatory = fields.Boolean('Kostenstelle ist Pflicht')