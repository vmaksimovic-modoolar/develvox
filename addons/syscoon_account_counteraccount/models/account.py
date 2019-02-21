# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    syscoon_account_counterpart = fields.Char('Counteraccount', compute='_compute_counteraccounts')

    @api.multi
    def _compute_counteraccounts(self):
        for move_line in self:
            accounts = []
            move_line_ids = self.env['account.move.line'].search([('move_id', '=', move_line.move_id.id)])
            for ml in move_line_ids:
                if ml.account_id != move_line.account_id and ml.account_id.code not in accounts:
                    if move_line.tax_line_id and ml.tax_ids:
                        continue
                    elif move_line.tax_ids and ml.tax_line_id:
                        continue
                    else:
                        accounts.append('%s %s' % (ml.account_id.code, ml.account_id.name))
            move_line.syscoon_account_counterpart = ', '.join(accounts)