# -*- coding: utf-8 -*-
#See LICENSE file for full copyright and licensing details.


from odoo import models, api


class partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create (self, vals):
        config_id = self.env['ecoservice.partner.auto.account.company'].search([('company_id', '=', self.env.user.company_id.id)])
        result = super(partner, self).create(vals)
        if config_id.create_auto_account_on == 'partners':
            if result.company_type == 'company' or result.company_type == 'company' and result.type == 'contact':
                ctx = dict(self._context)
                if result.customer:
                    ctx['type'] = 'receivable'
                    self.create_accounts([result.id], ctx)
                if result.supplier:
                    ctx['type'] = 'payable'
                    self.create_accounts([result.id], ctx)
        return result
