#See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class AccountTax(models.Model):
    _inherit = 'account.tax'

    bookingform_taxkey = fields.Char('Bookingform Taxkey')