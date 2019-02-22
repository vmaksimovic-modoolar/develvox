#See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    """ Inherits the res.company class and adds methods and attributes
    .. automethod:: _finance_interface_selection
    """
    _inherit = 'res.company'

    finance_interface = fields.Selection(selection=[('none', 'None')])
