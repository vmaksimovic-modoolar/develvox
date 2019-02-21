# Copyright (c) 2018 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
from odoo import fields, models, api

class ProductPackagingdpdCloude(models.Model):
    _inherit = 'product.packaging'
    package_carrier_type = fields.Selection(selection_add=[("dpd_ept", "DPD Cloud Shipping")])