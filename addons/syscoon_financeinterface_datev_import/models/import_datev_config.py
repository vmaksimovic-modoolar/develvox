#See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class ImportDatevConfig(models.Model):
    _name = 'import.datev.config'

    name = fields.Char('Name', default=lambda self: self.env.user.company_id.name)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    import_config_row_ids = fields.Many2many('import.datev.config.rows', string='Config Rows')
    delimiter = fields.Char('CSV Delimiter')
    encoding = fields.Char('Encoding')
    quotechar = fields.Char('Quotechar')
    headerrow = fields.Integer('Headerrow')
    skonto_account = fields.Many2one('account.account', string='Sconto Account Income')
    skonto_account_expenses = fields.Many2one('account.account', string='Sconto Account Expenses')
    ref = fields.Char('Reference')
    post_moves = fields.Boolean('Post Moves')
    auto_reconcile = fields.Boolean('Auto Reconcile')
    receivable_reconcile_field = fields.Many2one('import.datev.config.rows', string='Field for Receivable', help='Field with invoice number for receivable invoices.')
    payable_reconcile_field = fields.Many2one('import.datev.config.rows', string='Field for Payable', help='Field with invoice number for payable invoices.')
    payment_difference_handling = fields.Selection([('open', 'Keep open'), ('reconcile', 'Mark invoice as fully paid')], string="Payment Difference")
    skonto_account_automatic = fields.Boolean('Sconto Account automatic detection', default=False, help='If activated Odoo tries to find the sconto account by the given account in tax configuration. If it is not possible it uses the standard account.')

    _sql_constraints = [
        ('company_unique', 'unique(company_id)', 'Company must be unique!'),
    ]


class ImportDatevConfigRows(models.Model):
    _name = 'import.datev.config.rows'

    name = fields.Char('Name')
    import_datev_id = fields.Many2one('import.datev.config', string='Datev Config')
    csv_name = fields.Char(string='Column Name')
    csv_row = fields.Boolean(string='Row', default=False)
    type = fields.Selection([('string', 'String'), ('date', 'Date'), ('decimal', 'Decimal')], string='Type')
    dateformat = fields.Char(string='Dateformat')
    required = fields.Boolean(string='Required', default=False)
    erplookup = fields.Boolean(string='Search Model', default=True)
    erpobject = fields.Char(string='Model')
    erpfield = fields.Char(string='Field')
    domain = fields.Char(string='Domain')
    zerofill = fields.Integer(string='Fill with Zeros')
    decimalformat = fields.Char(string='Decimalformat')
    decimalreplacement = fields.Char(string='Decimal Replacement')
    skipon = fields.Char(string='Skip on')
    default = fields.Char(string='Default')
    cost1 = fields.Boolean(string='Cost 1')
    cost2 = fields.Boolean(string='Cost 2')

