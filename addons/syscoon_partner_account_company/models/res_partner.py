# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_number = fields.Char(string='Customer Number')
    supplier_number = fields.Char(string='Supplier Number')