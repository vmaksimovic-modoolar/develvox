# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare

from odoo.addons import decimal_precision as dp


class SaleAgreementType(models.Model):
    _name = "sale.agreement.type"
    _description = "Sale Agreement Type"
    _order = "sequence"

    name = fields.Char(string='Agreement Type', required=True, translate=True)
    sequence = fields.Integer(default=1)
    exclusive = fields.Selection([
        ('own_goods', 'Own Goods'), ('customer_goods', 'Customer Goods')],
        string='Agreement Selection Type', required=True, default='own_goods',
        )
    warehouse_id = fields.Many2many(
        'stock.warehouse', string='Warehouses',
        required=True)
    handling_cost = fields.Boolean("Handling Cost")
    handling_product_id = fields.Many2one('product.product', string='Handling Product')
    show_remaining_quantity = fields.Boolean(string='Show remaining qty on product', default=True)


class SaleAgreementTags(models.Model):
    _name = "sale.agreement.tags"
    _description = "Sales Agreement Tags"

    name = fields.Char(required=True)


class SaleAgreement(models.Model):
    _name = "sale.agreement"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sales Agreement"
    _order = 'date_order desc, id desc'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SA.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    @api.onchange('fiscal_position_id')
    def _compute_tax_id(self):
        """
        Trigger the recompute of the taxes if the fiscal position is changed on the SO.
        """
        for order in self:
            order.order_line._compute_tax_id()

    name = fields.Char(string='Agreement Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    date_order = fields.Datetime(string='Agreement Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    confirmation_date = fields.Datetime(string='Confirmation Date', readonly=True, index=True, help="Date on which the sales order is confirmed.", oldname="date_confirm", copy=False)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange', default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Affiliate', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always')
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Invoice address for current sales order.")
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Delivery address for current sales order.")

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order.")
    currency_id = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)

    order_line = fields.One2many('sale.agreement.line', 'order_id', string='Agreement Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)

    note = fields.Text('Terms and conditions')

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='onchange')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')

    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term')
    fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'))
    team_id = fields.Many2one('crm.team', 'Sales Channel', change_default=True, default=_get_default_team)

    agreement_type = fields.Many2one('sale.agreement.type', string='Agreement Type')
    tag_ids = fields.Many2many('sale.agreement.tags', string='Tags')

    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group', copy=False)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)]})
    picking_ids = fields.One2many('stock.picking', 'agreement_id', string='Pickings')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    picking_policy = fields.Selection([
        ('direct', 'Deliver each product when available'),
        ('one', 'Deliver all products at once')],
        string='Shipping Policy', required=True, readonly=True, default='direct',
        states={'draft': [('readonly', False)]})

    route_id = fields.Many2one('stock.location.route', string='Route', domain=[('sale_selectable', '=', True)], ondelete='restrict')

    sale_order_ids = fields.One2many('sale.order', 'sale_agreement_id', string="Sales Order")
    sale_count = fields.Integer(string='Sales Orders', compute='_compute_sale_orders')
    handling_cost = fields.Boolean(related="agreement_type.handling_cost", string="Handling Cost")

    @api.onchange('agreement_type')
    def _onchange_agreement_type(self):
        return {'domain': {'warehouse_id': [('id', 'in', self.agreement_type.warehouse_id.ids)]}}

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.picking_ids)

    @api.depends('sale_order_ids')
    def _compute_sale_orders(self):
        for order in self:
            order.sale_count = len(order.sale_order_ids)

    @api.multi
    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales agreement ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action

    @api.multi
    def action_view_sale_order(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders').read()[0]
        sale_orders = self.mapped('sale_order_ids')
        action['domain'] = [('id', 'in', sale_orders.ids)]
        action['context'] = {'default_sale_agreement_id': self.id, 'default_pricelist_id': self.pricelist_id.id, 'default_warehouse_id': self.warehouse_id.id, 'default_company_id': self.company_id.id}
        return action

    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(_('You can not delete a sent quotation or a sales order! Try to cancel it before.'))
        return super(SaleAgreement, self).unlink()

    # @api.multi
    # def _track_subtype(self, init_values):
    #     self.ensure_one()
    #     if 'state' in init_values and self.state == 'sale':
    #         return 'sale.mt_order_confirmed'
    #     elif 'state' in init_values and self.state == 'sent':
    #         return 'sale.mt_order_sent'
    #     return super(SaleAgreement, self)._track_subtype(init_values)

    @api.multi
    @api.onchange('partner_shipping_id', 'partner_id')
    def onchange_partner_shipping_id(self):
        """
        Trigger the change of fiscal position when the shipping address is modified.
        """
        self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, self.partner_shipping_id.id)
        return {}

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'user_id': self.partner_id.user_id.id or self.env.uid
        }
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_sale_note') and self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)

    @api.onchange('partner_id')
    def onchange_partner_id_warning(self):
        if not self.partner_id:
            return
        warning = {}
        title = False
        message = False
        partner = self.partner_id

        # If partner has no warning, check its company
        if partner.sale_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.sale_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if partner.sale_warn != 'block' and partner.parent_id and partner.parent_id.sale_warn == 'block':
                partner = partner.parent_id
            title = ("Warning for %s") % partner.name
            message = partner.sale_warn_msg
            warning = {
                    'title': title,
                    'message': message,
            }
            if partner.sale_warn == 'block':
                self.update({'partner_id': False, 'partner_invoice_id': False, 'partner_shipping_id': False, 'pricelist_id': False})
                return {'warning': warning}

        if warning:
            return {'warning': warning}

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('sale.agreement') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.agreement') or _('New')

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)
        result = super(SaleAgreement, self).create(vals)
        return result

    @api.multi
    def action_draft(self):
        return self.write({
            'state': 'draft',
        })

    @api.multi
    def action_cancel(self):
        for order in self:
            if order.sale_order_ids:
                raise UserError(_("You cannot cancel a sales agreement having sales order."))
            # Cancel the picking
            order.picking_ids.filtered(lambda r: r.state != 'cancel').action_cancel()
        return self.write({'state': 'cancel'})

    @api.multi
    def action_done(self):
        return self.write({'state': 'done'})

    @api.multi
    def _action_confirm(self):
        self.write({
            'state': 'confirm',
            'confirmation_date': fields.Datetime.now()
        })
        for order in self:
            order.order_line._action_launch_procurement_rule()
            # Check availability should be done automatically.
            order.picking_ids.filtered(lambda r: r.state != 'cancel').action_assign()
        return True

    @api.multi
    def action_confirm(self):
        self._action_confirm()
        return True


class SaleAgreementLine(models.Model):
    _name = 'sale.agreement.line'
    _description = 'Sales Agreement Line'
    _order = 'order_id, sequence, id'

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SA line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.multi
    def _compute_tax_id(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes

    def _compute_quantity(self):
        for line in self:
            if line.product_id.type in ('consu', 'product'):
                sale_orders = line.order_id.sale_order_ids
                ordered_qty = sum(sale_orders.filtered(lambda r: r.state not in ['draft', 'cancel']).mapped('order_line').filtered(lambda r: r.product_id == line.product_id and r.is_sa_product).mapped('product_uom_qty'))
                line.qty_ordered = ordered_qty
                line.qty_remaining = line.product_uom_qty - ordered_qty
            else:
                line.qty_ordered = 0.0
                line.qty_remaining = 0.0

    order_id = fields.Many2one('sale.agreement', string='Agreement Reference', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    handling_cost_from = fields.Date("Storage Cost From")

    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)

    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)

    qty_ordered = fields.Float(compute="_compute_quantity", string='Ordered Qty', digits=dp.get_precision('Product Unit of Measure'))
    qty_remaining = fields.Float(compute="_compute_quantity", string='Remaining Qty', digits=dp.get_precision('Product Unit of Measure'))

    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Salesperson', readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], related='order_id.state', string='Agreement Status', readonly=True, copy=False, store=True, default='draft')

    route_id = fields.Many2one(related='order_id.route_id', string='Route', store=True)
    move_ids = fields.One2many('stock.move', 'agreement_line_id', string='Stock Moves')
    handling_cost = fields.Boolean("Handling Cost")

    @api.multi
    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        if self.order_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.order_id.pricelist_id.id).price
        final_price, rule_id = self.order_id.pricelist_id.get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order)
        base_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id, rule_id, self.product_uom_qty, self.product_uom, self.order_id.pricelist_id.id)
        if currency_id != self.order_id.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(context_partner).compute(base_price, self.order_id.pricelist_id.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            return {}
        if self.product_id.type == 'product':
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            product = self.product_id.with_context(warehouse=self.order_id.warehouse_id.id)
            product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
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

    @api.multi
    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        if self.state == 'confirm' and self.product_id.type in ['product', 'consu'] and self.product_uom_qty < self._origin.product_uom_qty:
            warning_mess = {
                'title': _('Ordered quantity decreased!'),
                'message': _('You are decreasing the ordered quantity! Do not forget to manually update the picking if needed.'),
            }
            return {'warning': warning_mess}
        return {}

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        result = {'domain': domain}

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)

        return result

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

    @api.constrains('product_uom_qty', 'qty_ordered')
    def _check_product_uom_qty(self):
        for line in self.filtered(lambda r: r.state == 'confirm'):
            if line.product_uom_qty < line.qty_ordered:
                raise ValidationError(_("Decreasing is only allowed upto the ordered quantity!"))

    @api.model
    def create(self, values):
        line = super(SaleAgreementLine, self).create(values)
        if line.state == 'confirm':
            line._action_launch_procurement_rule()
            line.order_id.picking_ids.filtered(lambda r: r.state != 'cancel').action_assign()
        return line

    @api.multi
    def write(self, values):
        lines = False
        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            lines = self.filtered(
                lambda r: r.state == 'confirm' and float_compare(r.product_uom_qty, values['product_uom_qty'], precision_digits=precision) == -1)
        res = super(SaleAgreementLine, self).write(values)
        if lines:
            lines._action_launch_procurement_rule()
            lines.mapped('order_id').picking_ids.filtered(lambda r: r.state != 'cancel').action_assign()
        return res

    @api.multi
    def unlink(self):
        if self.filtered(lambda x: x.state in ('confirm', 'done')):
            raise UserError(_('You can not remove a sales agreement line.'))
        return super(SaleAgreementLine, self).unlink()

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
            if pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        product_currency = product_currency or(product.company_id and product.company_id.currency_id) or self.env.user.company_id.currency_id
        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id)

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id.id

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        self.discount = 0.0
        if not (self.product_id and self.product_uom and
                self.order_id.partner_id and self.order_id.pricelist_id and
                self.order_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('sale.group_discount_per_so_line')):
            return

        context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order)
        pricelist_context = dict(context_partner, uom=self.product_uom.id)

        price, rule_id = self.order_id.pricelist_id.with_context(pricelist_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        new_list_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id, rule_id, self.product_uom_qty, self.product_uom, self.order_id.pricelist_id.id)

        if new_list_price != 0:
            if self.order_id.pricelist_id.currency_id.id != currency_id:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = self.env['res.currency'].browse(currency_id).with_context(context_partner).compute(new_list_price, self.order_id.pricelist_id.currency_id)
            discount = (new_list_price - price) / new_list_price * 100
            if discount > 0:
                self.discount = discount

    # Delivery Orders

    @api.multi
    def _action_launch_procurement_rule(self):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale agreement line. procurement group will launch '_run_move', '_run_buy' or '_run_manufacture'
        depending on the sale agreement line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        errors = []
        for line in self:
            if line.state != 'confirm' or line.product_id.type not in ('consu', 'product'):
                continue
            qty = 0.0
            for move in line.move_ids.filtered(lambda r: r.state != 'cancel'):
                qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom, rounding_method='HALF-UP')
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line.order_id.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
                    'agreement_id': line.order_id.id,
                    'partner_id': line.order_id.partner_shipping_id.id,
                })
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the agreement was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            # Changes in reservation process.
            product_qty = line.product_uom_qty - qty - line.qty_ordered

            procurement_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                procurement_uom = quant_uom

            try:
                self.env['procurement.group'].run(line.product_id, product_qty, procurement_uom, line.order_id.partner_shipping_id.property_stock_customer, line.name, line.order_id.name, values)
            except UserError as error:
                errors.append(error.name)
        if errors:
            raise UserError('\n'.join(errors))
        return True

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be created from a procurement rule
        comming from a sale agreement line. This method could be override in order to add other custom key that could
        be used in move/po creation.
        """
        values = {}
        self.ensure_one()
        date_planned = datetime.strptime(self.order_id.confirmation_date, DEFAULT_SERVER_DATETIME_FORMAT)\
            + timedelta(days=0.0) - timedelta(days=self.order_id.company_id.security_lead)
        values.update({
            'company_id': self.order_id.company_id,
            'group_id': group_id,
            'agreement_line_id': self.id,
            'date_planned': date_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'route_ids': self.route_id,
            'warehouse_id': self.order_id.warehouse_id or False,
            'partner_dest_id': self.order_id.partner_shipping_id
        })
        return values

    def _check_routing(self):
        """ Verify the route of the product based on the warehouse
            return True if the product availibility in stock does not need to be verified,
            which is the case in MTO, Cross-Dock or Drop-Shipping
        """
        is_available = False
        product_routes = self.route_id or (self.product_id.route_ids + self.product_id.categ_id.total_route_ids)

        # Check MTO
        wh_mto_route = self.order_id.warehouse_id.mto_pull_id.route_id
        if wh_mto_route and wh_mto_route <= product_routes:
            is_available = True
        else:
            mto_route = False
            try:
                mto_route = self.env['stock.warehouse']._get_mto_route()
            except UserError:
                # if route MTO not found in ir_model_data, we treat the product as in MTS
                pass
            if mto_route and mto_route in product_routes:
                is_available = True

        # Check Drop-Shipping
        if not is_available:
            for pull_rule in product_routes.mapped('pull_ids'):
                if pull_rule.picking_type_id.sudo().default_location_src_id.usage == 'supplier' and\
                        pull_rule.picking_type_id.sudo().default_location_dest_id.usage == 'customer':
                    is_available = True
                    break

        return is_available


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    agreement_id = fields.Many2one('sale.agreement', 'Sales Agreement')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    agreement_id = fields.Many2one(related="group_id.agreement_id", string="Sales Agreement", store=True)


class StockMove(models.Model):
    _inherit = "stock.move"

    agreement_line_id = fields.Many2one('sale.agreement.line', 'Agreement Line')


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_agreement_id = fields.Many2one('sale.agreement', string="Sales Agreement")

    @api.onchange('sale_agreement_id')
    def _onchange_sale_agreement_id(self):
        if self.sale_agreement_id:
            self.pricelist_id = self.sale_agreement_id.pricelist_id
            self.warehouse_id = self.sale_agreement_id.warehouse_id
            self.company_id = self.sale_agreement_id.company_id

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            picking = order.sale_agreement_id.picking_ids.filtered(lambda r: r.state != 'cancel')
            if picking:
                picking.do_unreserve()
            for line in order.order_line.filtered(lambda r: r.is_sa_product):
                move_line = picking.move_lines.filtered(lambda r: r.product_id == line.product_id)
                if move_line:
                    move_line.product_uom_qty = move_line.product_uom_qty - line.product_uom_qty
            if picking:
                picking.action_assign()
        return res

    @api.multi
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for order in self:
            pickings = order.mapped('sale_agreement_id').mapped('picking_ids').filtered(lambda r: r.state != 'cancel')
            if pickings:
                pickings.do_unreserve()
            for line in order.order_line.filtered(lambda r: r.is_sa_product):
                move_line = pickings.move_lines.filtered(lambda r: r.product_id == line.product_id)
                if move_line:
                    move_line.product_uom_qty = move_line.product_uom_qty + line.product_uom_qty
            if pickings:
                pickings.action_assign()
        return res

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if self.sale_agreement_id:
            self.pricelist_id = self.sale_agreement_id.pricelist_id

    @api.multi
    def _remove_handling_cost_line(self):
        self.order_line.filtered(lambda x: x.is_handling_cost).unlink()

    @api.multi
    def set_handling_cost_line(self):
        for order in self:
            # Remove handling cost products from the sales agreement
            order._remove_handling_cost_line()

            if order.state not in ('draft'):
                raise UserError(_("You can add handling cost only on unconfirmed agreements."))
            else:
                order._create_handling_cost_line(order.sale_agreement_id)
        return True

    def _create_handling_cost_line(self, agreement_id):
        agreement_type = agreement_id.agreement_type

        # Apply fiscal position
        taxes = agreement_type.handling_product_id.taxes_id.filtered(lambda t: t.company_id.id == self.company_id.id)
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(taxes, agreement_type.handling_product_id, self.partner_id).ids

        # Filter Agreement Line which have agreement type is handling cost and handling cost is true in line
        agreement_product_ids = agreement_id.order_line.filtered(lambda x: x.handling_cost and x.product_id.id in self.order_line.mapped('product_id').ids and x.handling_cost_from <= fields.Date.context_today(self))
        product_qty = len(agreement_product_ids)

        if agreement_product_ids:
            # Create the sales order line
            values = {
                'order_id': self.id,
                'name': agreement_type.handling_product_id.name,
                'product_uom_qty': product_qty,
                'product_uom': agreement_type.handling_product_id.uom_id.id,
                'product_id': agreement_type.handling_product_id.id,
                'price_unit': agreement_type.handling_product_id.list_price,
                'tax_id': [(6, 0, taxes_ids)],
                'is_handling_cost': True,
            }
            if self.order_line:
                values['sequence'] = self.order_line[-1].sequence + 1
            sal = self.order_line.sudo().create(values)
            return sal


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_handling_cost = fields.Boolean()
    sale_agreement_id = fields.Many2one(related='order_id.sale_agreement_id', string="Sale Agreement", store=True)
    is_sa_product = fields.Boolean("SA Product")

    @api.constrains('product_id', 'product_uom_qty')
    def _check_remaining_quantity(self):
        SaleOrder = self.env['sale.order']
        for line in self.filtered(lambda r: r.order_id.sale_agreement_id and r.is_sa_product):
            sale_agreement_line = line.order_id.sale_agreement_id.mapped('order_line').filtered(lambda r: r.product_id == line.product_id)
            sale_orders = SaleOrder.search([('sale_agreement_id', '=', line.order_id.sale_agreement_id.id), ('state', '!=', 'cancel')])
            sale_order_line = sale_orders.mapped('order_line').filtered(lambda r: r.product_id == line.product_id and r.is_sa_product)
            ordered_quantity = sum(sale_order_line.mapped('product_uom_qty'))
            if ordered_quantity > sale_agreement_line.product_uom_qty:
                msg = "You cannot order qtys, greater than qtys left on the SA"
                raise ValidationError(_(msg))

    @api.multi
    def write(self, values):
        lines = minus_lines = False
        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            lines = self.filtered(
                lambda r: r.state == 'sale' and r.is_sa_product and float_compare(r.product_uom_qty, values['product_uom_qty'], precision_digits=precision) == -1)

            minus_lines = self.filtered(
                lambda r: r.state == 'sale' and r.is_sa_product and float_compare(r.product_uom_qty, values['product_uom_qty'], precision_digits=precision) == 1)
        if lines:
            # lines._action_launch_procurement_rule()
            for line in lines:
                picking = line.order_id.sale_agreement_id.picking_ids.filtered(lambda r: r.state != 'cancel')
                if picking:
                    picking.do_unreserve()

                    move_line = picking.move_lines.filtered(lambda r: r.product_id == line.product_id)
                    if move_line:
                        move_line.product_uom_qty = move_line.product_uom_qty - (values['product_uom_qty'] - line.product_uom_qty)
                if picking:
                    picking.action_assign()
        if minus_lines:
            # SA Picking Change
            for line in minus_lines:
                picking = line.order_id.sale_agreement_id.picking_ids.filtered(lambda r: r.state != 'cancel')
                if picking:
                    picking.do_unreserve()

                    move_line = picking.move_lines.filtered(lambda r: r.product_id == line.product_id)
                    if move_line:
                        move_line.product_uom_qty = move_line.product_uom_qty - (values['product_uom_qty'] - line.product_uom_qty)
                if picking:
                    picking.action_assign()
            # SO Picking Change
            # for line in minus_lines:
            #     picking = line.order_id.picking_ids.filtered(lambda r: r.state != 'cancel')
            #     if picking:
            #         picking.do_unreserve()
            # 
            #         move_line = picking.move_lines.filtered(lambda r: r.product_id == line.product_id)
            #         if move_line:
            #             move_line.product_uom_qty = move_line.product_uom_qty - (line.product_uom_qty - values['product_uom_qty'])
            #     if picking:
            #         picking.action_assign()
        return super(SaleOrderLine, self).write(values)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        super(SaleOrderLine, self).product_id_change()
        if self.order_id.sale_agreement_id:
            self.is_sa_product = True


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _compute_agreement_remaining_qty(self):
        SaleAgreementLine = self.env['sale.agreement.line']
        for product in self:
            sale_agreement_lines = SaleAgreementLine.search([('product_id', '=', product.id), ('state', '=', 'confirm'), ('order_id.agreement_type.show_remaining_quantity', '=', True)])
            product.agreement_remaining_qty = sum(sale_agreement_lines.mapped('qty_remaining'))

    agreement_remaining_qty = fields.Integer(string='Remaining Quantity', compute='_compute_agreement_remaining_qty')
    quantity_cartoon = fields.Float("Menge/Karton")
    weight_cartoon = fields.Float("Gewicht/Karton")
    quantity_pallet = fields.Float("Menge/Palette")

    @api.multi
    def action_view_sale_agreement_line(self):
        self.ensure_one()
        action = self.env.ref('sale_agreement.action_sale_agreement_line').read()[0]
        sale_agreement_lines = self.env['sale.agreement.line'].search([('product_id', '=', self.id), ('state', '=', 'confirm'), ('order_id.agreement_type.show_remaining_quantity', '=', True)])
        action['domain'] = [('id', 'in', sale_agreement_lines.ids)]
        return action


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        if values.get('agreement_line_id', False):
            result['agreement_line_id'] = values['agreement_line_id']
        return result
