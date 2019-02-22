#See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import ustr
from odoo.exceptions import UserError

import base64
from io import StringIO
import csv
from decimal import Decimal
from datetime import datetime
import re


class ecofi(models.Model):
    """
    The class ecofi is the central object to generate a csv file for the selected moves that
    can be used to be imported in the different financial programms
    """
    _name = 'ecofi'
    _description = 'Ecoservice Financial Interface'
    _zahlungsbedingungen = []
    _order = 'name desc'

    name = fields.Char('Exportname', size=64, required=True, readonly=True)
    journale = fields.Char('Journals', size=128, readonly=True)
    zeitraum = fields.Char('Zeitraum', size=128, required=True, readonly=True)
    csv_file = fields.Binary('Export CSV', readonly=True)
    csv_file_fname = fields.Char('Stored Filename', size=256)
    ecofi_document_ids = fields.Many2many('ir.attachment', string='Documents', ondelete='cascade')
    account_moves = fields.One2many('account.move', 'vorlauf_id', 'Account Moves', readonly=True)
    account_invoices = fields.One2many('account.invoice', 'vorlauf_id', 'Account Invoices', readonly=True)
    export_mode_xml = fields.Boolean('Export Mode XML')
    partner_error_ids = fields.Many2many('res.partner', 'ecofi_res_partner_error_rel',
        'ecofi_id', 'res_partner_id', 'Partner Errors')
    move_error_ids = fields.Many2many('account.move', 'ecofi_eccount_move_error_rel',
        'ecofi_id', 'account_move_id', 'Move Errors')
    invoice_error_ids = fields.Many2many('account.invoice', string='Invoice Errors')
    note = fields.Text('Comment')

    def replace_non_ascii_characters(self, text, replacement=''):
        return re.sub(r'[^\x00-\x7F]+', replacement, text)

    @api.multi
    def copy(self, selfdefault=None):
        """ Prevent the copy of the object"""
        raise UserError(_('Warning!'), _('Exports cannot be duplicated.'))

    @api.multi
    def is_taxline(self, account_id):
        """Method to check if the selected account is a tax account"""
        tax = self.env['account.tax'].search([('account_id', '=', account_id), ('refund_account_id', '=', account_id)])
        if len(tax.ids) > 0:
            return True
        else:
            return False

    @api.multi
    def get_tax_account(self, line):
        """ Calculates and returns the account of tax that has to be considered for an account_move_line.
        :param line: account_move_line
        """
        linetax = self.get_line_tax(line)
        tax_account = False
        if linetax:
            total = line.credit - line.debit
            if total <= 0.00:
                tax_account = linetax.refund_account_id
            else:
                tax_account = linetax.account_id
        return tax_account

    @api.multi
    def get_tax(self, account_id):
        """Method to get the tax for the selected account
        :param account_id: Id of the account to analyse
        """
        tax = self.env['account.tax'].search([('account_id', '=', account_id), ('refund_account_id', '=', account_id)])
        taxids = map(lambda x: x[0], tax)
        return taxids

    @api.multi
    def get_line_tax(self, line):
        """returns the tax used in the line
        """
        linetax = False
        if line.tax_line_id:
            linetax = line.tax_line_id
        if line.ecofi_taxid:
            linetax = line.ecofi_taxid
        return linetax

    @api.multi
    def calculate_tax(self, line):
        """ Calculates and returns the amount of tax that has to be considered for an account_move_line. The calculation
        always uses the _compute method of the account.tax object wich returns the tax as if it was excluded.
        :param line: account_move_line
        """
        linetax = self.get_line_tax(line)
        texamount = 0
        if linetax:
            if 'waehrung' in self._context and self._context['waehrung']:
                amount = line.amount_currency
            else:
                amount = line.debit - line.credit
            return self.calc_tax(linetax, amount)
        else:
            if 'return_calc' in self._context and self._context['return_calc'] is True:
                return []
        return texamount

    @api.multi
    def calc_tax(self, tax_object, amount):
        texamount = 0
        if tax_object:
            taxes = tax_object.compute_all(amount)['taxes']
            if 'return_calc' in self._context and self._context['return_calc'] is True:
                return taxes
            for tex in taxes:
                if tax_object.price_include:
                    tex['amount'] = amount * (tax_object.amount / 100 + 1) - amount
                    tex['amount'] = tax_object.company_id.currency_id.round(tex['amount'])
                texamount += tex['amount']
        else:
            if 'return_calc' in self._context and self._context['return_calc'] is True:
                return []
        return texamount

    @api.multi
    def set_main_account(self, move):
        """ This methods sets the main account of the corresponding account_move
        :param move: account_move

        How the Mainaccount is calculated (tax lines are ignored):

        1. Analyse the number of debit and credit lines.
        a. 1 debit, n credit lines: Mainaccount is the debitline account
        b. m debit, 1 credit lines: Mainaccount is the creditline account
        c. 1 debit, 1 credit lines: Mainaccount is the firstline account

        If there are m debit and n debitlines:
        a. Test if there is an invoice connected to the move_id and test if the invoice
            account_id is in the move than this is the mainaccount
        """
        ecofikonto = False
        sollkonto = list()
        habenkonto = list()
        nullkonto = list()
        error = False
        ecofikonto_no_invoice = move.line_ids[0].account_id
        exchange_diffrence_account = False

        for line in move.line_ids:
            Umsatz = Decimal(str(line.debit)) - Decimal(str(line.credit))
            if Umsatz == 0 and line.amount_currency and line.account_id.user_type_id.type in ['payable', 'receivable']:
                exchange_diffrence_account = line.account_id
            if Umsatz < 0:
                habenkonto.append(line.account_id)
            elif Umsatz > 0:
                sollkonto.append(line.account_id)
            else:
                nullkonto.append(line.account_id)
        sollkonto = list(set(sollkonto))
        habenkonto = list(set(habenkonto))
        nullkonto = list(set(nullkonto))
        if len(sollkonto) == 1 and len(habenkonto) == 1:
            ecofikonto = move.line_ids[0].account_id
        elif len(sollkonto) == 1 and len(habenkonto) > 1:
            ecofikonto = sollkonto[0]
        elif len(sollkonto) > 1 and len(habenkonto) == 1:
            ecofikonto = habenkonto[0]
        elif len(sollkonto) > 1 and len(habenkonto) > 1:
            if len(sollkonto) > len(habenkonto):
                habennotax = list()
                for haben in habenkonto:
                    if not self.is_taxline(haben.id):
                        habennotax.append(haben)
                if len(habennotax) == 1:
                    ecofikonto = habennotax[0]
            elif len(sollkonto) < len(habenkonto):
                sollnotax = list()
                for soll in sollkonto:
                    if not self.is_taxline(soll.id):
                        sollnotax.append(soll)
                if len(sollnotax) == 1:
                    ecofikonto = sollnotax[0]
        if not ecofikonto and exchange_diffrence_account:
            ecofikonto = exchange_diffrence_account
        if not ecofikonto and move.journal_id.type == 'bank':
            ecofikonto = move.journal_id.default_debit_account_id
        if not ecofikonto:
            if 'invoice' in self._context:
                invoice = self._context['invoice']
            else:
                invoice = self.env['account.invoice'].search([('move_id', '=', move.id)])
            in_booking = False
            invoice_mainaccount = False
            if len(invoice) == 1:
                invoice_mainaccount = invoice.account_id
                for sk in sollkonto:
                    if sk == invoice_mainaccount:
                        in_booking = True
                        break
                for hk in habenkonto:
                    if hk == invoice_mainaccount:
                        in_booking = True
                        break
            if not in_booking and invoice:
                error = _(u"The main account of the booking could not be resolved, the move has %s credit- and %s debitlines!") % (len(sollkonto), len(habenkonto))
                error += "\n"
                ecofikonto = ecofikonto_no_invoice
            else:
                ecofikonto = invoice_mainaccount
        if ecofikonto:
            for l in move.line_ids:
                line = self.env['account.move.line'].browse(l.id)
                l.write({'ecofi_account_counterpart': ecofikonto.id})
        return error

    @api.multi
    def generate_csv_move_lines(self, move, buchungserror, errorcount, thislog, thismovename, exportmethod,
                          partnererror, buchungszeilencount, bookingdict):
        """Method to be implemented for each Interface, generates the corresponding csv entries for each move
        :param move: account_move
        :param buchungserror: list of the account_moves with errors
        :param errorcount: number of errors
        :param thislog: logstring wich contains error descriptions or infos
        :param thismovename: Internal name of the move (for error descriptions)
        :param exportmethod: brutto / netto
        :param partnererror: List of the partners with errors (eg. missing ustid)
        :param buchungszeilencount: total number of lines written
        :param bookingdict: Dictionary that contains generated Bookinglines and Headers
        """
        return buchungserror, errorcount, thislog, partnererror, buchungszeilencount, bookingdict

    @api.multi
    def generate_csv(self, ecofi_csv, bookingdict, log):
        """ Method to be implemented for each Interface, generates the corresponding csv entries for each move
        :param ecofi_csv: object for the csv file
        :param bookingdict: Dictionary that contains generated Bookinglines and Headers
        :param log: logstring wich contains error descriptions or infos
        """
        return ecofi_csv, log

    @api.multi
    def pre_export(self, account_move_ids):
        """ Method to call before the Import starts and the moves to export are going to be browsed
        :param ecofi_csv: object for the csv file
        :param bookingdict: Dictionary that contains generated Bookinglines and Headers
        :param log: logstring wich contains error descriptions or infos
        """
        return True

    @api.multi
    def ecofi_buchungen(self, journal_ids=[], vorlauf_id=False, date_from=False, date_to=False):
        """ Method that generates the csv export by the given parameters
        :param journal_ids: list of journalsIDS wich should be exported if the value is False all exportable journals will be exported
        :param vorlauf_id: id of the vorlauf if an existing export should be generated again
        :param date_from: date in wich moves should be exported
        :param date_to: date in wich moves should be exported
        .. seealso:: 
            :class:`ecoservice_financeinterface.wizard.export_ecofi_buchungsaetze.export_ecofi`
        """
        buf = StringIO()
        ecofi_csv = csv.writer(buf, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        partnererror = []
        buchungserror = []
        exportmethod = ''
        user = self.env['res.users'].browse(self._uid)
        if user.company_id.finance_interface:
            self = self.with_context(export_interface = user.company_id.finance_interface)
            try:
                exportmethod = user.company_id.exportmethod
            except:
                exportmethod = 'netto'
        else:
            self = self.with_context(export_interface='datev')
            exportmethod = 'netto'
        if len(journal_ids) == 0:
            if user.company_id.journal_ids:
                if len(user.company_id.journal_ids) == 0:
                    return (_("There is no journal for the ecofi_export configured!"), False, 'none', buchungserror, partnererror)
                journalname = ''
                for journal in user.company_id.journal_ids:
                    journalname += ustr(journal.name) + ','
                    journal_ids.append(journal.id)
                journalname = journalname[:-1]
            else:
                return (_("There is no journal for the ecofi_export configured!"), False, 'none', buchungserror, partnererror)
        else:
            journalname = ''
            for journal in self.env['account.journal'].browse(journal_ids):
                journalname += ustr(journal.name) + ','
            journalname = journalname[:-1]
        if vorlauf_id is not False:
            account_move_searchdomain = [('vorlauf_id', '=', vorlauf_id)]
        else:
            account_move_searchdomain = [('journal_id', 'in', journal_ids),
                                         ('state', '=', 'posted'),
                                         ('vorlauf_id', '=', False)
            ]
            if date_from and date_to:
                account_move_searchdomain.append(('date', '>=', date_from))
                account_move_searchdomain.append(('date', '<=', date_to))
        account_move_ids = self.env['account.move'].search(account_move_searchdomain)
        if len(account_move_ids) != 0:
            thislog = ""
            if vorlauf_id is False:
                vorlaufname = self.env['ir.sequence'].next_by_code('ecofi.vorlauf')
                zeitraum = ""
                if date_from and date_to:
                    try:
                        date_from = datetime.strptime(date_from, '%Y-%m-%d').strftime('%d.%m.%Y')
                        date_to = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d.%m.%Y')
                    except:
                        pass
                    zeitraum = str(date_from) + " - " + str(date_to)
                vorlauf_id = self.env['ecofi'].create({
                    'name': str(vorlaufname),
                    'zeitraum': zeitraum,
                    'journale': ustr(journalname)
                })
            else:
                vorlaufname = self.env['ecofi'].browse()[0]['name']
            thislog += _("This export is conducted under the Vorlaufname: %s") % (vorlaufname)
            thislog += "\n"
            thislog += "-----------------------------------------------------------------------------------\n"
            thislog += _("Start export")
            thislog += "\n"
            bookingdictcount = 0
            buchungszeilencount = 0
            errorcount = 0
            warncount = 0
            bookingdict = {}
            self.pre_export(account_move_ids)
            for move in account_move_ids:
                move.write({'vorlauf_id': vorlauf_id.id})
                thismovename = ustr(move.name) + ", " + ustr(move.ref) + ": "
                bookingdictcount += 1
                buchungserror, errorcount, thislog, partnererror, buchungszeilencount, bookingdict = self.generate_csv_move_lines(move, buchungserror, errorcount, thislog, thismovename, exportmethod, # pylint: disable-msg=C0301
                          partnererror, buchungszeilencount, bookingdict)
            ecofi_csv, thislog = self.generate_csv(ecofi_csv, bookingdict, thislog)
            out = base64.b64encode(buf.getvalue().encode('iso-8859-1', 'ignore'))
            thislog += _("Export finished")
            thislog += "\n"
            thislog += "-----------------------------------------------------------------------------------\n\n"
            thislog += _("Edited posting record : %s") % (bookingdictcount)
            thislog += "\n"
            thislog += _("Edited posting lines: %s") % (buchungszeilencount)
            thislog += "\n"
            thislog += _("Warnings: %s") % (warncount)
            thislog += "\n"
            thislog += _("Error: %s") % (errorcount)
            thislog += "\n"
            document = self.env['ir.attachment'].create({
                'name': '%s.csv' % (vorlaufname),
                'datas_fname': '%s.csv' % (vorlaufname),
                'res_model': 'ecofi',
                'res_id': vorlauf_id.id,
                'type': 'binary',
                'datas': out,
            })
            vorlauf_id.write({
                'note': thislog,
                'partner_error_ids': [(6, 0, list(set(partnererror)))],
                'move_error_ids': [(6, 0, list(set(buchungserror)))],
                'ecofi_document_ids': [(6, 0, document.ids)]
            })
        else:
            thislog = _("No posting records found")
            out = False
            vorlauf_id = False
        return vorlauf_id.id
