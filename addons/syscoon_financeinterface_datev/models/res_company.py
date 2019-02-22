#See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    """ Inherits the res.company class and adds methods and attributes
    .. automethod:: _finance_interface_selection
    """
    _inherit = 'res.company'

    finance_interface = fields.Selection(selection_add=[('datev', 'Datev Export')], string='Finance Interface')
    journal_ids = fields.Many2many(comodel_name='account.journal',
                                   relation='res_company_account_journal',
                                   column1='res_company_id',
                                   column2='account_journal_id',
                                   string='Journal',
                                   domain="[('company_id', '=', active_id)]")
    exportmethod = fields.Selection(selection=[('netto', 'netto'), ('brutto', 'brutto')], string='Export method')
    enable_datev_checks = fields.Boolean('Perform Datev Checks', default=True)
    enable_fixing = fields.Boolean('Enable Fixing Moves in Datev', default=False)
    tax_accountant_id = fields.Char('Tax Accountant Number', size=6)
    client_id = fields.Char('Client Number', size=6)
    voucher_date_format = fields.Char(string='Belegdatum Format', 
        help='Format:\nTag = dd\nMonat = mm\nJahr = jjjj', default='ddmmjjjj')

