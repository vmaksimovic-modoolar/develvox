# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.multi
    @api.depends('lot_name', 'product_id')
    def _compute_is_use_time(self):
        for line in self:
            if line.product_id.product_tmpl_id and line.product_id.product_tmpl_id.product_use_time:
                line.has_use_time = True

    dangerous_goods_number = fields.Char(related="product_id.product_tmpl_id.dangerous_goods_number", string='Dangerous goods number', store=True)
    partner_id = fields.Many2one(related='picking_id.partner_id', string='Partner', store=True)
    lot_expire_date = fields.Date(string='Expire Date', help='This date will determine end of life, best before use, removal and alert date for serial or lot numbers')
    has_use_time = fields.Boolean(compute='_compute_is_use_time')
