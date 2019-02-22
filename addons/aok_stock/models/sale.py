# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    picking_note = fields.Char(string='Kommissionierhinweis')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            self.product_packaging = False
            return {}
        if self.product_id.type != 'service':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(warehouse=self.order_id.warehouse_id.id)
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
            if product.bom_ids:  # and product.bom_ids[:1].type == 'phantom':
                message = _('You have %s kits of %s available to sell.') % \
                        (product._get_kit_qty(), product.display_name)
                warning_mess = {
                    'title': _('Kits avilability!'),
                    'message': message
                }
                return {'warning': warning_mess}
            if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                is_available = self._check_routing()

                if not is_available:
                    message = _('You plan to sell %s %s but you only have %s %s available in %s warehouse.') % \
                            (self.product_uom_qty, self.product_uom.name, product.virtual_available, product.uom_id.name, self.order_id.warehouse_id.name)
                    # We check if some products are available in other warehouses.
                    if float_compare(product.virtual_available, self.product_id.virtual_available, precision_digits=precision) == -1:
                        message += _('\nThere are %s %s available accross all warehouses.') % \
                                (self.product_id.virtual_available, product.uom_id.name)

                    warning_mess = {
                        'title': _('Not enough inventory!'),
                        'message': message
                    }
                    return {'warning': warning_mess}

        return {}
