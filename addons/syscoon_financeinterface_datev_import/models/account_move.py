#See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    import_datev = fields.Many2one('import.datev', 'DATEV Import', readonly=True)

    @api.multi
    def assert_balanced(self):
        for rec in self:
            if rec.import_datev:
                return True
        res = super(AccountMove, self).assert_balanced()
        return res
