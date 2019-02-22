##############################################################################
#
# Copyright (c) 2018 - Now Modoolar (http://modoolar.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract support@modoolar.com
#
##############################################################################

from odoo import models, fields, api, exceptions, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    published = fields.Selection(
        selection=[
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly')
        ],
        string='Published'
    )

    isbn_number = fields.Char(
        string='ISBN Number',
    )

    page_number = fields.Integer(
        string='Page Number'
    )

    printing = fields.Integer(
        string='Printing'
    )

    no_subscription = fields.Integer(
        string='No subscription'
    )

    copyright = fields.Char(
        string='Copyright'
    )

    product_performance = fields.Text(
        string='Product Performance'
    )

    type = fields.Selection(
        default='product'
    )

    # General Information

    prev_product_id = fields.Many2one(
        comodel_name='product.template',
        string='Previous product'
    )

    follow_up_product_id = fields.Many2one(
        comodel_name='product.template',
        string='Follow-up Product'
    )

    tag_ids = fields.Many2many(
        comodel_name='product.template.tag',
        relation='tag_product_rel',
        column1='product_id',
        column2='tag_id',
        string='Tags'
    )

    # Purchase Information

    purchase_responsible_id = fields.Many2one(
        comodel_name='res.users',
        string='Purchase Responsible',
        compute='_compute_purchase_responsible',
        inverse='_set_purchase_responsible',
        store=True
    )

    competency_tag_id = fields.Many2one(
        comodel_name='product.template.competency.tag',
        string='Core Competency'
    )

    # Quotations

    quotations_count = fields.Integer(
        compute='_compute_quotations_count',
        string='Quotations'
    )

    internal_info_purchase = fields.Text('Internal Info Purchase')
    internal_info_publisher = fields.Text('Internal Info Publisher')

    sale_ok = fields.Boolean(
        readonly=True,
        compute='_compute_sale_ok',
        search='_search_sale_ok',
    )
    purchase_ok = fields.Boolean(
        readonly=True,
        compute='_compute_purchase_ok',
        search='_search_purchase_ok',
    )

    product_status = fields.Many2one(
        comodel_name='product.template.status',
    )

    def prev_next_prod(self, vals):

        if 'prev_product_id' in vals:
            super(ProductTemplate, self.prev_product_id).write({
                'follow_up_product_id': self.id,
            })

        if 'follow_up_product_id' in vals:
            super(ProductTemplate, self.follow_up_product_id).write({
                'prev_product_id': self.id,
            })


    @api.multi
    def write(self, vals):
        if ('prev_product_id' in vals or 'follow_up_product_id' in vals) and len(self) > 1:
            raise exceptions.UserError(_("A product can only have one previous or follow-up product!"))

        res = super(ProductTemplate, self).write(vals)

        self.prev_next_prod(vals)

        return res

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)

        res.prev_next_prod(vals)

        return res


    def _search_sale_ok(self, operator, value):
        if operator not in ('=', '!=', '<>'):
            raise ValueError('Invalid operator: %s' % (operator,))

        value = bool(value)

        search_query = """
            SELECT
                pt.id
            FROM 
                product_template AS pt INNER JOIN product_product AS pp 
            ON
                pt.id = pp.product_tmpl_id      
            GROUP BY
                pt.id
            HAVING 
                bool_or(pp.sale_ok) %s %s
            """ % (operator, value)

        self.env.cr.execute(search_query)
        res_ids = [x[0] for x in self.env.cr.fetchall()]

        return [('id', 'in', res_ids)]

    def _search_purchase_ok(self, operator, value):
        if operator not in ('=', '!=', '<>'):
            raise ValueError('Invalid operator: %s' % (operator,))

        value = bool(value)

        search_query = """
            SELECT
                pt.id
            FROM 
                product_template AS pt INNER JOIN product_product AS pp 
            ON
                pt.id = pp.product_tmpl_id      
            GROUP BY
                pt.id
            HAVING 
                bool_or(pp.purchase_ok) %s %s
            """ % (operator, value)

        self.env.cr.execute(search_query)
        res_ids = [x[0] for x in self.env.cr.fetchall()]

        return [('id', 'in', res_ids)]

    @api.multi
    @api.depends('product_variant_ids.sale_ok')
    def _compute_sale_ok(self):
        for record in self:
            tf = any(record.product_variant_ids.filtered(lambda o: o.sale_ok))
            record.sale_ok = tf

    @api.multi
    @api.depends('product_variant_ids.purchase_ok')
    def _compute_purchase_ok(self):
        for record in self:
            tf = any(
                record.product_variant_ids.filtered(lambda o: o.purchase_ok))
            record.purchase_ok = tf

    @api.multi
    def _compute_quotations_count(self):
        """ Calculate number of Quotations with specific product """
        SaleOrderModel = self.env['sale.order']

        for record in self:
            cnt = SaleOrderModel.search_count([
                ('order_line.product_id.product_tmpl_id.id', '=', record.id),
                ('state', 'in', ['draft', 'sent']),
            ])
            record.quotations_count = cnt

    @api.depends('product_variant_ids',
                 'product_variant_ids.purchase_responsible_id')
    def _compute_purchase_responsible(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.purchase_responsible_id = template.product_variant_ids.purchase_responsible_id
        for template in (self - unique_variants):
            template.purchase_responsible_id = None

    @api.one
    def _set_purchase_responsible(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.purchase_responsible_id = self.purchase_responsible_id


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_prod_performance = fields.Text(
        string='Product Performance'
    )

    purchase_responsible_id = fields.Many2one(
        comodel_name='res.users',
        string='Purchase Responsible',
        track_visibility='onchange',
    )

    sale_ok = fields.Boolean(
        string='Can be Sold',
        default=True,
        help="Specify if the product can be selected in a sales order line."
    )

    purchase_ok = fields.Boolean(
        string='Can be Purchased',
        default=True
    )

    description_sale = fields.Text(
        'Sale Description', translate=True,
        help="A description of the Product that you want to communicate to your customers. "
             "This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note"
    )

    description_purchase = fields.Text(
        'Purchase Description', translate=True,
        help="A description of the Product that you want to communicate to your vendors. "
             "This description will be copied to every Purchase Order, Receipt and Vendor Bill/Credit Note."
    )

    product_status = fields.Many2one(
        comodel_name='product.template.status',
    )

    _sql_constraints = [
        ('default_code_uniq', 'unique (default_code)',
         "Internal reference already exists!"
         ),
    ]

    @api.model
    def create(self, vals):
        """ If we didn't set Internal reference create it automatically
        This works only if we create product from product.product form
        """
        # if not self._context.get('create_from_tmpl', False):
        if not vals.get('default_code', False):
            vals['default_code'] = self.env['ir.sequence'].next_by_code(
                'product.internal.reference'
            )
        return super(ProductProduct, self).create(vals)


class ProductAbstractTag(models.AbstractModel):
    _name = 'product.abstract.tag'
    _description = 'Product Abstract Tag'

    name = fields.Char(
        string='Tag Name',
        required=True,
        index=True,
        translate=True
    )

    color = fields.Integer(
        string='Color Index'
    )

    active = fields.Boolean(
        default=True,
        help="The active field allows you to hide "
             "the category without removing it."
    )


class ProductTemplateTag(models.Model):
    _name = 'product.template.tag'
    _inherit = 'product.abstract.tag'
    _description = 'Product Tags'

    product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='tag_product_rel',
        column1='tag_id',
        column2='product_id',
        string='Products'
    )


class ProductTemplateStatus(models.Model):
    _name = 'product.template.status'
    _description = 'Product Template Status'
    _order = 'sequence, id'

    name = fields.Char(
        required=True,
    )

    sequence = fields.Integer(
        help="Determine the display order",
    )


class ProductTemplateCompetencyTag(models.Model):
    _name = 'product.template.competency.tag'
    _inherit = 'product.abstract.tag'
    _description = 'Product Core Competency Tags'

    product_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='competency_tag_id',
        string='Products'
    )
