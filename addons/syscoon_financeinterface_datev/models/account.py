#See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from decimal import Decimal


class account_account(models.Model):
    _inherit = 'account.account'

    ustuebergabe = fields.Boolean('Datev VAT-ID', help=_(u'Is required when transferring a sales tax identification number from the account partner (e.g. EU-Invoice)'))
    automatic = fields.Boolean('Datev Automatic Account')
    datev_steuer = fields.Many2many('account.tax', string='Datev Tax Account', domain=[('buchungsschluessel', '!=', -1)])
    datev_steuer_erforderlich = fields.Boolean('Tax posting required?')

    @api.multi
    def cron_update_line_autoaccounts_tax(self):
        """Method for Cronjop that Updates all account.move.lines
        without ecofi_taxid of Accounts where automatic is True and a datev_steuer
        """
        ids = self.search([('automatic', '=', True), ('datev_steuer', '!=', False)])
        for account in self.read(load='_classic_write'):
            move_line_ids = self.env['account.move.line'].search([('account_id', '=', account['id']), ('ecofi_taxid', '=', False)])
            if move_line_ids:
                self.env['account.move.line'].write({'ecofi_taxid': account['datev_steuer']})


class AccountTax(models.Model):
    _inherit = 'account.tax'

    datev_skonto = fields.Many2one('account.account', 'Datev Cashback Account')


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    zahlsl = fields.Integer('Payment key')


class AccountMove(models.Model):
    _inherit = 'account.move'

    enable_datev_checks = fields.Boolean('Perform Datev Checks', default=True)

    @api.multi
    def datev_account_checks(self, move):
        errors = list()
        self.update_line_autoaccounts_tax(move)
        for linecount, line in enumerate(move.line_ids, start=1):
            if line.account_id.id != line.ecofi_account_counterpart.id:
                if not self.env['ecofi'].is_taxline(line.account_id.id) or line.ecofi_bu == 'SD':
                    linetax = self.env['ecofi'].get_line_tax(line)
                    if line.account_id.automatic and not line.account_id.datev_steuer:
                        errors.append(_(u'The account {account} is an Auto-Account but the automatic taxes are not configured!').format(
                            account=line.account_id.code))
                    if line.account_id.datev_steuer_erforderlich and not linetax:
                        errors.append(_(u'The Account requires a tax but the move line {line} has no tax!').format(line=linecount))
                    if line.account_id.automatic and linetax:
                        if not line.account_id.datev_steuer or linetax.id not in line.account_id.datev_steuer.ids:
                            tax_datev = []
                            for id in line.account_id.datev_steuer:
                                tax_datev.append(id.name)
                            errors.append(_(
                                u'The account is an Auto-Account but the tax account ({line}) in the move line {tax_line} differs from the configured {tax_datev}!').format(
                                    line=linecount, tax_line=linetax.name, tax_datev=','.join(tax_datev)))
                    if line.account_id.automatic and not linetax:
                        errors.append(_(u'The account is an Auto-Account but the tax account in the move line {line} is not set!').format(line=linecount))
                    if not line.account_id.automatic and linetax and linetax.buchungsschluessel < 0:
                        errors.append(_(u'The booking key for the tax {tax} is not configured!').format(tax=linetax.name))
        return '\n'.join(errors)

    @api.multi
    def update_line_autoaccounts_tax(self, move):
        errors = list()
        for linecount, line in enumerate(move.line_ids, start=1):
            if line.account_id.id != line.ecofi_account_counterpart.id:
                if not self.env['ecofi'].is_taxline(line.account_id.id):
                    linetax = self.env['ecofi'].get_line_tax(line)
                    if line.account_id.automatic and not linetax:
                        if line.account_id.datev_steuer:
                            self.env['account.move.line'].write({'ecofi_taxid': line.account_id.datev_steuer and line.account_id.datev_steuer[0].id or False})
                        else:
                            errors.append(_(u'The Account is an Auto-Account but the move line {line} has no tax!').format(line=linecount))
        return '\n'.join(errors)

    @api.multi
    def datev_tax_check(self, move):
        errors = list()
        linecount = 0
        tax_values = dict()
        linecounter = 0
        for line in move.line_ids:
            linecount += 1
            if line.account_id.id != line.ecofi_account_counterpart.id:
                if self.env['ecofi'].is_taxline(line.account_id.id) and not line.ecofi_bu == 'SD':
                    if line.account_id.code not in tax_values:
                        tax_values[line.account_id.code] = {
                            'real': 0.0,
                            'datev': 0.0
                        }
                    tax_values[line.account_id.code]['real'] += line.debit - line.credit
                else:
                    linecounter += 1
                    new_context = self._context
                    new_context['return_calc'] = True
                    taxcalc_ids = self.env['ecofi'].calculate_tax(line)
                    for taxcalc_id in taxcalc_ids:
                        taxaccount = taxcalc_id['account_paid_id'] and taxcalc_id['account_paid_id'] or taxcalc_id['account_collected_id']
                        if taxaccount:
                            datev_account_code = self.env['account.account'].read(taxaccount)['code']
                            if datev_account_code not in tax_values:
                                tax_values[datev_account_code] = {
                                    'real': 0.0,
                                    'datev': 0.0,
                                }
                            if line.ecofi_bu and line.ecofi_bu == '40':
                                continue
                            tax_values[datev_account_code]['datev'] += taxcalc_id['amount']

        sum_real = 0.0
        sum_datev = 0.0
        for value in tax_values.itervalues():
            sum_real += value['real']
            sum_datev += value['datev']
        if Decimal(str(abs(sum_real - sum_datev))) > Decimal(str(10 ** -2 * linecounter)):
            errors.append(_(u'The sums for booked ({real}) and calculated ({datev}) are different!').format(
                real=sum_real, datev=sum_datev))

        return '\n'.join(errors)

    @api.multi
    def datev_checks(self, move):
        errors = list()
        errors.append(self.update_line_autoaccounts_tax(move))
        errors.append(self.datev_account_checks(move))
        if not errors:
            errors.append(self.datev_tax_check(move))
        return '\n'.join(filter(lambda e: bool(e), errors)) or False

    @api.model
    def finance_interface_checks(self):
        res = True
        context = self._context
        if 'invoice' not in context or context['invoice'] and context['invoice'].enable_datev_checks:
            for move in self:
                if move.enable_datev_checks and self._uid:
                    res &= super(AccountMove, self).finance_interface_checks()
                    error = self.datev_checks(move)
                    if error:
                        raise UserError(error)
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    ecofi_bu = fields.Selection([
        ('40', '40'),
        ('SD', 'Steuer Direkt')
    ], 'Datev BU', index=True)
