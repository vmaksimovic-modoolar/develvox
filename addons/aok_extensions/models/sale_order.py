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

from odoo import models, fields, api


class SaleOrderBarcode(models.Model):
    _name = 'sale.order.barcode'
    _description = 'Sale Order Barcode'

    name = fields.Char(
        string='Barcode'
    )

    active = fields.Boolean(
        string='Active'
    )

    order_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='barcode_id',
        string='Sale Orders'
    )


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_note = fields.Char(
        string='Delivery Note'
    )

    subs_from = fields.Date(
        string='Subs From'
    )

    subs_to = fields.Date(
        string='Subs To'
    )

    barcode_id = fields.Many2one(
        comodel_name='sale.order.barcode',
        string='Barcode'
    )

    contact_person_id = fields.Many2one(
        string='Contact Person',
        comodel_name='res.partner',
        domain="[('parent_id', '=', partner_id)]"
    )
