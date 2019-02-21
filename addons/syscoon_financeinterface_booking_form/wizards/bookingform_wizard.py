#See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from datetime import datetime


class syscoonFinanceinterfaceBookingform(models.TransientModel):
    _name = 'syscoon.financeinterface.bookingform.wizard'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    @api.multi
    @api.onchange('doctype')
    def _compute_move_type(self):
        context = dict(self._context or {})
        if context.get('doctype'):
            self.doctype = context['doctype']
        if self.doctype:
            dtype = self.doctype.upper()
            if dtype == 'A':
                self.move_type = 'customer_invoice'
            elif dtype == 'AG':
                self.move_type = 'customer_refund'
            elif dtype == 'E':
                self.move_type = 'supplier_invoice'
            elif dtype == 'EG':
                self.move_type = 'supplier_refund'
            elif dtype == 'B':
                self.move_type = 'move'
            else:
                raise UserError(_('Type can only be A, AG, E, EG or B'))

    @api.multi
    @api.onchange('account', 'counteraccount')
    def _compute_accounts(self):
        if self.account:
            partner = False
            account_id = self.account
            if not account_id:
                raise UserError(_('Account does not exist!'))
            else:
                if not self.partner_id:
                    partner = self.get_partner(account_id)
                self.account_id = account_id.id
                if partner:
                    self.partner_id = partner.id
        if self.counteraccount:
            partner = False
            counteraccount_id = self.counteraccount
            if not counteraccount_id:
                raise UserError(_('Counteraccount does not exist!'))
            else:
                if not self.partner_id:
                    partner = self.get_partner(counteraccount_id)
                self.counteraccount_id = counteraccount_id.id
                if partner:
                    self.partner_id = partner.id
        if 'analytic_id_obligatory' in self.env['account.account']._fields:
            if self.account_id.analytic_id_obligatory or self.counteraccount_id.analytic_id_obligatory:
                self.analytic_id_obligatory = True
            else:
                self.analytic_id_obligatory = False

    @api.multi
    @api.onchange('analytic_account')
    def _compute_analytic_id(self):
        if self.analytic_account:
            analytic_id = self.env['account.analytic.account'].search([('code', '=', self.analytic_account), ('company_id', '=', self.company_id.id)])
            if self.analytic_account and not analytic_id:
                raise UserError(_('Analytic Account does not exist!'))
            elif len(analytic_id) > 1:
                raise UserError(_('Analytic Account exists more than one time. Please delete one.'))
            else:
                self.analytic_id = analytic_id.id

    @api.multi
    @api.onchange('analytic_tag')
    def _compute_analytic_tag_id(self):
        if self.analytic_tag:
            analytic_tag_id = self.env['account.analytic.tag'].search([('name', 'like', self.analytic_tag)])
            if analytic_tag_id:
                self.analytic_tag_id = analytic_tag_id.id

    @api.multi
    @api.onchange('date')
    def _compute_move_date(self):
        if self.date:
            try:
                date_convert = datetime.strptime(self.date, '%d%m%y')
                self.move_date = date_convert.strftime('%Y-%m-%d')
            except:
                raise UserError(_('Date has not the correct format DDMMYY'))

    @api.multi
    @api.onchange('tax')
    def _compute_tax_id(self):
        if self.tax:
            tax_id = self.env['account.tax'].search([('bookingform_taxkey', '=', self.tax), ('price_include', '=', True), ('company_id', '=', self.company_id.id)])
            if not tax_id:
                tax_id = self.env['account.tax'].search([('buchungsschluessel', '=', int(self.tax)), ('price_include', '=', True), ('company_id', '=', self.company_id.id)])
            if not tax_id:
                tax_id = self.env['account.tax'].search([('buchungsschluessel', '=', int(self.tax)), ('amount_type', '=', 'group'), ('company_id', '=', self.company_id.id)])
            if not tax_id:
                raise UserError(_('There is not tax with option "Included in Price" for this taxkey!'))
            elif len(tax_id) > 1:
                raise UserError(_('There is more than one tax rate with this taxkey. Please manke sure that there is only one!'))
            else:
                self.tax_id = tax_id

    @api.multi
    @api.onchange('amount')
    def _compute_amount_float(self):
        if self.amount:
            new_amount = self.amount.replace(',', '.')
            self.amount_float = float(new_amount)

    @api.multi
    @api.depends('account_id', 'counteraccount_id')
    def _compute_partner_id(self):
        partner = False
        property_account = False
        if self.move_type == 'customer_invoice' or self.move_type == 'customer_refund':
            property_account = 'property_account_receivable_id'
            account_id = self.account_id
        if self.move_type == 'supplier_invoice' or self.move_type == 'supplier_refund':
            property_account = 'property_account_payable_id'
            account_id = self.counteraccount_id
        if property_account:
            partner = self.env['res.partner'].search([(property_account, 'in', [account_id.id]), ('company_id', '=', self.company_id.id)])
        if partner and partner[0]:
            self.partner_id = partner[0]
            return partner[0]

    @api.multi
    def get_partner(self, account_id):
        partner = False
        property_account = False
        if self.move_type == 'customer_invoice' or self.move_type == 'customer_refund':
            property_account = 'property_account_receivable_id'
        if self.move_type == 'supplier_invoice' or self.move_type == 'supplier_refund':
            property_account = 'property_account_payable_id'
        if property_account:
            partner = self.env['res.partner'].search([(property_account, 'in', [account_id.id]), ('company_id', '=', self.company_id.id)])
        if partner and partner[0]:
            return partner[0]

    @api.multi
    @api.depends('amount_float')
    def _compute_remaining_amount(self):
        remain = 0.0
        first_line = True
        for line in self.booking_line_ids:
            if line.company_id.id == self.env.user.company_id.id and line.user_id.id == self.env.user.id:
                if first_line:
                    remain += line.amount_float
                    first_line = False
                else:
                    remain -= line.amount_float
        self.remaining_amount = remain

    @api.multi
    def search_account_id(self, account):
        return self.env['account.account'].search([('code', '=', account), ('company_id', '=', self.company_id.id)])

    doctype = fields.Char('Doctype', size=2)
    ref = fields.Char('Reference', size=24)
    external_ref = fields.Char('External Reference', size=24)
    date = fields.Char('Date', size=6)
    amount = fields.Char('Amount')
    currency_id = fields.Many2one('res.currency', default=_default_currency, string='Company Currency')
    tax = fields.Char('Bookingkey', size=2)
    account = fields.Many2one('account.account', string='Account')
    counteraccount = fields.Many2one('account.account', string='Counteraccount')
    analytic_account = fields.Char('Analytic Account')
    analytic_tag = fields.Char('Analytic tags')
    text = fields.Char(string='Document Field')

    move_type = fields.Selection([
        ('customer_invoice', 'Customer Invoice'),
        ('customer_refund', 'Customer Refund'),
        ('supplier_invoice', 'Supplier Invoice'),
        ('supplier_refund', 'Supplier Refund'),
        ('move', 'Move')],
        compute='_compute_move_type', string='Move Type', readonly=1)
    move_date = fields.Date(string='Move Date', compute='_compute_move_date', readonly=1)
    account_id = fields.Many2one('account.account', compute='_compute_accounts', string='Account', readonly=1)
    counteraccount_id = fields.Many2one('account.account', compute='_compute_accounts', string='Counteraccount', readonly=1)
    partner_id = fields.Many2one('res.partner', compute='_compute_partner_id', string='Partner', readonly=1)
    tax_id = fields.Many2one('account.tax', compute='_compute_tax_id', string='Tax ID', readonly=1)
    analytic_id = fields.Many2one('account.analytic.account', compute='_compute_analytic_id', string='Analytic ID', readonly=1)
    analytic_tag_id = fields.Many2one('account.analytic.tag', compute='_compute_analytic_tag_id', string='Analytic Tag', readonly=1)
    amount_float = fields.Float(string='Amount', compute='_compute_amount_float', readonly=1)
    user_id = fields.Many2one('res.users', string='Accountant', default=lambda self: self.env.user, readonly=1)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id, string='Company', readonly=1)
    booking_line_ids = fields.Many2many('syscoon.financeinterface.bookingform.lines', 'syscoon_bookingform_lines_rel', 'wizard_id', 'line_ids', compute='_compute_booking_line_ids')
    remaining_amount = fields.Monetary('Remaining Amount', compute='_compute_remaining_amount')
    analytic_id_obligatory = fields.Boolean(compute='_compute_accounts', string='Kostenstelle ist Pflicht', readonly=1)

    @api.multi
    @api.depends('doctype')
    def _compute_booking_line_ids(self):
        lines = []
        line_ids = self.env['syscoon.financeinterface.bookingform.lines'].search([('user_id', '=', self.user_id.id)])
        for line in line_ids:
            lines.append(line.id)
        self.booking_line_ids = lines

    @api.multi
    def action_create(self, context=False, check=False, split=False):
        if not check:
            check = self.check_move(split)
        if check:
            check_string = '. '.join(check)
            raise UserError(_('The following fields are missing: %s. Please fill this fields to create a move.' % check_string))
        bookingform = self.env['syscoon.financeinterface.bookingform.lines']
        vals = self.create_line(split)
        line = bookingform.save_line(vals)
        if self.move_type != 'move':
            invoice = bookingform.create_invoice(line)
            return invoice
        else:
            move = bookingform.create_move(line)
            return move

    @api.multi
    def action_split(self, context=False, check=False, split=True):
        if not check:
            check = self.check_move(split)
        if check:
            check_string = '. '.join(check)
            raise UserError(_('The following fields are missing: %s. Please fill this fields to create a move.' % check_string))
        bookingform = self.env['syscoon.financeinterface.bookingform.lines']
        vals = self.create_line(split)
        line = bookingform.save_line(vals)
        context['doctype'] = self.doctype
        context['line'] = line.id
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
    def action_create_split(self):
        bookingform = self.env['syscoon.financeinterface.bookingform.lines']
        move = False
        for line in self.booking_line_ids:
            if line.move_type == 'move':
                move = True
        if move:
            invoice = bookingform.create_split_move(self.booking_line_ids.ids)
        else:
            invoice = bookingform.create_split_invoice(self.booking_line_ids.ids)
        return invoice

    @api.multi
    def check_move(self, split):
        error = []
        if self.analytic_id_obligatory and not self.analytic_id:
            error.append(_('Kost1'))
        if not split:
            if not self.move_type:
                error.append(_('DT'))
            if not self.move_date:
                error.append(_('DocDt'))
            if not self.ref and not self.move_type == 'customer_invoice':
                error.append(_('DocNo'))
            if not self.account_id:
                error.append(_('Account'))
            if not self.counteraccount_id:
                error.append(_('Counteract'))
            if not self.amount_float:
                error.append(_('Amount'))
            return error
        else:
            if not self.move_type:
                error.append(_('DT'))
            if not self.account_id and not self.counteraccount_id:
                error.append(_('Account or Counteraccount'))
            if not self.amount_float:
                error.append(_('Amount'))
            return error

    @api.multi
    def create_line(self, split):
        vals = {
            'doctype': self.doctype,
            'ref': self.ref,
            'external_ref': self.external_ref,
            'text': self.text,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'move_type': self.move_type,
            'move_date': self.move_date,
            'account_id': self.account_id.id,
            'counteraccount_id': self.counteraccount_id.id,
            'partner_id': self.partner_id.id,
            'tax_id': self.tax_id.id,
            'analytic_id': self.analytic_id.id,
            'analytic_tag_id': self.analytic_tag_id.id,
            'amount_float': self.amount_float,
            'user_id': self.user_id.id,
            'split': split,
        }
        return vals