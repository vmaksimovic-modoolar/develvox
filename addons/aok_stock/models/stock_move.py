# -*- coding: utf-8 -*-

from odoo import fields, models

class StockMove(models.Model):
    _inherit = "stock.move"

    partner_id = fields.Many2one(related='picking_id.partner_id', string='Partner', store=True)

    def _action_done(self):
        result = super(StockMove, self)._action_done()
        for line in result.mapped('move_line_ids').filtered(lambda ml: ml.lot_id and ml.lot_expire_date):
            line.lot_id.use_date = line.lot_expire_date
        return result


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    lot_expire_date = fields.Date(related='lot_id.use_date', string="MHD", store=True)
    cost_per_unit = fields.Float(related='product_id.standard_price', string="Stückkosten", store=True)
