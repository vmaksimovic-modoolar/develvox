# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    standard_price = fields.Float(digits=dp.get_precision('Standard Price'))
    is_encasing = fields.Boolean("Is Encasing")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    standard_price = fields.Float(digits=dp.get_precision('Standard Price'))
