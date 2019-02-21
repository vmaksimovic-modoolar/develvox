# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class Http(models.AbstractModel):

    _inherit = 'ir.http'

    def session_info(self):
        result = super(Http, self).session_info()

        result.update({
            'companyAllowDifferentAccountTypeReconciliation': self.env.user.company_id.allow_different_account_type_reconciliation
        })

        return result
