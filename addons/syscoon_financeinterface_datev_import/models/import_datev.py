#See LICENSE file for full copyright and licensing details.

import base64
from io import StringIO
import csv
import sys
import time
import traceback
import functools
from datetime import datetime
from decimal import Decimal

from odoo import fields, models, api, _
from odoo.tools import ustr
from odoo.exceptions import UserError
from babel._compat import iteritems


class ImportDatev(models.Model):
    """
    The class import.datev manages the reimport of datev buchungsstapel (account.moves)
    """
    _name = 'import.datev'
    _order = 'name desc'

    name = fields.Char('Name', readonly=True, default=lambda self: self.env['ir.sequence'].get('datev.import.sequence') or '-')
    description = fields.Char('Description', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    datev_ascii_file = fields.Binary('DATEV ASCII File')
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    one_move = fields.Boolean('In one move?')
    start_date = fields.Date('Start Date', required=True, default=fields.Date.today())
    end_date = fields.Date('End Date', required=True, default=fields.Date.today())
    log_line = fields.One2many('import.datev.log', 'parent_id', 'Log', ondelete='cascade')
    account_moves = fields.One2many('account.move', 'import_datev', 'Account Moves')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('error', 'Error'),
        ('imported', 'Imported'),
        ('booking_error', 'Booking Error'),
        ('booked', 'Booked')],
        'Status', index=True, readonly=True, default='draft')

    @api.multi
    def _lookup_erpvalue(self, field_config, value):
        """ Method to get the ERP ID for the Object and the given Value
        :param field_config: Dictionary of the field containing the erpobject and the erpfield
        :param value: Domain Search Value
        """
        genret = 0
        try:
            if field_config['erpfield'] == 'buchungsschluessel':
                if value and len(value) > 1:
                    if value[0] == '2':
                        genret = 1
                        value = value[1]
                    if value in ['SD', '40']:
                        return value
            args = 'domain' in field_config and field_config['domain'] or []
            args.append((field_config['erpfield'], '=', value))
            value = self.env[field_config['erpobject']].search(args)
            if len(value) == 1:
                return value[0], genret
            elif field_config['erpfield'] == 'buchungsschluessel':
                for val in value:
                    if not val.price_include:
                        return val, genret
            else:
                return False, genret
        except:
            return False, genret

    @api.multi
    def _convert_to_unicode_dict(self, importcsv, import_config, import_struct, errorlist, start_date, end_date):
        """ Method that imports the CSV File using the import_config and import struct rules. The CSV File is than converted
        to a unicode encoded Dictionary that can be used from the following functions
        :param importcsv: CSV File to be imported
        :param import_config: Import Config Dictionary
        :param import_struct: Import Structure Dictionary
        :param errorlist: Listobject that handles errors through the whole function
        """
        delimiter = import_config['delimiter']
        encoding = import_config['encoding']
        headerrow = import_config['headerrow']
        quotechar = import_config['quotechar']
        importcsv = importcsv.decode(encoding)
        importliste = csv.reader(StringIO(importcsv), delimiter=delimiter, quotechar=quotechar)
        date_year = datetime.strptime(str(start_date), '%Y-%m-%d').strftime('%Y')
        vorlauf = {'header': [],
                   'lines': {}
                   }
        for linecounter, line in enumerate(importliste, start=1):
            if linecounter == headerrow:
                for spalte in line:
                    try:
                        vorlauf['header'].append(spalte)
                    except:
                        errorlist.append({
                            'line': linecounter,
                            'name': _('Decoding ERROR'),
                            'beschreibung': _("Headerline %s could not be converted from format %s!") % (spalte, encoding)
                        })
            if linecounter > headerrow:
                thisline = []
                for spalte in line:
                    thisline.append(spalte)
                line = linecounter - 1
                vorlauf['lines'][line] = thisline
            linecounter += 1

        if len(vorlauf['header']) != len(list(set(vorlauf['header']))):
            errorlist.append({
                'line': 2,
                'name': _("Attributename twice in Header"),
                'beschreibung': _("The Attributename must be unique in the header")
            })

        for key in import_struct.keys():
            headercount = 0
            for header in vorlauf['header']:
                if header == import_struct[key]['csv_name']:
                    import_struct[key]['csv_row'] = headercount
                headercount += 1
        for key in import_struct.keys():
            if import_struct[key]['csv_row'] is False:
                errorlist.append({
                    'line': headerrow,
                    'name': _("Attribute not found"),
                    'beschreibung': _("Attribute %s could not be found") % (import_struct[key]['csv_name'])
                })
        linecounter = headerrow
        data_list = []
        for num, line in iteritems(vorlauf['lines']):
            skip = False
            for key in import_struct.keys():
                if 'skipon' in import_struct[key]:#
                    if import_struct[key]['skipon']: 
                        if line[import_struct[key]['csv_row']] in import_struct[key]['skipon']:
                            skip = True
            if skip:
                thisvalue = {}
                thisvalue['skip'] = True
                data_list.append(thisvalue)
                continue
            linecounter += 1
            spaltenvalues = {}

            for key in import_struct.keys():
                thisvalue = False
                genret = False
                if line[import_struct[key]['csv_row']] == 'False':
                    if 'default' in import_struct[key]:
                        line[import_struct[key]['csv_row']] = import_struct[key]['default']
                if line[import_struct[key]['csv_row']] == '' and import_struct[key]['required'] is False:
                    spaltenvalues[key] = thisvalue
                    continue
                if line[import_struct[key]['csv_row']] == '' and import_struct[key]['required'] is True:
                    errorlist.append({
                        'line': linecounter,
                        'name': _("Attribute is required"),
                        'beschreibung': _("Attribute %s in line %s is required but not filled") % (import_struct[key]['csv_name'], linecounter)
                    })
                    spaltenvalues[key] = thisvalue
                    continue
                try:
                    if import_struct[key]['type'] == 'string':
                        thisvalue = str(line[import_struct[key]['csv_row']])
                        if 'zerofill' in import_struct[key]:
                            thisvalue = thisvalue.zfill(import_struct[key]['zerofill'])
                    elif import_struct[key]['type'] == 'integer':
                        thisvalue = int(line[import_struct[key]['csv_row']])
                    elif import_struct[key]['type'] == 'decimal':
                        decimalvalue = line[import_struct[key]['csv_row']]
                        if decimalvalue and import_struct[key]['decimalformat'][0]:
                            decimalvalue = decimalvalue.replace(import_struct[key]['decimalformat'][0], import_struct[key]['decimalformat'][1])
                            thisvalue = float(decimalvalue)
                        elif not import_struct[key]['required']:
                            thisvalue = False
                        else:
                            thisvalue
                    elif import_struct[key]['type'] == 'date':
                        if import_struct[key]['dateformat'] == '%d%m':
                            dateformat = '%Y%d%m'
                            line[import_struct[key]['csv_row']] = date_year + line[import_struct[key]['csv_row']].zfill(import_struct[key]['zerofill'])
                        else:
                            dateformat = import_struct[key]['dateformat']
                        thisvalue = datetime.strptime(str(line[import_struct[key]['csv_row']]), dateformat)

                        if datetime.strptime(str(start_date) + " 00:00", "%Y-%m-%d %H:%M") > thisvalue or datetime.strptime(str(end_date) + " 23:59", "%Y-%m-%d %H:%M") < thisvalue:
                            errorlist.append({
                                'line': linecounter,
                                'name': _("Date is not in the selected date range!"),
                                'beschreibung': _("Date %s in line %s is not in the selected date range!") % (thisvalue.strftime('%d.%m.%Y'), import_struct[key]['csv_name'])
                            })
                    else:
                        errorlist.append({
                            'line': linecounter,
                            'name': _("Attributetype could not be resolved"),
                            'beschreibung': _("Attributetype %s could not be resolved!") % (import_struct[key]['type'])
                        })
                    if 'convert_method' in import_struct[key]:
                        thisvalue = import_struct[key]['convert_method'](thisvalue)

                except:
                    errorlist.append({
                        'line': linecounter,
                        'name': _("Attribute could not be converted!"),
                        'beschreibung': _("Attribute %s in line %s could not be converted to type: %s!") % (import_struct[key]['csv_name'], linecounter, import_struct[key]['type'])
                    })
                if thisvalue == 'False':
                    thisvalue = False
                if thisvalue is not False:
                    if 'erplookup' in import_struct[key] and import_struct[key]['erplookup']:
                        newvalue, genret = self._lookup_erpvalue(import_struct[key], thisvalue)
                        if newvalue is False:
                            errorlist.append({
                                'line': linecounter,
                                'name': _("ERP object not found"),
                                'beschreibung': _("The ERP object for Value %s (%s) in line %s could not be resolved!") % (thisvalue, import_struct[key]['csv_name'], linecounter)
                            })
                            thisvalue = newvalue
                        elif newvalue is True:
                            thisvalue = False
                        else:
                            thisvalue = newvalue
                spaltenvalues[key] = thisvalue
                if genret:
                    spaltenvalues['generalumkehr'] = genret
            data_list.append(spaltenvalues)
        return data_list, errorlist

    @api.multi
    def unlink(self):
        """ Import can only be unlinked if State is draft
        """
        for thisimport in self:
            if thisimport.state not in ('error', 'draft'):
                raise UserError(_('Warning! Import can only be deleted in state draft!'))
        return super(ImportDatev, self).unlink()

    @api.multi
    def reset_import(self):
        """ Method to reset the import
        #. Unreconcile all reconciled imported Moves
        #. Cancel all imported moves not in state draft
        #. Delete all imported moves
        #. Delete all Importloglines
        #. Set Import state to draft 
        """
        for datev_import in self:
            if datev_import.account_moves:
                try:
                    self.with_context(delete_none = True)
                    for move in datev_import.account_moves:
                        for line in move.line_ids:
                            if line.reconciled:
                                ### must be different
                                line.remove_move_reconcile()
                                #self.env['account.move.line'].remove_move_reconcile(move_ids=[line.id])
                                ###
                        if move.state != 'draft':
                            move.button_cancel()
                        move.unlink()
                    for log in datev_import.log_line:
                        log.unlink()
                    self.write({'state': 'draft'})
                except:
                    tb_s = reduce(lambda x, y: x + y, traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))  # @UndefinedVariable # pylint: disable-msg=C0301
                    self.env['import.datev.log'].create({
                        'parent_id': datev_import.id,
                        'name': _("%s could not be booked, ERP ERROR: %s") % (ustr(move.name), tb_s),
                        'state': 'error',
                    })
            else:
                raise UserError('No Moves to reset!')
            error = True
        return True

    @api.multi
    def search_partner(self, konto, gegenkonto):
        """ Get the partner for the specified account
        :param konto: ID of the account
        """
        partner_konto = self.env['ir.property'].search([['value_reference', '=', 'account.account,' + str(konto)]])
        partner_gegenkonto = self.env['ir.property'].search([['value_reference', '=', 'account.account,' + str(gegenkonto)]])
        if partner_konto and partner_gegenkonto:
            if partner_konto == partner_gegenkonto:
                return partner_konto
            if partner_konto and not partner_gegenkonto:
                return partner_konto
            if partner_gegenkonto and not partner_konto:
                return partner_gegenkonto
            if partner_konto and partner_gegenkonto:
                return False

    @api.multi
    def get_partner(self, line):
        """ Search Partner for the line
        :param line: Move Line
        """
        partner_id = False
        ppty = False
        if line['konto'].user_type_id.type in ('receivable', 'payable'):
            ppty = 'account.account,%s' % line['konto'].id
        elif line['gegenkonto'].user_type_id.type in ('receivable', 'payable'):
            ppty = 'account.account,%s' % line['gegenkonto'].id
        if ppty:
            ir_property = self.env['ir.property'].search([('value_reference', '=', ppty)])
            for ids in ir_property:
                if ids and ids.res_id:
                    partner_id = ids.res_id.split(',')
        if partner_id:
            return partner_id[1]
        else:
            return False

    @api.multi
    def get_import_defaults(self, datev_import):
        """ Default import_config and import_struct
        """
        config = self.env['import.datev.config'].search([('company_id', '=', self.company_id.id)])
        if not config:
            raise UserError(_('There is no config for this company'))

        import_config = {}
        import_config['delimiter'] = str(config.delimiter)
        import_config['encoding'] = config.encoding
        import_config['quotechar'] = str(config.quotechar)
        import_config['headerrow'] = config.headerrow
        import_config['journal_id'] = datev_import.journal_id.id
        import_config['company_id'] = datev_import.company_id.id
        import_config['company_currency_id'] = datev_import.company_id.currency_id.id
        import_config['skonto_account'] = config.skonto_account
        import_config['skonto_account_expenses'] = config.skonto_account_expenses
        import_config['date'] = datev_import.start_date
        import_config['ref'] = config.ref
        import_config['post'] = config.post_moves
        import_config['auto_reconcile'] = config.auto_reconcile
        import_config['payment_difference_handling'] = config.payment_difference_handling
        import_config['payable_reconcile_field'] = config.payable_reconcile_field
        import_config['receivable_reconcile_field'] = config.receivable_reconcile_field
        import_config['skonto_account_automatic'] = config.skonto_account_automatic

        import_struct = {}
        for struct in config.import_config_row_ids:
            import_struct[struct.name] = {
                'csv_name': struct.csv_name,
                'csv_row': struct.csv_row,
                'type': struct.type,
                'dateformat': struct.dateformat,
                'required': struct.required,
                'erplookup': struct.erplookup,
                'erpobject': struct.erpobject,
                'erpfield': struct.erpfield,
                'domain': struct.domain,
                'zerofill': struct.zerofill,
                'decimalformat': (struct.decimalformat, struct.decimalreplacement),
                'skipon': struct.skipon and struct.skipon.split() or False,
                'default': struct.default,
            }

        return import_config, import_struct

    @api.multi
    def create_account_move(self, datev_import, import_config, line, linecounter, move_id=False, manual=False):
        """ Create the move for the import line
        
        :param datev_import: Datev Import
        :param import_config: Import Config
        :param line: Move Line
        :param linecounter: Counter of the move line
        """
        ref = []
        partner_id = self.get_partner(line)
        if move_id is False:
            if 'buchungstext' in line and line['buchungstext']:
                ref.append(line['buchungstext'])
            if 'beleg1' in line and line['beleg1']:
                ref.append(line['beleg1'])
            if 'beleg2' in line and line['beleg2']:
                ref.append(line['beleg2'])
            if ref:
                ref = ', '.join(ref)
            else:
                ref = ''
            move = {
                'import_datev': datev_import.id,
                'name': line['name'],
                'ref': ref,
                'journal_id': datev_import.journal_id.id,
                'company_id': import_config['company_id'],
                'date': line['belegdatum'].strftime('%Y-%m-%d'),
                'ecofi_manual': manual,
                'partner_id': partner_id,
            }
            move_id = self.env['account.move'].create(move)

        return move_id, partner_id

    @api.multi
    def create_move_line_dict(self, move, import_config):
        move_line_dict = {
            'company_id': import_config['company_id'],
            'partner_id': move['partner_id'],
            'credit': str(move['credit']),
            'debit': str(move['debit']),
            'journal_id': import_config['journal_id'] and import_config['journal_id'] or False,
            'account_id': move['account_id'],
            'date': move['date'],
            'name': move['name'],
            'move_id': move['move_id'],
            'ecofi_taxid': 'ecofi_taxid' in move and move['ecofi_taxid'] or False,
            'amount_currency': 'amount_currency' in move and move['amount_currency'] or False,
            'currency_id': 'currency_id' in move and move['currency_id'] or False,
            'date_maturity': 'date_maturity' in move and move['date_maturity'] or False,
            'analytic_account_id': False,
            'quantity': 1.0,
            'ecofi_bu': 'ecofi_bu' in move and move['ecofi_bu'] or '',
            'product_id': False,
        }
        return move_line_dict

    @api.multi
    def compute_currency(self, move_line, line, import_config):
        cur_obj = self.env['res.currency']
        if line['wkz'] != import_config['company_currency_id']:
            self.with_context(date = line['belegdatum'].strftime('%Y-%m-%d') or time.strftime('%Y-%m-%d'))
            move_line['currency_id'] = line['wkz'].id
            move_line['amount_currency'] = move_line['debit'] - move_line['credit']
            move_line['debit'] = cur_obj.compute(float(move_line['debit']), line['wkz'])
            move_line['credit'] = cur_obj.compute(float(move_line['credit']), line['wkz'])
        return move_line

    @api.multi
    def create_main_lines(self, line, thismove, partner_id, import_config, move_lines=None):
        """ Create the Main booking Lines
        :param line: Import Line
        :param thismove: MoveID
        :param move_lines: MoveLines
        """
        taxmoves = []
        date_maturity = False
        if move_lines is None:
            move_lines = []
        debit, credit = self.create_debit_credit(line['umsatz'], line['sollhaben'])
        if 'faelligkeit' in line and line['faelligkeit']:
            date_maturity = line['faelligkeit'].strftime('%Y-%m-%d') or False
        if 'generalumkehr' in line:
            if debit:
                debit = -debit
            if credit:
                credit = -credit
        gegenmove = {
            'credit': debit,
            'debit': credit,
            'account_id': line['gegenkonto'].id,
            'date': line['belegdatum'].strftime('%Y-%m-%d'),
            'move_id': thismove.id,
            'name': 'Gegenbuchung',
            'partner_id': partner_id,
            'date_maturity': date_maturity,
        }
        mainmove = {
            'credit': credit,
            'debit': debit,
            'account_id': line['konto'].id,
            'date': line['belegdatum'].strftime('%Y-%m-%d'),
            'move_id': thismove.id,
            'name': 'Buchung',
            'partner_id': partner_id,
            'date_maturity': date_maturity,
        }
        skontomove, mainmove = self.create_skonto_move(line, mainmove, partner_id, thismove, import_config)
        if not 'buschluessel' in line or line['buschluessel'] == False:
            if line['konto'].automatic:
                line['buschluessel'] = line['konto'].datev_steuer[0] or False
            elif line['gegenkonto'].automatic:
                line['buschluessel'] = line['gegenkonto'].datev_steuer[0] or False
            else:
                line['buschluessel'] = False
        if 'buschluessel' in line and line['buschluessel']:
            mainmove, gegenmove, taxmoves = self.create_tax_line(mainmove, gegenmove, import_config, line)
        gegenmove = self.compute_currency(gegenmove, line, import_config)
        mainmove = self.compute_currency(mainmove, line, import_config)
        if taxmoves: 
            for taxmove in taxmoves:
                move_lines.append(self.compute_currency(taxmove, line, import_config))
        move_lines.append(self.create_move_line_dict(gegenmove, import_config))
        move_lines.append(self.create_move_line_dict(mainmove, import_config))
        if skontomove:
            for key in skontomove.keys():
                if skontomove[key]:
                    skvalue, taxvalue = self.create_skonto_tax_line(mainmove, line, skontomove[key], import_config)
                    move_lines.append(self.create_move_line_dict(skvalue, import_config))
                    taxmoves.append(self.create_move_line_dict(taxvalue, import_config))
        return move_lines

    @api.multi
    def create_debit_credit(self, amount, sollhaben):
        if sollhaben.upper() == 'S':
            debit = amount
            credit = 0.0
        else:
            debit = 0.0
            credit = amount
        return debit, credit

    @api.multi
    def create_skonto_move(self, line, mainmove, partner_id, thismove, import_config):
        if 'skonto' in line and line['skonto']:
            if mainmove['credit']:
                mainmove['credit'] += line['skonto']
            else:
                mainmove['debit'] += line['skonto']
            skontomove = {}
            if import_config['skonto_account_automatic']:
                skontoaccount = invoice_id = False
                if line['konto'].user_type_id.type == 'payable':
                    inv_var = ['reference', line[import_config['payable_reconcile_field'].name]]
                elif line['konto'].user_type_id.type == 'receivable':
                    inv_var = ['number', line[import_config['receivable_reconcile_field'].name]]
                elif line['gegenkonto'].user_type_id.type == 'payable':
                    inv_var = ['reference', line[import_config['payable_reconcile_field'].name]]
                elif line['gegenkonto'].user_type_id.type == 'receivable':
                    inv_var = ['number', line[import_config['receivable_reconcile_field'].name]]
                else:
                    inv_var = False
                if inv_var:
                    invoice_id = self.env['account.invoice'].search([(inv_var[0], '=', inv_var[1])])[0]
                if invoice_id:
                    if invoice_id.type == 'out_invoice':
                        account_id = import_config['skonto_account'].id
                    else:
                        account_id = import_config['skonto_account_expenses'].id
                    lines = {}
                    total_amount = 0.0
                    for invl in invoice_id.invoice_line_ids:
                        total_amount += invl.price_subtotal
                        if invl.account_id not in lines:
                            lines[invl.account_id] = [invl.price_subtotal, invl.invoice_line_tax_ids]
                        else:
                            lines[invl.account_id][0] += invl.price_subtotal
                            if invl.invoice_line_tax_ids not in lines[invl.account_id][1]:
                                lines[invl.account][1].append(invl.linvoice_line_tax_ids)
                if lines:
                    count = 0
                    for key, values in lines.items():
                        amount = (values[0] / total_amount) * line['skonto']
                        if mainmove['credit']:
                            debit = amount
                            credit = 0.0
                        else:
                            debit = 0.0
                            credit = amount
                        if values[1][0].datev_skonto.id:
                            if 'generalumkehr' in line:
                                if debit:
                                    debit = -debit
                                if credit:
                                    credit = -credit
                            skontomove[count] = {
                                'credit': credit,
                                'debit': debit,
                                'account_id': values[1][0].datev_skonto.id,
                                'date': line['belegdatum'].strftime('%Y-%m-%d'),
                                'move_id': thismove.id,
                                'ecofi_taxid': values[1][0].id,
                                'name': 'Skontobuchung',
                                'partner_id': partner_id,
                            }
                        else:
                            if invoice_id.type == 'out_invoice':
                                account_id = import_config['skonto_account'].id
                            else:
                                account_id = import_config['skonto_account_expenses'].id
                            skontomove[count] = {
                                'credit': credit,
                                'debit': debit,
                                'account_id': account_id,
                                'date': line['belegdatum'].strftime('%Y-%m-%d'),
                                'move_id': thismove.id,
                                'name': 'Skontobuchung',
                                'partner_id': partner_id,
                                'ecofi_taxid': values[1][0].id,
                            }
                        count += 1
            else:
                if mainmove['credit']:
                    debit = line['skonto']
                    credit = 0.0
                else:
                    debit = 0.0
                    credit = line['skonto']
                skontomove[0] = {
                    'credit': credit,
                    'debit': debit,
                    'account_id': import_config['skonto_account'].id,
                    'date': line['belegdatum'].strftime('%Y-%m-%d'),
                    'move_id': thismove.id,
                    'name': 'Skontobuchung',
                    'partner_id': partner_id,
                    'ecofi_taxid': import_config['skonto_account'].datev_steuer[0].id or False,
                }
        else:
            skontomove = False
        return skontomove, mainmove

    @api.multi
    def create_skonto_tax_line(self, mainmove, line, skvalue, import_config):
        tax_debit = tax_credit = 0.0
        tax_id = self.env['account.tax'].browse(skvalue['ecofi_taxid'])
        total = float(skvalue['debit'] + skvalue['credit'])
        taxes = tax_id.compute_all_datev_import(total)['taxes'][0]
        if skvalue['credit']:
            tax_credit = taxes['amount']
            skvalue['credit'] -= taxes['amount']
        else:
            tax_debit = taxes['amount']
            skvalue['debit'] -= taxes['amount']
        data = {
            'move_id': mainmove['move_id'],
            'name': ustr(mainmove['name'] or '') + ' ' + ustr(taxes['name'] or ''),
            'date': mainmove['date'],
            'partner_id': mainmove['partner_id'] and mainmove['partner_id'] or False,
            'ref': import_config['ref'] or 'Skonto Steuerbuchung' or False,
            'tax_line_id': skvalue['ecofi_taxid'],
            'account_id': taxes['account_id'],
            'credit': tax_credit,
            'debit': tax_debit,
        }
        skvalue.pop('tax_line_id', False)
        return skvalue, data

    @api.multi
    def create_tax_line(self, mainmove, gegenmove, import_config, line):
        tax_debit = tax_credit = 0.0
        if isinstance(line['buschluessel'], str) and line['buschluessel'] in ['40', 'SD']:
            mainmove['ecofi_bu'] = line['buschluessel']
            mainmove['ecofi_taxid'] = line['konto_object'].datev_steuer[0].id and line['konto_object'].datev_steuer[0].id or False
            return mainmove, gegenmove, []

        

        ref = []
        if 'buchungstext' in line and line['buchungstext']:
            ref.append(line['buchungstext'])
        if 'beleg1' in line and line['beleg1']:
            ref.append(line['beleg1'])
        if 'beleg2' in line and line['beleg2']:
            ref.append(line['beleg2'])
        if ref:
            ref = ', '.join(ref)

        tax_id = line['buschluessel']
        total = float(mainmove['debit'] + mainmove['credit'])
        taxes = tax_id.compute_all_datev_import(total)['taxes'][0]
        if mainmove['credit']:
            tax_debit = taxes['amount']
        else:
            tax_credit = taxes['amount']
        data = {
            'move_id': mainmove['move_id'],
            'name': ustr(mainmove['name'] or '') + ' ' + ustr(taxes['name'] or ''),
            'date': mainmove['date'],
            'partner_id': mainmove['partner_id'] and mainmove['partner_id'] or False,
            'ref': import_config['ref'] or 'Steuerbuchung' or False,
            'tax_id': tax_id.id or False,
            'ref': import_config['ref'] or ref or False,
            'tax_line_id': tax_id.id or False,
            'account_id': taxes['account_id'],
            'credit': tax_credit,
            'debit': tax_debit,
        }
        if mainmove['debit'] and data['credit']:
            gegenmove['debit'] -= float(str(data['debit']))
            gegenmove['credit'] -= float(str(data['credit']))
            gegenmove['ecofi_taxid'] = line['buschluessel'].id
        elif mainmove['debit'] and data['debit']:
            mainmove['debit'] -= float(str(data['debit']))
            mainmove['credit'] -= float(str(data['credit']))
            mainmove['ecofi_taxid'] = line['buschluessel'].id
        elif mainmove['credit'] and data['credit']:
            mainmove['debit'] -= float(str(data['debit']))
            mainmove['credit'] -= float(str(data['credit']))
            mainmove['ecofi_taxid'] = line['buschluessel'].id
        elif mainmove['credit'] and data['debit']:
            gegenmove['debit'] -= float(str(data['debit']))
            gegenmove['credit'] -= float(str(data['credit']))
            gegenmove['ecofi_taxid'] = line['buschluessel'].id
        return mainmove, gegenmove, [data]

    @api.multi
    def do_import(self, import_config={}, import_struct={}):
        """Method to Start the Import of the Datev ASCII File Containing the Datev Moves
        :param import_config: Dictionary Containing the Config parameterws
        :param import_struct: Dictionary Containing the Structure of the ASCII FIle
        """
        errorlist = []
        move_ids = []
        for datev_import in self:
            import_config, import_struct = self.get_import_defaults(datev_import)
            if datev_import.account_moves:
                self.reset_import()
            self.env['import.datev.log'].create({
                'parent_id': datev_import.id,
                'name': _("Import started!"),
                'state': 'info',
            })
            if datev_import.datev_ascii_file:
                importcsv = base64.decodestring(datev_import.datev_ascii_file)
                vorlauf, errorlist = self._convert_to_unicode_dict(
                    importcsv,
                    import_config,
                    import_struct,
                    errorlist,
                    datev_import.start_date,
                    datev_import.end_date
                )
                if len(errorlist) == 0:
                    linecounter = 0
                    thismove = False
                    for line in vorlauf:
                        linecounter += 1
                        if 'skip' in line:
                            self.env['import.datev.log'].create({
                                'parent_id': datev_import.id,
                                'name': _("Line: %s has been skipped") % (ustr(linecounter + import_config['headerrow'])),
                                'state': 'standard',
                            })
                            continue
                        if datev_import.one_move is False:
                            thismove = False
                            manual = False
                        else:
                            manual = True
                        next_seq = datev_import.journal_id.sequence_id.next_by_id()
                        line['name'] = next_seq
                        if not line.get('wkz', False):
                            currency_id = datev_import.journal_id.currency_id or datev_import.company_id.currency_id
                            line['wkz'] = currency_id
                        thismove, partner_id = self.create_account_move(datev_import,
                                                                        import_config, line, linecounter, move_id=thismove, manual=manual)
                        move_lines = self.create_main_lines(line, thismove, partner_id, import_config)
                        move_line_ids = []
                        for move in move_lines:
                            self.with_context(check_move_validity = False)
                            move['credit'] = float(move['credit'])
                            move['debit'] = float(move['debit'])
                            move_line_ids.append(self.env['account.move.line'].create(move))
                            self.with_context(check_move_validity = True)
                        self.env['import.datev.log'].create({
                            'parent_id': datev_import.id,
                            'name': _("Line: %s has been imported") % (ustr(linecounter + import_config['headerrow'])),
                            'state': 'standard',
                        })
                        if import_config['post']:
                            thismove.post()
                        if import_config['auto_reconcile'] and partner_id and line['beleg1']:
                            self.auto_reconcile(move_line_ids, line, import_config)
                    if len(errorlist) != 0:
                        for line in errorlist:
                            self.env['import.datev.log'].create({
                                'parent_id': datev_import.id,
                                'name': _("%s line: %s") % (ustr(line['beschreibung']), ustr(line['line'])),
                                'state': 'error',
                            })
                        self.write({'state': 'error'})
                    else:
                        self.write({'state': 'imported'})
                else:
                    for line in errorlist:
                        self.env['import.datev.log'].create({
                            'parent_id': datev_import.id,
                            'name': _("%s Line: %s") % (ustr(line['beschreibung']), ustr(line['line'])),
                            'state': 'error',
                        })
                    self.write({'state': 'error'})
        return True

    @api.multi
    def auto_reconcile(self, move_line_ids, line, import_config):
        line_ids = []
        inv_var = False
        for ml in move_line_ids:
            if ml.account_id.user_type_id.type == 'payable':
                inv_var = ['reference', line[import_config['payable_reconcile_field'].name]]
                line_ids.append(ml.id)
            elif ml.account_id.user_type_id.type == 'receivable':
                inv_var = ['number', line[import_config['receivable_reconcile_field'].name]]
                line_ids.append(ml.id)
        if inv_var:
            invoice_ids = self.env['account.invoice'].search([(inv_var[0], '=', inv_var[1])])
        for invoice in invoice_ids:
            for ml in invoice.move_id.line_ids:
                if ml.account_id.user_type_id.type in ('receivable', 'payable'):
                    line_ids.append(ml.id)
        if len(line_ids) > 1:
            currency = False
            move_lines = self.env['account.move.line'].browse(line_ids)
            for aml in move_lines:
                if not currency and aml.currency_id.id:
                    currency = aml.currency_id.id
                elif aml.currency_id:
                    if aml.currency_id.id == currency:
                        continue
                    raise UserError(_('Operation not allowed. You can only reconcile entries that share the same secondary currency or that don\'t have one. Edit your journal items or make another selection before proceeding any further.'))
            #Because we are making a full reconcilition in batch, we need to consider use cases as defined in the test test_manual_reconcile_wizard_opw678153
            #So we force the reconciliation in company currency only at first, then in second pass the amounts in secondary currency.
            move_lines.with_context(skip_full_reconcile_check = 'amount_currency_excluded', manual_full_reconcile_currency=currency).reconcile()
            move_lines_filtered = move_lines.filtered(lambda aml: not aml.reconciled)
            if move_lines_filtered:
                move_lines_filtered.with_context(skip_full_reconcile_check='amount_currency_only', manual_full_reconcile_currency=currency).reconcile()
            move_lines.compute_full_after_batch_reconcile()
        return

    @api.multi
    def confirm_booking(self):
        """ Confirm the booking after all moves have been imported
         
        :param ids: List of Datev Imports
        """
        for thisimport in self:
            error = False
            for move in thisimport.account_moves:
                if move.state == 'draft':
                    try:
                        move.post()
                        self.env['import.datev.log'].create({
                            'parent_id': thisimport.id,
                            'name': _("%s booked successful.") % (ustr(move.name)),
                            'state': 'standard',
                        })
                    except:
                        tb_s = functools.reduce(lambda x, y: x + y, traceback.format_exception(sys.exc_info()))
                        self.env['import.datev.log'].create({
                            'parent_id': thisimport.id,
                            'name': _("%s could not be booked, ERP ERROR: %s") % (ustr(move.name), tb_s),
                            'state': 'error',
                        })
                        error = True
            if error is False:
                self.write({'state': 'booked'})
            else:
                self.write({'state': 'booking_error'})
        return True


class ImportDatevLog(models.Model):
    """
    Logzeilenobject des Imports
    """
    _name = 'import.datev.log'
    _order = 'id desc'

    name = fields.Text('Name')
    parent_id = fields.Many2one('import.datev', 'Import', ondelete='cascade')
    date = fields.Datetime('Time', readonly=True, default=lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'))
    state = fields.Selection([('info', 'Info'), ('error', 'Error'), ('standard', 'Ok')],
                             'State', index=True, readonly=True, default='info')
