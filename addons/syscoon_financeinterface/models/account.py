#See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import ustr
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('journal_id', 'line_ids', 'journal_id.default_debit_account_id', 'journal_id.default_credit_account_id')
    def _get_interface_datev_account(self):
        for move in self:
            value = False
            # If move has an invoice, return invoice's account_id
            invoice = self.env['account.invoice'].search([('move_id', '=', move.id)])
            if len(invoice):
                move.ecofi_account_counterpart = invoice[0].account_id
                continue
            # If move belongs to a bank journal, return the journal's account (debit/credit should normally be the same)
            if move.journal_id.type == 'bank' and move.journal_id.default_debit_account_id:
                move.ecofi_account_counterpart = move.journal_id.default_debit_account_id
                continue
            # If the move is an automatic exchange rate entry, take the gain/loss account set on the exchange journal
            elif move.journal_id.type == 'general' and move.journal_id == self.env.user.company_id.currency_exchange_journal_id:
                accounts = [
                    move.journal_id.default_debit_account_id,
                    move.journal_id.default_credit_account_id,
                ]
                lines = move.line_ids.filtered(lambda r: r.account_id in accounts)
                if len(lines) == 1:
                    move.ecofi_account_counterpart = lines.account_id
                    continue

            # Look for an account used a single time in the move, that has no originator tax
            aml_debit = self.env['account.move.line']
            aml_credit = self.env['account.move.line']
            for aml in move.line_ids:
                if aml.debit > 0:
                    aml_debit += aml
                if aml.credit > 0:
                    aml_credit += aml
            if len(aml_debit) == 1:
                value = aml_debit[0].account_id
            elif len(aml_credit) == 1:
                value = aml_credit[0].account_id
            else:
                aml_debit_wo_tax = [a for a in aml_debit if not a.tax_line_id]
                aml_credit_wo_tax = [a for a in aml_credit if not a.tax_line_id]
                if len(aml_debit_wo_tax) == 1:
                    value = aml_debit_wo_tax[0].account_id
                elif len(aml_credit_wo_tax) == 1:
                    value = aml_credit_wo_tax[0].account_id
            move.ecofi_account_counterpart = value

    vorlauf_id = fields.Many2one('ecofi', 'Export', readonly=True, ondelete='set null', index=2)
    ecofi_buchungstext = fields.Char('Export Voucher Text', size=30)
    ecofi_manual = fields.Boolean('Set Counteraccounts manual')
    ecofi_autotax = fields.Boolean('Automatic Tax Lines')
    ecofi_account_counterpart = fields.Many2one('account.account', compute='_get_interface_datev_account',
        help='Technical field needed for datev export')

    @api.multi
    def unlink(self):
        for thismove in self:
            if 'delete_none' in self._context:
                if self._context['delete_none'] is True:
                    continue
            if thismove.vorlauf_id:
                raise UserError(_('Warning!'), _('Account moves which are already in an export can not be deleted!'))
        return super(AccountMove, self).unlink()

    @api.multi
    def financeinterface_test_move(self, move):
        """ Test if the move account counterparts are set correct """
        res = ''
        checkdict = {}
        for line in move.line_ids:
            if line.account_id and move.ecofi_account_counterpart:
                if line.account_id.id != move.ecofi_account_counterpart.id:
                    if move.ecofi_account_counterpart.id not in checkdict:
                        checkdict[move.ecofi_account_counterpart.id] = {}
                        checkdict[move.ecofi_account_counterpart.id]['check'] = 0
                        checkdict[move.ecofi_account_counterpart.id]['real'] = 0
                    checkdict[move.ecofi_account_counterpart.id]['check'] += line.debit - line.credit
                else:
                    if move.ecofi_account_counterpart.id not in checkdict:
                        checkdict[move.ecofi_account_counterpart.id] = {}
                        checkdict[move.ecofi_account_counterpart.id]['check'] = 0
                        checkdict[move.ecofi_account_counterpart.id]['real'] = 0
                    checkdict[move.ecofi_account_counterpart.id]['real'] += line.debit - line.credit
            else:
                res += _('Not all move lines have an account and an account counterpart defined.')
                return res
        for key in checkdict:
            if abs(checkdict[key]['check'] + checkdict[key]['real']) > 10 ** -4:
                res += _('The sum of the account lines debit/credit and the account_counterpart lines debit/credit is no Zero!')
                return res
        return False

    @api.multi
    def finance_interface_checks(self):
        """Hook Method for different checks wich is called if the moves post method is called """
        for move in self:
            if move.company_id.finance_interface == 'none' or move.company_id.finance_interface == False:
                continue
            if len(move.line_ids) == 0:  # There is actually the possibility to post account moves w/o move lines
                continue
            thiserror = ''
            if move.ecofi_manual is False:
                error = self.env['ecofi'].set_main_account(move)
                if error:
                    thiserror += error
                if thiserror != '':
                    raise UserError(thiserror)
            error = self.financeinterface_test_move(move)
            if error:
                raise UserError(error)
        return True

    @api.multi
    def button_cancel(self):
        """Check if the move has already been exported"""
        res = super(AccountMove, self).button_cancel()
        for move in self:
            if move.vorlauf_id:
                raise UserError(_('You cannot modify an already exported move.'))
            if move.ecofi_autotax:
                for line in move.line_ids:
                    if line.ecofi_move_line_autotax:
                        self.env['account.move.line'].delete_autotaxline([line.id])
        return res

    @api.multi
    def post(self):
        """ If a move is posted to a journal the Datev corresponding checks are being performed.
        """
        for move in self:
            if move.ecofi_autotax:
                for line in move.line_ids:
                    if self.env['ecofi'].is_taxline(line.account_id.id) and not line.ecofi_move_line_autotax:
                        raise UserError(_('You can not create tax lines in an auto tax move.'))
                    self.env['account.move.line'].create_update_taxline([line.id])
        res = super(AccountMove, self).post()
        self.finance_interface_checks()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    ecofi_taxid = fields.Many2one('account.tax', 'Move Tax')
    ecofi_brutto_credit = fields.Float('Amount Credit Brutto', digits=dp.get_precision('Account'))
    ecofi_brutto_debit = fields.Float('Amount Debit Brutto', digits=dp.get_precision('Account'))
    ecofi_move_line_autotax = fields.Many2one('account.move.line', 'Move Counterpart', ondelete='cascade', index=2)
    ecofi_manual = fields.Boolean(relation='move_id.ecofi_manual', string="Manual", store=True)

    @api.multi
    def name_get(self):
        if 'counterpart_name' in self._context and self._context['counterpart_name']:
            result = []
            for line in self:
                if line.ref:
                    result.append((line.id, (line.name or '') + ' (' + line.ref + ')'))
                else:
                    result.append((line.id, line.name))
            return result
        else:
            return super(AccountMoveLine, self).name_get()

    @api.multi
    def delete_autotaxline(self, move_lineids):
        """ Method that deletes the corresponding auto generated tax moves"""
        for move_line in move_lineids:
            move_line_main = self.browse(move_line.ecofi_move_line_autotax.id)
            update = {
                'debit': move_line_main.ecofi_brutto_debit,
                'credit': move_line_main.ecofi_brutto_credit,
                'tax_code_id': False,
                'tax_amount': 0.00,
            }
            self.unlink()
            self.write(update)
        return True

    @api.multi
    def create_update_taxline(self):
        "Method to create Tax Lines in manual Mode"
        tax_obj = self.env['account.tax']
        for move_line in self:
            if move_line.ecofi_move_line_autotax:
                self.delete_autotaxline([move_line.id])
            if move_line.ecofi_taxid:
                journal = self.env['account.journal'].browse(move_line.move_id.journal_id.id)
                tax_id = tax_obj.browse(move_line.ecofi_taxid.id)
                total = move_line.debit - move_line.credit
                if journal.type in ('purchase_refund', 'sale_refund'):
                    base_code = 'ref_base_code_id'
                    tax_code = 'ref_tax_code_id'
                    account_id = 'refund_account_id'
                    base_sign = 'ref_base_sign'
                    tax_sign = 'ref_tax_sign'
                else:
                    base_code = 'base_code_id'
                    tax_code = 'tax_code_id'
                    account_id = 'account_id'
                    base_sign = 'base_sign'
                    tax_sign = 'tax_sign'
                all_taxes = {
                        'debit': 0,
                        'credit': 0,
                }
                tmp_cnt = 0
                real_tax_code_id = False
                real_tax_amount = 0
                for tax in tax_obj.compute_all_inv([tax_id], total, 1.00, force_excluded=True).get('taxes'):
                    data = {
                        'move_id': move_line.move_id.id,
                        'name': ustr(move_line.name or '') + ' ' + ustr(tax['name'] or ''),
                        'date': move_line.date,
                        'partner_id': move_line.partner_id and move_line.partner_id.id or False,
                        'ref': move_line.ref and move_line.ref or False,
                        'tax_line_id': False,
                        'tax_code_id': tax[tax_code],
                        'tax_amount': tax[tax_sign] * abs(tax['amount']),
                        'account_id': tax[account_id] or move_line.account_id.id,
                        'credit': tax['amount'] < 0 and -tax['amount'] or 0.0,
                        'debit': tax['amount'] > 0 and tax['amount'] or 0.0,
                        'ecofi_move_line_autotax': move_line.id,
                    }
                    if data['tax_code_id']:
                        self.create(data)
                    if tmp_cnt == 0:
                        if tax[base_code]:
                            tmp_cnt += 1
                            real_tax_code_id = tax[base_code]
                            real_tax_amount = tax[base_sign] * abs(total)
                    all_taxes['debit'] += data['debit']
                    all_taxes['credit'] += data['credit']
                if all_taxes['debit'] >= all_taxes['credit']:
                    all_taxes['debit'] = all_taxes['debit'] - all_taxes['credit']
                    all_taxes['credit'] = 0
                else:
                    all_taxes['credit'] = all_taxes['credit'] - all_taxes['debit']
                    all_taxes['debit'] = 0
                actual_move = self.browse(move_line.id)
                self.write({
                    'ecofi_brutto_credit': actual_move.credit,
                    'ecofi_brutto_debit': actual_move.debit,
                    'debit': actual_move.debit - all_taxes['debit'],
                    'credit': actual_move.credit - all_taxes['credit'],
                    'tax_code_id': real_tax_code_id,
                    'tax_amount': real_tax_amount
                })

    @api.model
    def create(self, vals):
        if vals.get('statement_line_id'):
            account_id = self.env['account.account'].browse(vals['account_id'])
            if account_id.user_type_id.type == 'regular' or account_id.user_type_id.type == 'other':
                if vals.get('tax_ids'):
                    vals['ecofi_taxid'] = vals['tax_ids'][0][1]
        if 'ecofi_taxid' not in vals and 'tax_ids' in vals:
            if vals['tax_ids'] and vals['tax_ids'][0][2]:
                vals['ecofi_taxid'] = vals['tax_ids'][0][2][0]
        res = super(AccountMoveLine, self).create(vals)
        return res


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    ecofi_buchungstext =  fields.Char('Export Voucher Text', size=30)
    vorlauf_id = fields.Many2one('ecofi', 'Export', readonly=True, ondelete='set null', index=2)

    def inv_line_characteristic_hashcode(self, invoice_line):
        """Transfers the line tax to the hash code
        """
        res = super(account_invoice, self).inv_line_characteristic_hashcode(invoice_line)
        res += "-%s" % (invoice_line.get('ecofi_taxid', "False"))
        return res

    @api.model
    def line_get_convert(self, line, part):
        """Extends the line_get_convert method that it transfers the tax to the account_move_line
        """
        res = super(account_invoice, self).line_get_convert(line, part)
        if line.get('tax_ids', False):
            for tax in line.get('tax_ids', False):
                res['ecofi_taxid'] = tax[1]
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
 
    @api.model
    def create(self, vals):
        """Prevent that a user places two different taxes in an invoice line
        """
        if vals.get('invoice_line_tax_id', False):
            if len(vals['invoice_line_tax_id'][0][2]) > 1:
                raise UserError(_("""There can only be one tax per invoice line"""))
        result = super(AccountInvoiceLine, self).create(vals)
        return result

    @api.model
    def write(self, vals):
        """Prevent that a user places two different taxes in an invoice line
        """
        if vals.get('invoice_line_tax_id', False):
            if len(vals['invoice_line_tax_id'][0][2]) > 1:
                raise UserError(_("""There can only be one tax per invoice line"""))
        return super(AccountInvoiceLine, self).write(vals)


class AccountTax(models.Model):
    """Inherits the account.tax class and adds attributes
    """
    _inherit = 'account.tax'

    buchungsschluessel = fields.Integer('Posting key', default=lambda * a: -1, required=True)

    @api.model 
    def compute_all_inv(self, cr, uid, taxes, price_unit, quantity, product=None, partner=None, force_excluded=False):
        """
        :param force_excluded: boolean used to say that we don't want to consider the value of field price_include of
            tax. It's used in encoding by line where you don't matter if you encoded a tax with that boolean to True or
            False
        RETURN: {
                'total': 0.0,                # Total without taxes
                'total_included: 0.0,        # Total with taxes
                'taxes': []                  # List of taxes, see compute for the format
            }
        """

        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line

        precision = self.env['decimal.precision'].precision_get('Account')
        tax_compute_precision = precision
        if taxes and taxes[0].company_id.tax_calculation_rounding_method == 'round_globally':
            tax_compute_precision += 5
        totalin = totalex = float_round(price_unit * quantity, precision)
        tin = []
        tex = []
        for tax in taxes:
            tin.append(tax)
        tin = self.compute_inv(cr, uid, tin, price_unit, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tin:
            totalex -= r.get('amount', 0.0)
        totlex_qty = 0.0
        try:
            totlex_qty = totalex / quantity
        except:
            pass
        tex = self._compute(cr, uid, tex, totlex_qty, quantity, product=product, partner=partner, precision=tax_compute_precision)
        for r in tex:
            totalin += r.get('amount', 0.0)
        return {
            'total': totalex,
            'total_included': totalin,
            'taxes': tin + tex
        }
