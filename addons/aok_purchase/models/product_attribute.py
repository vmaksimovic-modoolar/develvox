# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AttributeChecklistCategory(models.Model):
    _name = "attributes.checklist.category"

    name = fields.Char(string='Name', translate=True)
    attribute_ids = fields.One2many('attributes.checklist', 'category_id', string='Attributes')
    description = fields.Html(string='Description')


class AttributeChecklist(models.Model):
    _name = "attributes.checklist"

    name = fields.Char(string='Attribute Name', translate=True)
    category_id = fields.Many2one('attributes.checklist.category', string='Category')
    require = fields.Boolean(string="Required")


class ProductAttributesChecklist(models.Model):
    _name = "product.attributes.checklist"

    name = fields.Many2one("attributes.checklist", string="Attribute Name")
    product_id = fields.Many2one('product.product', string='Product')
    value = fields.Char('Value')
    require = fields.Boolean(string="Required")

    @api.constrains('require', 'value')
    def check_mandatory(self):
        for record in self:
            if record.require and not record.value:
                raise UserError(_("Please fill the mandatory Checklist Attribute Value."))
