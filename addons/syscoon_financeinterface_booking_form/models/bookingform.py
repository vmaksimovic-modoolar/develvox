#See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class syscoonFinanceinterfaceBookingformLines(models.Model):
    _name = 'syscoon.financeinterface.bookingform.lines'

    doctype = fields.Char('Doctype', size=2)
    ref = fields.Char('Reference', size=24)
    external_ref = fields.Char('External Reference', size=24)
    currency_id = fields.Many2one('res.currency', string='Company Currency')
    text = fields.Char(string='Document Field')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company')
    move_type = fields.Selection([
        ('customer_invoice', 'Customer Invoice'),
        ('customer_refund', 'Customer Refund'),
        ('supplier_invoice', 'Supplier Invoice'),
        ('supplier_refund', 'Supplier Refund'),
        ('move', 'Move')],
        string='Move Type')
    move_date = fields.Date(string='Move Date')
    account_id = fields.Many2one('account.account', string='Account')
    counteraccount_id = fields.Many2one('account.account', string='Counteraccount Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    tax_id = fields.Many2one('account.tax', string='Tax ID')
    analytic_id = fields.Many2one('account.analytic.account', string='Analytic ID')
    analytic_tag_id = fields.Many2one('account.analytic.tag', string='Analytic Tag')
    amount_float = fields.Float(string='Amount')
    user_id = fields.Many2one('res.users', string='Accountant')
    split = fields.Boolean('Split Move')

    @api.model
    def save_line(self, vals):
        line_id = self.create(vals)
        return line_id

    @api.multi
    def create_invoice(self, line):
        if line[0].move_type == 'customer_invoice':
            account_id = line[0].account_id
            inv_type = 'out_invoice'
        if line[0].move_type == 'customer_refund':
            account_id = line[0].counteraccount_id
            inv_type = 'out_refund'
        if line[0].move_type == 'customer_invoice' or line[0].move_type == 'customer_refund':
            journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
            payment_term = line[0].partner_id.property_payment_term_id
            reference = False
        if line[0].move_type == 'supplier_invoice':
            account_id = line[0].counteraccount_id
            inv_type = 'in_invoice'
        if line[0].move_type == 'supplier_refund':
            account_id = line[0].account_id
            inv_type = 'in_refund'
        if line[0].move_type == 'supplier_invoice' or line[0].move_type == 'supplier_refund':
            journal_id = self.env['account.journal'].search([('type', '=', 'purchase'), ('company_id', '=', line[0].company_id.id)])[0].id
            payment_term = line[0].partner_id.property_supplier_payment_term_id
            reference = line[0].external_ref
        invoice_vals = {
            'name': line[0].ref,
            'date_invoice': line[0].move_date,
            'number': line[0].ref if line[0].move_type == 'supplier_invoice' or line[0].move_type == 'supplier_refund' else '',
            'move_name': line[0].ref if line[0].move_type == 'supplier_invoice' or line[0].move_type == 'supplier_refund' else '',
            'origin': line[0].external_ref,
            'reference': reference,
            'type': inv_type,
            'account_id': account_id.id,
            'partner_id': line[0].partner_id.id or False,
            'journal_id': journal_id,
            'currency_id': line[0].currency_id.id,
            'payment_term_id': payment_term.id,
            'fiscal_position_id': line[0].partner_id.property_account_position_id.id or False,
            'company_id': line[0].company_id.id,
            'user_id': line[0].user_id and line[0].user_id.id,
        }
        invoice_id = self.env['account.invoice'].create(invoice_vals)
        invoice_line_ids = self.create_invoice_lines(invoice_id, line)
        invoice_id.compute_taxes()
        context = dict(self._context or {})
        context['doctype'] = line[0].doctype
        line.unlink()
        view = self.env.ref('syscoon_financeinterface_booking_form.syscoon_financeinterface_bookingform_wizard')
        return {
            'name': _('Bookingform'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'syscoon.financeinterface.bookingform.wizard',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def create_split_invoice(self, lines):
        inv_vals = False
        inv_lines = []
        for line in lines:
            if lines[0] == line:
                inv_vals = self.browse([line])
            else:
                inv_lines.append(line)
        if inv_vals.move_type == 'customer_invoice':
            inv_type = 'out_invoice'
        if inv_vals.move_type == 'customer_refund':
            inv_type = 'out_refund'
        if inv_vals.move_type == 'customer_invoice' or inv_vals.move_type == 'customer_refund':
            account_id = inv_vals.account_id
            journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
            payment_term = inv_vals.partner_id.property_payment_term_id
            reference = False
        if inv_vals.move_type == 'supplier_invoice':
            inv_type = 'in_invoice'
        if inv_vals.move_type == 'supplier_refund':
            inv_type = 'in_refund'
        if inv_vals.move_type == 'supplier_invoice' or inv_vals.move_type == 'supplier_refund':
            account_id = inv_vals.counteraccount_id
            journal_id = self.env['account.journal'].search([('type', '=', 'purchase')])[0].id
            payment_term = inv_vals.partner_id.property_supplier_payment_term_id
            reference = inv_vals.external_ref
        invoice_vals = {
            'name': inv_vals.ref,
            'date_invoice': inv_vals.move_date,
            'number': inv_vals.ref if inv_vals.move_type == 'supplier_invoice' else '',
            'move_name': inv_vals.ref if inv_vals.move_type == 'supplier_invoice' else '',
            'origin': inv_vals.external_ref,
            'reference': reference,
            'type': inv_type,
            'account_id': account_id.id,
            'partner_id': inv_vals.partner_id.id or False,
            'journal_id': journal_id,
            'currency_id': inv_vals.currency_id.id,
            'payment_term_id': payment_term.id,
            'fiscal_position_id': inv_vals.partner_id.property_account_position_id.id or False,
            'company_id': inv_vals.company_id.id,
            'user_id': inv_vals.user_id and inv_vals.user_id.id,
        }
        invoice_id = self.env['account.invoice'].create(invoice_vals)
        inv_line_ids = self.browse(inv_lines)
        invoice_line_ids = self.create_invoice_lines(invoice_id, inv_line_ids)
        invoice_id.compute_taxes()
        context = dict(self._context or {})
        view = self.env.ref('syscoon_financeinterface_booking_form.syscoon_financeinterface_bookingform_wizard')
        if invoice_id and invoice_line_ids:
            inv_vals.unlink()
            inv_line_ids.unlink()
        return {
            'name': _('Bookingform'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'syscoon.financeinterface.bookingform.wizard',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def create_split_move(self, lines):
        move_lines = []
        move = self.browse([lines[0]])
        for line in lines:
            line_vals = self.browse([line])
            journal_id = self.env['account.journal'].search([('type', '=', 'general')])[0]
            if line_vals.currency_id and line_vals.company_id and line_vals.currency_id != line_vals.company_id.currency_id:
                currency_id = self.currency_id.with_context(date=line_vals.date)
                amount_currency = line_vals.amount_float
                amount_total = currency_id.compute(line_vals.amount_float, self.company_id.currency_id)
            else:
                amount_currency = False
                amount_total = line_vals.amount_float
            name = []
            if line_vals.ref:
                name.append(line_vals.ref)
            if line_vals.external_ref:
                name.append(line_vals.external_ref)
            if line_vals.text:
                name.append(line_vals.text)
            if line_vals.tax_id:
                raise UserError(_('A move with Taxes must have the DT A or E at the moment.'))
            if line_vals.account_id:
                account = line_vals.account_id.id
            else:
                account = line_vals.counteraccount_id.id
            move_lines.append((0, 0, {
                'date_maturity': False,
                'partner_id': line_vals.partner_id and line_vals.partner_id.id or False,
                'name': ', '.join(name),
                'debit': line_vals.account_id and amount_total or False,
                'credit': line_vals.counteraccount_id and amount_total or False,
                'account_id': account,
                'analytic_account_id': line_vals.analytic_id.id,
                'analytic_tag_ids': [(4, line_vals.analytic_tag_id)],
            }))
        move_vals = {
            'ref': move.external_ref,
            'line_ids': move_lines,
            'journal_id': journal_id.id,
            'date': move.move_date,
            'narration': name,
        }
        self.env['account.move'].create(move_vals)
        lines_to_remove = self.browse(lines)
        lines_to_remove.unlink()
        context = dict(self._context or {})
        view = self.env.ref('syscoon_financeinterface_booking_form.syscoon_financeinterface_bookingform_wizard')
        return {
            'name': _('Bookingform'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'syscoon.financeinterface.bookingform.wizard',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def create_invoice_lines(self, invoice, lines):
        sequence = 10
        invoice_line_ids = []
        for line in lines:
            if line.move_type == 'customer_invoice' or line.move_type == 'supplier_refund':
                account_id = line.counteraccount_id
            if line.move_type == 'supplier_invoice' or line.move_type == 'customer_refund':
                account_id = line.account_id#
            if line.analytic_tag_id.id:
                tag_ids = [(6, 0, [line.analytic_tag_id.id])]
            else:
                tag_ids = False
            if line.tax_id:
                line_tax = [(6, 0, [line.tax_id.id])]
            else:
                line_tax = False
            line_vals = {
                'name': line.text or '/',
                'sequence': sequence,
                'origin': line.ref,
                'invoice_id': invoice.id,
                'account_id': account_id.id,
                'price_unit': line.amount_float,
                'quantity': 1.0,
                'product_id': False,
                'invoice_line_tax_ids': line_tax,
                'account_analytic_id': line.analytic_id.id,
                'analytic_tag_ids': tag_ids,
                'invoice_id': invoice.id,
            }
            line_id = self.env['account.invoice.line'].create(line_vals)
            invoice_line_ids.append(line_id.id)
            sequence += 10
        return invoice_line_ids

    @api.multi
    def create_move(self, line):
        journal_id = self.env['account.journal'].search([('type', '=', 'general')])[0]
        debit_analytic_account_id = False
        credit_analytic_account_id = False
        credit_tag_ids = False
        debit_tag_ids = False
        amount_currency = False
        if line[0].currency_id and line[0].company_id and line[0].currency_id != line[0].company_id.currency_id:
            currency_id = self.currency_id.with_context(date=line[0].date)
            amount_currency = line[0].amount_float
            amount_total = currency_id.compute(line[0].amount_float, self.company_id.currency_id)
        else:
            amount_total = line[0].amount_float
        name = []
        if line[0].ref:
            name.append(line[0].ref)
        if line[0].external_ref:
            name.append(line[0].external_ref)
        if line[0].text:
            name.append(line[0].text)
        if line[0].tax_id:
            raise UserError(_('A move with Taxes must have the DT A or E at the moment.'))
        if line[0].account_id.user_type_id.name == 'Income':
            credit_analytic_account_id = line[0].analytic_id and line[0].analytic_id.id or False
            if line[0].analytic_tag_id:
                credit_tag_ids = [(6, 0, [line[0].analytic_tag_id.id])]
        if line[0].account_id.user_type_id.name == 'Expenses':
            debit_analytic_account_id = line[0].analytic_id and line[0].analytic_id.id or False
            if line[0].analytic_tag_id:
                debit_tag_ids = [(6, 0, [line[0].analytic_tag_id.id])]
        debit_line = {
            'date_maturity': False,
            'partner_id': line[0].partner_id and line[0].partner_id.id or False,
            'name': ', '.join(name),
            'debit': amount_total,
            'credit': 0.0,
            'account_id': line.account_id.id,
            'analytic_account_id': debit_analytic_account_id,
            'analytic_tag_ids': debit_tag_ids,
        }
        credit_line = {
            'date_maturity': False,
            'partner_id': line[0].partner_id and line[0].partner_id.id or False,
            'name': ', '.join(name),
            'debit': 0.0,
            'credit': amount_total,
            'account_id': line.counteraccount_id.id,
            'analytic_account_id': credit_analytic_account_id,
            'analytic_tag_ids': credit_tag_ids,
        }
        move_vals = {
            'ref': line[0].external_ref,
            'line_ids': [(0, 0, debit_line), (0, 0, credit_line)],
            'journal_id': journal_id.id,
            'date': line[0].move_date,
            'narration': name,
        }
        self.env['account.move'].create(move_vals)
        line.unlink()
        context = dict(self._context or {})
        view = self.env.ref('syscoon_financeinterface_booking_form.syscoon_financeinterface_bookingform_wizard')
        return {
            'name': _('Bookingform'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'syscoon.financeinterface.bookingform.wizard',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def delete_line(self):
        context = dict(self._context or {})
        for line in self:
            line.unlink()
        view = self.env.ref('syscoon_financeinterface_booking_form.syscoon_financeinterface_bookingform_wizard')
        return {
            'name': _('Bookingform'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'syscoon.financeinterface.bookingform.wizard',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
