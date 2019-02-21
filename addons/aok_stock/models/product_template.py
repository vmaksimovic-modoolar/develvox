# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    dangerous_goods_number = fields.Char(string='Dangerous goods number')
    product_use_time = fields.Boolean(string="Product Use Time")

    @api.onchange('tracking')
    def _onchange_tracking(self):
        if self.tracking in ('lot', 'serial'):
            self.product_use_time = True
        else:
            self.product_use_time = False


class ProductProduct(models.Model):
    _inherit = "product.product"

    kit_qty = fields.Float(string='Kit Quantity')

    def _get_kit_qty(self):
        MrpBom = self.env['mrp.bom']
        bom = MrpBom._bom_find(product_tmpl=self.product_tmpl_id, product=self, company_id=self.company_id.id)
        if bom:
            products = {}
            for line in bom.bom_line_ids:
                # Calculate product quantity based on uom
                qty = line.product_qty
                product_uom_type = line.product_uom_id.uom_type
                product_uom_factor = line.product_uom_id.factor_inv
                if product_uom_type == 'bigger':
                    qty = line.product_qty * product_uom_factor
                elif product_uom_type == 'smaller':
                    qty = line.product_qty / product_uom_factor
                if line.product_id.id in products.keys():
                    products[line.product_id.id]['qty'] += qty
                else:
                    products.update({line.product_id.id: {'qty_available': line.product_id.virtual_available > 0.00 and line.product_id.virtual_available or 0.00, 'qty': qty}})
            possible_qty = []
            for p in products:
                qty_to_add = int(products[p]['qty_available'] / products[p]['qty'])
                if bom.type == 'normal':
                    qty_to_add = qty_to_add + (self.virtual_available > 0.00 and self.virtual_available or 0.00)
                possible_qty.append(qty_to_add)
            if possible_qty:
                return min(possible_qty)
            else:
                return 0.00
        else:
            return 0.00

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state')
    def _compute_quantities(self):
        super(ProductProduct, self)._compute_quantities()
        for product in self:
            product.kit_qty = product._get_kit_qty()


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    @api.multi
    @api.depends('tage_bis_andruckmuster', 'tage_ab_freigabe', 'konfektionierung', 'lieferzeitpuffer')
    def _compute_delay_time(self):
        for record in self:
            record.delay = record.tage_bis_andruckmuster + record.tage_ab_freigabe + record.konfektionierung + record.lieferzeitpuffer

    delay = fields.Integer('Delivery Lead Time', compute='_compute_delay_time', store=True)
    tage_bis_andruckmuster = fields.Integer(string="Tage bis Andruckmuster")
    tage_ab_freigabe = fields.Integer(string="Tage ab Freigabe")
    konfektionierung = fields.Integer(string="Konfektionierung")
    lieferzeitpuffer = fields.Integer(string="Lieferzeitpuffer")
