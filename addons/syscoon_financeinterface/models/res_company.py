#See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    """ Inherits the res.company class and adds methods and attributes
    .. automethod:: _finance_interface_selection
    """
    _inherit = 'res.company'

    finance_interface = fields.Selection(selection=[('none', 'None')])
    journal_ids = fields.Many2many(comodel_name='account.journal',
                                   relation='res_company_account_journal',
                                   column1='res_company_id',
                                   column2='account_journal_id',
                                   string='Journal',
                                   domain="[('company_id', '=', active_id)]")
