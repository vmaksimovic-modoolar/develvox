# -*- coding: utf-8 -*-
# This file is part of Odoo. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from odoo import models, api, _ 
from odoo.exceptions import UserError


class Company(models.Model):
    _inherit = 'res.company'

    @api.multi
    def set_datev_skr03(self):
        self.env['account.tax']._set_taxkeys(self.id)
        self.env['account.account']._set_account_autoaccount(self.id)
        return
