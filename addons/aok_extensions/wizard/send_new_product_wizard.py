from odoo import models, api, fields, exceptions
import logging

_logger = logging.getLogger(__name__)


class SendNewProduct(models.TransientModel):
    _name = 'send.new.product.wizard'

    subs_date = fields.Date(
        string='Check Date',
        default=fields.Date.today()
    )

    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product'
    )

    @api.multi
    def send_product(self):
        self.ensure_one()

        SaleOrderModel = self.env['sale.order']
        SaleOrderLineModel = self.env['sale.order.line']
        ProductProductModel = self.env['product.product']

        product_id = self._context.get('active_id', False)

        if self._context.get('active_model') == 'product.template':
            product = ProductProductModel.search([
                ('product_tmpl_id', '=', self._context.get('active_id', False))
            ], limit=1)
            product_id = product.id

        if not product_id:
            raise exceptions.MissingError('Product_id does not exist.')

        _logger.info('SEND PRODUCT')
        _logger.info("product (%s %s)" % (
            product_id, ProductProductModel.browse(product_id).name))

        domain = [
            ('subs_from', '<=', self.subs_date),
            ('order_line.product_id', '=', product_id),
            '|',
            ('subs_to', '=', False),
            ('subs_to', '>=', self.subs_date),
        ]

        _logger.info("Domain (%s)" % (domain))

        orders = SaleOrderModel.search(domain)

        _logger.info("Sale oders (%s)" % (orders))

        for order in orders:
            lines = order.order_line.filtered(
                lambda x: x.product_id.id == product_id)

            qty = 0
            discount = []

            for line in lines:
                qty += line.product_uom_qty
                discount.append(line.discount)

            new_line = SaleOrderLineModel.create({
                'product_id': self.product_id.id,
                'product_uom_qty': qty,
                'order_id': order.id,
                'discount': max(discount)
            })
            new_line.product_id_change()
            new_line.product_uom_change()

        return True
