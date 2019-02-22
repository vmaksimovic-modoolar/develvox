# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountTax(models.Model):
    _inherit = 'account.tax'

    discount_account_id = fields.Many2one('account.account', domain=[('deprecated', '=', False)], string='Discount Account', ondelete='restrict')

    def get_grouping_key_aok(self, invoice_tax_val, group_by='group_by_tax'):
        """ Returns a string that will be used to group account.invoice.tax sharing the same properties"""
        self.ensure_one()
        if group_by == 'group_by_account':
            return str(invoice_tax_val['line_account_id']) + '-' + str(invoice_tax_val['tax_id']) + '-' + str(invoice_tax_val['account_id']) + '-' + str(invoice_tax_val['account_analytic_id'])
        elif group_by == 'group_by_tax':
            return str(invoice_tax_val['tax_id']) + '-' + str(invoice_tax_val['account_id']) + '-' + str(invoice_tax_val['account_analytic_id'])


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    one_due_amount = fields.Boolean('Create one due amount', default=True)

    @api.one
    def compute(self, value, date_ref=False):
        date_ref = date_ref or fields.Date.today()
        amount = value
        sign = value < 0 and -1 or 1
        result = []
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id
        for line in self.line_ids:
            if line.value == 'fixed':
                amt = sign * currency.round(line.value_amount)
            elif line.value == 'percent':
                amt = currency.round(value * (line.value_amount / 100.0))
            elif line.value == 'balance':
                amt = currency.round(amount)
            if amt:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days)
                elif line.option == 'fix_day_following_month':
                    next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=line.days - 1)
                elif line.option == 'last_day_following_month':
                    next_date += relativedelta(day=31, months=1)  # Getting last day of next month
                elif line.option == 'last_day_current_month':
                    next_date += relativedelta(day=31, months=0)  # Getting last day of next month
                result.append((fields.Date.to_string(next_date), amt))
                amount -= amt
        amount = sum(amt for _, amt in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist))
        if self.one_due_amount:
            return [(result[-1][0], value)]
        return result

    @api.one
    def compute_payment_term_date(self, value, date_ref=False):
        date_ref = date_ref or fields.Date.today()
        amount = value
        sign = value < 0 and -1 or 1
        result = []
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id
        for line in self.line_ids.sorted():
            if line.value == 'fixed':
                amt = sign * currency.round(line.value_amount)
            elif line.value == 'percent':
                amt = currency.round(value * (line.value_amount / 100.0))
            elif line.value == 'balance':
                amt = currency.round(amount)
            if amt:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days)
                elif line.option == 'fix_day_following_month':
                    next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=line.days - 1)
                elif line.option == 'last_day_following_month':
                    next_date += relativedelta(day=31, months=1)  # Getting last day of next month
                elif line.option == 'last_day_current_month':
                    next_date += relativedelta(day=31, months=0)  # Getting last day of next month
                result.append((fields.Date.to_string(next_date), amt, line))
                amount -= amt
        amount = sum(amt for _, amt, _ in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist, line))
#         if self.one_due_amount:
#             return [(result[-1][0], value, line)]
        return result


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    consider_payment_discount = fields.Boolean("Consider Payment Discount", default=True)


class AccountPaymentLine(models.Model):
    _inherit = 'account.payment.line'

    def _compute_all(self):
        for line in self:
            sum = 0.0
            dates = []
            for discount in line.payment_line_discount_ids:
                sum += discount.payment_discount
                dates.append(discount.discount_due_date)
            line.payment_discount = sum
            line.discount_due_date = min(dates) if dates else False
            line.discounted_amount = line.amount_currency - sum

    payment_line_discount_ids = fields.One2many('account.payment.line.discount', 'payment_line_id', string="Payment Order Line Discount")
    payment_discount = fields.Monetary(compute="_compute_all", string="Payment Discount", currency_field='currency_id')
    deduct_discount = fields.Boolean("Deduct Discount")
    discount_due_date = fields.Date(compute="_compute_all", string="Discount Due Date")
    discounted_amount = fields.Monetary(compute="_compute_all", string="Discounted Amount", currency_field='currency_id')


class AccountPaymentLineDiscount(models.Model):
    _name = 'account.payment.line.discount'
    _description = 'Payment Line Discount'

    def _compute_all(self):
        for record in self:
            invoice = record.payment_line_id.move_line_id.invoice_id
            record.invoice_amount = record.invoice_tax_id.base + record.invoice_tax_id.amount_total

            date_invoice = invoice.date_invoice
            if not date_invoice:
                date_invoice = fields.Date.context_today(self)

            pterm = invoice.payment_term_id
            pterm_list = pterm.with_context(currency_id=invoice.company_id.currency_id.id).compute_payment_term_date(value=record.invoice_amount, date_ref=date_invoice)
            pterm_list = pterm_list and pterm_list[0] or []
            discount_date = payment_discount = False
            payment_discount_amount = 0.0
            for line in pterm_list:
                if line[2].value == 'percent' and fields.Date.from_string(line[0]) >= fields.Date.from_string(fields.Date.context_today(self)):
                    discount_date = line[0]
                    payment_discount = line[2].value_amount
                    payment_discount_amount = line[1]
                    break
            record.discount_due_date = discount_date
            record.payment_discount_perc = payment_discount
            record.payment_discount = payment_discount_amount

    payment_line_id = fields.Many2one("account.payment.line", string="Payment Line")
    currency_id = fields.Many2one(
        'res.currency', string='Currency of the Payment Transaction',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id)
    invoice_amount = fields.Monetary(compute="_compute_all", string="Invoice Amount", currency_field='currency_id')
    discount_due_date = fields.Date(compute="_compute_all", string="Discount Due Date")
    payment_discount_perc = fields.Float(compute="_compute_all", string="Payment Discount %")
    payment_discount = fields.Monetary(compute="_compute_all", string="Payment Discount", currency_field='currency_id')
    tax_id = fields.Many2one("account.tax", string="Tax")
    account_id = fields.Many2one("account.account", string="Account")
    invoice_tax_id = fields.Many2one('account.invoice.tax.aok', string="Account Invoice Tax")


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    consider_payment_discount = fields.Boolean(related="payment_mode_id.consider_payment_discount", string="Consider Payment Discount")

    @api.multi
    def draft2open(self):
        AccountPaymentLineDiscount = self.env['account.payment.line.discount']
        AccountInvoiceTax = self.env['account.invoice.tax.aok']
        for order in self:
            for line in order.payment_line_ids:
                if line.move_line_id.invoice_id:
                    invoice = line.move_line_id.invoice_id
                    # Unlink the existing invoice tax records.
                    account_invoice_tax = AccountInvoiceTax.search([('invoice_id', '=', invoice.id)])
                    account_invoice_tax.unlink()
                    lines_by_account = invoice.compute_taxes_aok('group_by_account')
                    for tax_line in lines_by_account:
                        AccountPaymentLineDiscount.create({'payment_line_id': line.id, 'tax_id': tax_line.tax_id.id, 'account_id': tax_line.line_account_id.id, 'invoice_tax_id': tax_line.id})
                    lines_by_tax = invoice.compute_taxes_aok('group_by_tax')
                    for tax_line in lines_by_tax:
                        AccountPaymentLineDiscount.create({'payment_line_id': line.id, 'tax_id': tax_line.tax_id.id, 'account_id': tax_line.tax_id.discount_account_id.id, 'invoice_tax_id': tax_line.id})
        return super(AccountPaymentOrder, self).draft2open()

    @api.multi
    def _prepare_move_line_offsetting_account(
            self, amount_company_currency, amount_payment_currency,
            bank_lines):
        vals = {}
        if self.payment_type == 'outbound':
            name = _('Payment order %s') % self.name
        else:
            name = _('Debit order %s') % self.name
        if self.payment_mode_id.offsetting_account == 'bank_account':
            vals.update({'date': bank_lines[0].date})
        else:
            vals.update({'date_maturity': bank_lines[0].date, 'date': bank_lines[0].date})

        if self.payment_mode_id.offsetting_account == 'bank_account':
            account_id = self.journal_id.default_debit_account_id.id
        elif self.payment_mode_id.offsetting_account == 'transfer_account':
            account_id = self.payment_mode_id.transfer_account_id.id
        partner_id = False
        for index, bank_line in enumerate(bank_lines):
            if index == 0:
                partner_id = bank_line.payment_line_ids[0].partner_id.id
            elif bank_line.payment_line_ids[0].partner_id.id != partner_id:
                # we have different partners in the grouped move
                partner_id = False
                break
        vals.update({
            'name': name,
            'partner_id': partner_id,
            'account_id': account_id,
            'credit': (self.payment_type == 'outbound' and
                       amount_company_currency or 0.0),
            'debit': (self.payment_type == 'inbound' and
                      amount_company_currency or 0.0),
        })
        if bank_lines[0].currency_id != bank_lines[0].company_currency_id:
            sign = self.payment_type == 'outbound' and -1 or 1
            vals.update({
                'currency_id': bank_lines[0].currency_id.id,
                'amount_currency': amount_payment_currency * sign,
                })
        return vals

    @api.multi
    def generate_move(self):
        """
        Create the moves that pay off the move lines from
        the payment/debit order.
        """
        self.ensure_one()
        am_obj = self.env['account.move']
        post_move = self.payment_mode_id.post_move
        # prepare a dict "trfmoves" that can be used when
        # self.payment_mode_id.move_option = date or line
        # key = unique identifier (date or True or line.id)
        # value = bank_pay_lines (recordset that can have several entries)
        trfmoves = {}
        for bline in self.bank_line_ids:
            hashcode = bline.move_line_offsetting_account_hashcode()
            if hashcode in trfmoves:
                trfmoves[hashcode] += bline
            else:
                trfmoves[hashcode] = bline

        for hashcode, blines in trfmoves.items():
            mvals = self._prepare_move(blines)
            total_company_currency = total_payment_currency = 0
            for bline in blines:
                total_company_currency += bline.amount_company_currency
                total_payment_currency += bline.amount_currency
                partner_ml_vals = self._prepare_move_line_partner_account(
                    bline)
                mvals['line_ids'].append((0, 0, partner_ml_vals))
            trf_ml_vals = self._prepare_move_line_offsetting_account(
                total_company_currency, total_payment_currency, blines)
            split_vals = self._split_lines(blines, trf_ml_vals)
            for vals in split_vals:
                mvals['line_ids'].append(vals)
            move = am_obj.create(mvals)
            blines.reconcile_payment_lines()
            if post_move:
                move.post()

    @api.multi
    def _split_lines(self, blines, trf_ml_vals=None):
        self.ensure_one()
        if trf_ml_vals is None:
            trf_ml_vals = {}
        for bline in blines:
            list1 = []
            total_discount = 0.0
            for payment_line in bline.payment_line_ids:
                for discount in payment_line.payment_line_discount_ids:
                    invoice_tax = discount.invoice_tax_id
                    if invoice_tax:
                        base_discount = (invoice_tax.base * discount.payment_discount_perc / 100)
                        tax_discount = (invoice_tax.amount_total * discount.payment_discount_perc / 100)
                        total_discount += base_discount + tax_discount
                        #  discount_account = invoice_tax.tax_id.discount_account_id
                        list1.append((0, 0, {'credit': tax_discount, 'name': 'Payment Discount', 'debit': 0.0, 'partner_id': trf_ml_vals.get('partner_id'), 'date': trf_ml_vals.get('date'), 'account_id': invoice_tax.account_id.id}))
                        list1.append((0, 0, {'credit': base_discount, 'name': 'Payment Tax Discount', 'debit': 0.0, 'partner_id': trf_ml_vals.get('partner_id'), 'date': trf_ml_vals.get('date'), 'account_id': discount.account_id.id}))
            list1.append((0, 0, {'credit': trf_ml_vals.get('credit') - total_discount, 'name': trf_ml_vals.get('name'), 'debit': 0.0, 'partner_id': trf_ml_vals.get('partner_id'), 'date': trf_ml_vals.get('date'), 'account_id': trf_ml_vals.get('account_id')}))
        return list1

    @api.multi
    def action_cancel(self):
        res = super(AccountPaymentOrder, self).action_cancel()
        for order in self:
            order.mapped('payment_line_ids').mapped('payment_line_discount_ids').unlink()
        return res


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.multi
    def post(self):
        invoice = self._context.get('invoice', False)
        self._post_validate()
        for move in self:
            move.line_ids.create_analytic_lines()
            if move.name == '/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.move_name and invoice.move_name != '/':
                    new_name = invoice.move_name
                else:
                    if journal.sequence_id:
                        # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                        sequence = journal.sequence_id
                        if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                            if not journal.refund_sequence_id:
                                raise UserError(_('Please define a sequence for the credit notes'))
                            sequence = journal.refund_sequence_id

                        new_name = sequence.with_context(ir_sequence_date=move.date).next_by_id()
                    else:
                        raise UserError(_('Please define a sequence on the journal.'))

                if new_name and invoice and invoice.type != 'in_invoice':
                    move.name = new_name
                if new_name and invoice and invoice.type == 'in_invoice':
                    move.name = invoice.number or new_name
        return self.write({'state': 'posted'})


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    number = fields.Char(related='move_id.name', store=True, copy=False,
        readonly=True, states={'draft': [('readonly', False)]})
    subscription_id = fields.Many2one("sale.subscription", string="Subscription")
    job_number = fields.Char("Job Number")
    delivery_date = fields.Date("Lieferdatum")

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        if vals.get('number'):
            res.write({'number': vals.get('number')})
        return res

    @api.multi
    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        AccountMove = self.env['account.move']
        for invoice in self:
            if invoice.type == 'in_invoice':
                for line in invoice.invoice_line_ids:
                    if line.product_id.categ_id.property_cost_method == 'average' and line.product_id.categ_id.property_valuation == 'real_time':
                        account_moves = line.purchase_line_id.mapped('move_ids').mapped('account_move_ids')
                        sum_credit = sum(account_moves.mapped('line_ids').filtered(lambda r: r.account_id.id == r.product_id.categ_id.property_stock_valuation_account_id.id).mapped('credit'))
                        sum_debit = sum(account_moves.mapped('line_ids').filtered(lambda r: r.account_id.id == r.product_id.categ_id.property_stock_valuation_account_id.id).mapped('debit'))
                        difference = sum_credit - sum_debit + line.price_subtotal

                        #  If difference is positive
                        if difference > 0:
                            move_line_1 = {
                                'name': line.product_id.name + ': ' + 'Difference',
                                'credit': difference,
                                'account_id': line.product_id.categ_id.property_stock_account_input_categ_id.id,
                                'partner_id': line.invoice_id.partner_id.id,
                            }

                            move_line_2 = {
                                'name': line.product_id.name + ': ' + 'Difference',
                                'debit': difference,
                                'account_id': line.product_id.categ_id.property_stock_valuation_account_id.id,
                                'partner_id': line.invoice_id.partner_id.id,
                            }

                        #  If difference is negative
                        if difference < 0:
                            move_line_1 = {
                                'name': line.product_id.name + ': ' + 'Difference',
                                'credit': difference,
                                'account_id': line.product_id.categ_id.property_stock_valuation_account_id.id,
                                'partner_id': line.invoice_id.partner_id.id,
                            }

                            move_line_2 = {
                                'name': line.product_id.name + ': ' + 'Difference',
                                'debit': difference,
                                'account_id': line.product_id.categ_id.property_stock_account_output_categ_id.id,
                                'partner_id': line.invoice_id.partner_id.id,
                            }

                        date = invoice.date or invoice.date_invoice
                        move_vals = {
                            'ref': invoice.number,
                            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                            'journal_id': line.product_id.categ_id.property_stock_journal.id,
                            'date': date,
                            'narration': invoice.comment,
                        }
                        move = AccountMove.create(move_vals)
                        move.post()

                        new_price = ((line.purchase_line_id.price_unit * line.purchase_line_id.qty_received) + difference) / line.purchase_line_id.qty_received or 1.0
                        line.product_id.standard_price = new_price

        return res

    def _prepare_tax_line_vals_aok(self, line, tax):
        """ Prepare values to create an account.invoice.tax line

        The line parameter is an account.invoice.line, and the
        tax parameter is the output of account.tax.compute_all().
        """
        vals = {
            'invoice_id': self.id,
            'name': tax['name'],
            'tax_id': tax['id'],
            'amount': tax['amount'],
            'base': tax['base'],
            'manual': False,
            'sequence': tax['sequence'],
            'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
            'account_id': self.type in ('out_invoice', 'in_invoice') and (tax['account_id'] or line.account_id.id) or (tax['refund_account_id'] or line.account_id.id),
            'line_account_id': line.account_id.id,
        }

        # If the taxes generate moves on the same financial account as the invoice line,
        # propagate the analytic account from the invoice line to the tax line.
        # This is necessary in situations were (part of) the taxes cannot be reclaimed,
        # to ensure the tax move is allocated to the proper analytic account.
        if not vals.get('account_analytic_id') and line.account_analytic_id and vals['account_id'] == line.account_id.id:
            vals['account_analytic_id'] = line.account_analytic_id.id

        return vals

    @api.multi
    def get_taxes_values_aok(self, group_by='group_by_tax'):
        tax_grouped = {}
        lines = self.env['account.invoice.line']
        lines_by_account = self.invoice_line_ids.filtered(lambda l: l.account_id.user_type_id.name in ('Current Assets', 'Non-current Assets', 'Fixed Assets'))
        lines_by_tax = self.invoice_line_ids - lines_by_account
        if group_by == 'group_by_account':
            lines = lines_by_account
        elif group_by == 'group_by_tax':
            lines = lines_by_tax
        for line in lines:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals_aok(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key_aok(val, group_by=group_by)

                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
        return tax_grouped

    @api.multi
    def compute_taxes_aok(self, group_by='group_by_tax'):
        """Function used in other module to compute the taxes on a fresh invoice created (onchanges did not applied)"""
        account_invoice_tax = self.env['account.invoice.tax.aok']
        self.ensure_one()
        # Generate one tax line per tax, however many invoice lines it's applied to
        tax_grouped = self.get_taxes_values_aok(group_by=group_by)
        # Create new tax lines
        for tax in tax_grouped.values():
            account_invoice_tax |= account_invoice_tax.create(tax)
        return account_invoice_tax


class ProductCategory(models.Model):
    _inherit = "product.category"

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')


class ProductProduct(models.Model):
    _inherit = "product.product"

    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    job_number = fields.Char("Job Number")

    @api.multi
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['job_number'] = self.job_number
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()
        self.analytic_tag_ids = self.product_id.analytic_tag_ids
        return result

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res['account_analytic_id'] = self.product_id.categ_id.analytic_account_id.id
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(PurchaseOrderLine, self).onchange_product_id()
        self.analytic_tag_ids = self.product_id.analytic_tag_ids
        self.account_analytic_id = self.product_id.categ_id.analytic_account_id
        return result


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    is_encasing = fields.Boolean(related="product_id.product_tmpl_id.is_encasing", string="Is Encasing")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        result = super(AccountInvoiceLine, self)._onchange_product_id()
        self.analytic_tag_ids = self.product_id.analytic_tag_ids
        self.account_analytic_id = self.product_id.categ_id.analytic_account_id
        return result


class AccountInvoiceTaxAOK(models.Model):
    _name = "account.invoice.tax.aok"
    _description = "Invoice Tax AOK"
    _order = 'sequence'

    invoice_id = fields.Many2one('account.invoice', string='Invoice', ondelete='cascade', index=True)
    name = fields.Char(string='Tax Description', required=True)
    tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict')
    account_id = fields.Many2one('account.account', string='Tax Account', required=True, domain=[('deprecated', '=', False)])
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')
    amount = fields.Monetary()
    amount_rounding = fields.Monetary()
    amount_total = fields.Monetary(string="Amount", compute='_compute_amount_total')
    manual = fields.Boolean(default=True)
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of invoice tax.")
    company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True, readonly=True)
    base = fields.Monetary(string='Base', store=True)
    line_account_id = fields.Many2one('account.account', string='Tax Account', domain=[('deprecated', '=', False)])

    @api.depends('amount', 'amount_rounding')
    def _compute_amount_total(self):
        for tax_line in self:
            tax_line.amount_total = tax_line.amount + tax_line.amount_rounding


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    def _prepare_invoice_data(self):
        res = super(SaleSubscription, self)._prepare_invoice_data()
        res['subscription_id'] = self.id
        return res
