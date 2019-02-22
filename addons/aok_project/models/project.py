# -*- coding: utf-8 -*-

from odoo import fields, models


class Project(models.Model):
    _inherit = "project.project"

    product_id = fields.Many2one('product.product', string='Product')
    product_ids = fields.Many2many('product.product', string="Products")
    partner_ids = fields.Many2many('res.partner', domain=[('customer', '=', True)], string="Customers")
