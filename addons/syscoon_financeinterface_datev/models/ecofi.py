#See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.tools import ustr

from decimal import Decimal
import datetime
import logging

_logger = logging.getLogger(__name__)


class ecofi(models.Model):
    _inherit = 'ecofi'

    @api.multi
    def migrate_datev(self):
        _logger.info("Starting Move Migration")
        invoice_ids = self.env['account.invoice'].search()
        counter = 0
        for invoice in self.env['account.invoice'].browse(invoice_ids):
            counter += 1
            _logger.info(_("Migrate Move %s / %s") % (counter, len(invoice_ids)))
            if invoice.move_id:
                self.env['account.move'].write({
                    'ecofi_buchungstext': invoice.ecofi_buchungstext or False,
                })
                move = self.env['account.move'].browse(invoice.move_id.id)
                for invoice_line in invoice.invoice_line_ids:
                    if invoice_line.invoice_line_tax_ids:
                        for move_line in move.line_ids:
                            if move_line.account_id.id == invoice_line.account_id.id:
                                if move_line.debit + move_line.credit == abs(invoice_line.price_subtotal):
                                    self.env['account.move.line'].write({
                                        'ecofi_taxid': invoice_line.invoice_line_tax_ids[0].id
                                    })
        _logger.info(_("Move Migration Finished"))
        return True

    @api.multi
    def field_config(self, move, line, errorcount, partnererror, thislog, thismovename, faelligkeit, datevdict, belegdatum_format=False):
        """ Method that generates gets the values for the different Datev columns.
        :param move: account_move
        :param line: account_move_line
        :param errorcount: Errorcount
        :param partnererror: Partnererror
        :param thislog: Log
        :param thismovename: Movename
        :param faelligkeit: Fälligkeit
        """
        thisdate = move.date
        if belegdatum_format:
            datum = belegdatum_format.replace('dd', thisdate[8:10])
            datum = datum.replace('mm', thisdate[5:7])
            datum = datum.replace('jjjj', thisdate[0:4])
            datevdict['Datum'] = datum
        else:
            datevdict['Datum'] = ('%s%s%s' % (thisdate[8:10], thisdate[5:7], thisdate[0:4]))
        if move.name:
            datevdict['Beleg1'] = ustr(move.name)
        if move.journal_id.type == 'purchase' and move.ref:
            datevdict['Beleg1'] = ustr(move.ref)
        datevdict['Beleg1'] = datevdict['Beleg1'][-12:]
        if faelligkeit:
            datevdict['Beleg2'] = faelligkeit
        datevdict['Waehrung'], datevdict['Kurs'] = self.format_waehrung(line)
        if line.move_id.ecofi_buchungstext:
            datevdict['Buchungstext'] = ustr(line.move_id.ecofi_buchungstext)#
        else:
            datevdict['Buchungstext'] = line.name
        if line.account_id.ustuebergabe:
            if move.partner_id:
                if move.partner_id.vat:
                    datevdict['EulandUSTID'] = ustr(move.partner_id.vat)
                    if datevdict['EulandUSTID'] == '':
                        errorcount += 1
                        partnererror.append(move.partner_id.id)
                        thislog = thislog + thismovename + _(u'Error: No sales tax identification number stored in the partner!') + '\n'
        datevdict['Beleg1'] = ''.join(e for e in datevdict['Beleg1'] if e.isalnum())
        return errorcount, partnererror, thislog, thismovename, datevdict

    @api.multi
    def format_umsatz(self, lineumsatz):
        """ Returns the formatted amount
        :param lineumsatz: amountC
        :param context: context arguments, like lang, time zone
        :param lineumsatz:
        """
        Umsatz = ''
        Sollhaben = ''
        if lineumsatz < 0:
            Umsatz = str(lineumsatz * -1).replace('.', ',')
            Sollhaben = 's'
        if lineumsatz > 0:
            Umsatz = str(lineumsatz).replace('.', ',')
            Sollhaben = 'h'
        if lineumsatz == 0:
            Umsatz = str(lineumsatz).replace('.', ',')
            Sollhaben = 's'
        return Umsatz, Sollhaben

    @api.multi
    def format_waehrung(self, line):
        """ Formats the currency for the export
        :param line: account_move_line
        """
        context = self._context
        user = self.env['res.users'].browse(self._uid)
        Waehrung = False
        if user.company_id:
            Waehrung = user.company_id.currency_id.id
        else:
            thiscompany = self.env['res.company'].search([('parent_id', '=', False)])[0]
            thiscompany = self.env['res.company'].browse([thiscompany])[0]
            Waehrung = thiscompany.currency_id.id
        if line.currency_id:
            Waehrung = line.currency_id.id
        if Waehrung:
            thisw = self.env['res.currency'].browse(Waehrung)
            Waehrung = thisw.name
            if Waehrung != 'EUR':
                Faktor = ustr(thisw.rate).replace('.', ',')
            else:
                Faktor = ''
        return Waehrung, Faktor

    @api.multi
    def generate_csv(self, ecofi_csv, bookingdict, log):
        """ Implements the generate_csv method for the datev interface
        """

        user = self.env.user
        berater_nr = user.company_id.tax_accountant_id
        mandanten_nr = user.company_id.client_id

        if berater_nr and mandanten_nr:

            datum_von = 0
            datum_bis = 0
            datum_arr = []

            for buchungssatz in bookingdict['buchungen']:
                datum_arr.append(buchungssatz[9])

            datum_von_str = str(min(datum_arr))
            datum_bis_str = str(max(datum_arr))

            datum_von = int('%s%s%s' % (datum_von_str[4:8], datum_von_str[2:4], datum_von_str[0:2]))
            datum_bis = int('%s%s%s' % (datum_bis_str[4:8], datum_bis_str[2:4], datum_bis_str[0:2]))

            current_date = datetime.datetime.now()
            current_date_string = current_date.isoformat()

            automatisierungs_header_dict = {
                'DATEVFormatKZ': 'EXTF',
                'Versionsnummer': 141,
                'Datenkategorie': 21,
                'Formatname': 'Buchungsstapel',
                'Formatversion': 1,
                'Erzeugtam': int('%s%s%s%s%s%s%s' % (
                    current_date_string[0:4], current_date_string[5:7], current_date_string[8:10],
                    current_date_string[11:13], current_date_string[14:16], current_date_string[17:19],
                    current_date_string[20:23])),
                'Importiert': '',
                'Herkunft': 'OE',
                'Exportiertvon': '',
                'Importiertvon': '',
                'Berater': int(berater_nr),
                'Mandant': int(mandanten_nr),
                'WJBeginn': int(str(current_date.year) + '0101'),
                'Sachkontenlaenge': 4,
                'Datumvon': datum_von,
                'Datumbis': datum_bis,
                'Bezeichnung': '',
                'Diktatkuerzel': '',
                'Buchungstyp': '',
                'Rechnungslegungszweck': '',
                'res1': '',
                'WKZ': '',
                'res2': '',
                'res3': '',
                'res4': '',
                'res5': '',
            }

            ecofi_csv.writerow(self.buchungenAutomatisierungsHeaderDatev(automatisierungs_header_dict))

        if 'export_interface' in self._context:
            if self._context['export_interface'] == 'datev':
                ecofi_csv.writerow(bookingdict['buchungsheader'])
                for buchungsatz in bookingdict['buchungen']:
                    ecofi_csv.writerow(buchungsatz)
        (ecofi_csv, log) = super(ecofi, self).generate_csv(ecofi_csv, bookingdict, log)
        return ecofi_csv, log

    @api.multi
    def generate_csv_move_lines(self, move, buchungserror, errorcount, thislog, thismovename,
                                exportmethod, partnererror, buchungszeilencount, bookingdict):
        """ Implements the generate_csv_move_lines method for the datev interface
        """
        belegdatum_format = self.env.user.company_id.voucher_date_format
        if self._context.get('export_interface', '') == 'datev':
            if 'buchungen' not in bookingdict:
                bookingdict['buchungen'] = []
            if 'buchungsheader' not in bookingdict:
                bookingdict['buchungsheader'] = self.buchungenHeaderDatev()
            user = self.env['res.users'].browse(self._uid)
            if user.company_id.enable_fixing == True:
                finance_secure = '1'
            else:
                finance_secure = '0'
            faelligkeit = False
            for line in move.line_ids:
                if line.debit == 0 and line.credit == 0:
                    continue
                datevkonto = line.ecofi_account_counterpart.code
                datevgegenkonto = ustr(line.account_id.code)
                if datevgegenkonto == datevkonto:
                    if line.journal_id.type != 'sale' or line.journal_id.type != 'purchase':
                        if line.payment_id.invoice_ids:
                            faelligkeit = line.payment_id.invoice_ids[0].number
                            faelligkeit = ustr(faelligkeit.replace('/', ''))
                    #if line.date_maturity:
                    #    faelligkeit = '%s%s%s' % (line.date[8:10], line.date[5:7], line.date[2:4])
                    continue
                lineumsatz = Decimal(str(0))
                lineumsatz += Decimal(str(line.debit))
                lineumsatz -= Decimal(str(line.credit))
                self = self.with_context(waehrung = False)
                if line.amount_currency != 0.0:
                    lineumsatz = Decimal(str(line.amount_currency))
                    self = self.with_context(waehrung = True)
                buschluessel = ''
                if exportmethod == 'brutto':
                    if self.is_taxline(line.account_id.id) and not line.ecofi_bu == 'SD':
                        continue
                    if line.ecofi_bu and line.ecofi_bu == '40':
                        buschluessel = '40'
                    else:
                        taxamount = self.calculate_tax(line)
                        lineumsatz = lineumsatz + Decimal(str(taxamount))
                        linetax = self.get_line_tax(line)
                        if not line.account_id.automatic and linetax:
                            buschluessel = str(linetax.buchungsschluessel)  # pylint: disable-msg=E1103
                umsatz, sollhaben = self.format_umsatz(lineumsatz)

                datevdict = {
                    'Umsatz': umsatz,
                    'Sollhaben': sollhaben,
                    'WKZUmsatz': '',
                    'Kurs': '',
                    'BasisUmsatz': '',
                    'WKZBasisUmsatz': '',
                    'Konto': datevkonto or '',
                    'Gegenkonto': datevgegenkonto,
                    'Buschluessel': buschluessel,
                    'Datum': '',
                    'Beleg1': '',
                    'Beleg2': '',
                    'Skonto': '',
                    'Buchungstext': '',
                    'Postensperre': '',
                    'DiverseAdressnummer': '',
                    'Geschaeftspartnerbank': '',
                    'Sachverhalt': '',
                    'Zinssperre': '',
                    'Beleglink': '',
                    'BeleginfoArt1': '',
                    'BeleginfoInhalt1': '',
                    'BeleginfoArt2': '',
                    'BeleginfoInhalt2': '',
                    'BeleginfoArt3': '',
                    'BeleginfoInhalt3': '',
                    'BeleginfoArt4': '',
                    'BeleginfoInhalt4': '',
                    'BeleginfoArt5': '',
                    'BeleginfoInhalt5': '',
                    'BeleginfoArt6': '',
                    'BeleginfoInhalt6': '',
                    'BeleginfoArt7': '',
                    'BeleginfoInhalt7': '',
                    'BeleginfoArt8': '',
                    'BeleginfoInhalt8': '',
                    'Kost1': '',
                    'Kost2': '',
                    'KostMenge': '',
                    'EulandUSTID': '',
                    'EUSteuer': '',
                    'AbwVersteuerungsart': '',
                    'SachverhaltLL': '',
                    'FunktionsergänzungLL': '',
                    'BU49Hauptfunktionstyp': '',
                    'BU49Hauptfunktionsnummer': '',
                    'BU49Funktionsergänzung': '',
                    'ZusatzinformationArt 1': '',
                    'ZusatzinformationInhalt1': '',
                    'ZusatzinformationArt2': '',
                    'ZusatzinformationInhalt2': '',
                    'ZusatzinformationArt3': '',
                    'ZusatzinformationInhalt3': '',
                    'ZusatzinformationArt4': '',
                    'ZusatzinformationInhalt4': '',
                    'ZusatzinformationArt5': '',
                    'ZusatzinformationInhalt5': '',
                    'ZusatzinformationArt6': '',
                    'ZusatzinformationInhalt6': '',
                    'ZusatzinformationArt7': '',
                    'ZusatzinformationInhalt7': '',
                    'ZusatzinformationArt8': '',
                    'ZusatzinformationInhalt8': '',
                    'ZusatzinformationArt9': '',
                    'ZusatzinformationInhalt9': '',
                    'ZusatzinformationArt10': '',
                    'ZusatzinformationInhalt10': '',
                    'ZusatzinformationArt11': '',
                    'ZusatzinformationInhalt11': '',
                    'ZusatzinformationArt12': '',
                    'ZusatzinformationInhalt12': '',
                    'ZusatzinformationArt13': '',
                    'ZusatzinformationInhalt13': '',
                    'ZusatzinformationArt14': '',
                    'ZusatzinformationInhalt14': '',
                    'ZusatzinformationArt15': '',
                    'ZusatzinformationInhalt15': '',
                    'ZusatzinformationArt16': '',
                    'ZusatzinformationInhalt16': '',
                    'ZusatzinformationArt17': '',
                    'ZusatzinformationInhalt17': '',
                    'ZusatzinformationArt18': '',
                    'ZusatzinformationInhalt18': '',
                    'ZusatzinformationArt19': '',
                    'ZusatzinformationInhalt19': '',
                    'ZusatzinformationArt20': '',
                    'ZusatzinformationInhalt20': '',
                    'Stueck': '',
                    'Gewicht': '',
                    'Zahlweise': '',
                    'Forderungsart': '',
                    'Veranlagungsjahr': '',
                    'ZugeordneteFaelligkeit': '',
                    'Skontotyp': '',
                    'Auftragsnummer': '',
                    'Buchungstyp': '',
                    'UStSchluessel': '',
                    'EULand': '',
                    'SachverhaltLL': '',
                    'EUSteuersatzAnzahlungen': '',
                    'ErloeskontoAnzahlungen': '',
                    'HerkunftKz': '',
                    'BuchungsGUID': '',
                    'KOSTDatum': '',
                    'SEPAMandatsreferenz': '',
                    'Skontosperre': '',
                    'Gesellschaftername': '',
                    'Beteiligtennummer': '',
                    'Identifikationsnummer': '',
                    'Zeichnernummer': '',
                    'Movename': ustr(move.name),
                    'Postensperre bis': '',
                    'Bezeichnung SoBil-Sachverhalt': '',
                    'Kennzeichen SoBil-Buchung': '',
                    'Festschreibung': finance_secure,
                    'Leistungsdatum': '',
                    'Datum Zuord.Steuerperiode': '',
                }

                (errorcount, partnererror, thislog, thismovename, datevdict) = \
                    self.field_config(move, line, errorcount, partnererror, thislog,
                    thismovename, faelligkeit, datevdict, belegdatum_format)


                bookingdict['buchungen'].append(self.buchungenCreateDatev(datevdict))
                buchungszeilencount += 1

        buchungserror, errorcount, thislog, partnererror, buchungszeilencount, bookingdict = \
            super(ecofi, self).generate_csv_move_lines(move, buchungserror, errorcount, thislog, 
            thismovename, exportmethod, partnererror, buchungszeilencount, bookingdict)

        return buchungserror, errorcount, thislog, partnererror, buchungszeilencount, bookingdict

    def buchungenAutomatisierungsHeaderDatev(self, dict):
        # erstellt den Automatisierungheader
        buchung = []

        buchung.append(dict['DATEVFormatKZ'])
        buchung.append(dict['Versionsnummer'])
        buchung.append(dict['Datenkategorie'])
        buchung.append(dict['Formatname'])
        buchung.append(dict['Formatversion'])
        buchung.append(dict['Erzeugtam'])
        buchung.append(dict['Importiert'])
        buchung.append(dict['Herkunft'])
        buchung.append(dict['Exportiertvon'])
        buchung.append(dict['Importiertvon'])
        buchung.append(dict['Berater'])
        buchung.append(dict['Mandant'])
        buchung.append(dict['WJBeginn'])
        buchung.append(dict['Sachkontenlaenge'])
        buchung.append(dict['Datumvon'])
        buchung.append(dict['Datumbis'])
        buchung.append(dict['Bezeichnung'])
        buchung.append(dict['Diktatkuerzel'])
        buchung.append(dict['Buchungstyp'])
        buchung.append(dict['Rechnungslegungszweck'])
        buchung.append(dict['res1'])
        buchung.append(dict['WKZ'])
        buchung.append(dict['res2'])
        buchung.append(dict['res3'])
        buchung.append(dict['res4'])
        buchung.append(dict['res5'])

        return buchung

    def buchungenHeaderDatev(self):
        """ Method that creates the Datev CSV header line
        """
        return [
            u'Umsatz (ohne Soll/Haben-Kz)',
            u'Soll/Haben-Kennzeichen',
            u'WKZ Umsatz',
            u'Kurs',
            u'Basis-Umsatz',
            u'WKZ Basis-Umsatz',
            u'Konto',
            u'Gegenkonto (ohne BU-Schlüssel)',
            u'BU-Schlüssel',
            u'Belegdatum',
            u'Belegfeld 1',
            u'Belegfeld 2',
            u'Skonto',
            u'Buchungstext',
            u'Postensperre',
            u'Diverse Adressnummer',
            u'Geschäftspartnerbank',
            u'Sachverhalt',
            u'Zinssperre',
            u'Beleglink',
            u'Beleginfo - Art 1',
            u'Beleginfo - Inhalt 1',
            u'Beleginfo - Art 2',
            u'Beleginfo - Inhalt 2',
            u'Beleginfo - Art 3',
            u'Beleginfo - Inhalt 3',
            u'Beleginfo - Art 4',
            u'Beleginfo - Inhalt 4',
            u'Beleginfo - Art 5',
            u'Beleginfo - Inhalt 5',
            u'Beleginfo - Art 6',
            u'Beleginfo - Inhalt 6',
            u'Beleginfo - Art 7',
            u'Beleginfo - Inhalt 7',
            u'Beleginfo - Art 8',
            u'Beleginfo - Inhalt 8',
            u'KOST1 - Kostenstelle',
            u'KOST2 - Kostenstelle',
            u'Kost-Menge',
            u'EU-Land u. UStID ',
            u'EU-Steuersatz',
            u'Abw. Versteuerungsart',
            u'Sachverhalt L+L',
            u'Funktionsergänzung L+L',
            u'BU 49 Hauptfunktionstyp',
            u'BU 49 Hauptfunktionsnummer',
            u'BU 49 Funktionsergänzung',
            u'Zusatzinformation - Art 1',
            u'Zusatzinformation- Inhalt 1',
            u'Zusatzinformation - Art 2',
            u'Zusatzinformation- Inhalt 2',
            u'Zusatzinformation - Art 3',
            u'Zusatzinformation- Inhalt 3',
            u'Zusatzinformation - Art 4',
            u'Zusatzinformation- Inhalt 4',
            u'Zusatzinformation - Art 5',
            u'Zusatzinformation- Inhalt 5',
            u'Zusatzinformation - Art 6',
            u'Zusatzinformation- Inhalt 6',
            u'Zusatzinformation - Art 7',
            u'Zusatzinformation- Inhalt 7',
            u'Zusatzinformation - Art 8',
            u'Zusatzinformation- Inhalt 8',
            u'Zusatzinformation - Art 9',
            u'Zusatzinformation- Inhalt 9',
            u'Zusatzinformation - Art 10',
            u'Zusatzinformation- Inhalt 10',
            u'Zusatzinformation - Art 11',
            u'Zusatzinformation- Inhalt 11',
            u'Zusatzinformation - Art 12',
            u'Zusatzinformation- Inhalt 12',
            u'Zusatzinformation - Art 13',
            u'Zusatzinformation- Inhalt 13',
            u'Zusatzinformation - Art 14',
            u'Zusatzinformation- Inhalt 14',
            u'Zusatzinformation - Art 15',
            u'Zusatzinformation- Inhalt 15',
            u'Zusatzinformation - Art 16',
            u'Zusatzinformation- Inhalt 16',
            u'Zusatzinformation - Art 17',
            u'Zusatzinformation- Inhalt 17',
            u'Zusatzinformation - Art 18',
            u'Zusatzinformation- Inhalt 18',
            u'Zusatzinformation - Art 19',
            u'Zusatzinformation- Inhalt 19',
            u'Zusatzinformation - Art 20',
            u'Zusatzinformation- Inhalt 20',
            u'Stück',
            u'Gewicht',
            u'Zahlweise',
            u'Forderungsart',
            u'Veranlagungsjahr',
            u'Zugeordnete Fälligkeit',
            u'Skontotyp',
            u'Auftragsnummer',
            u'Buchungstyp',
            u'USt-Schlüssel (Anzahlungen)',
            u'EU-Land (Anzahlungen)',
            u'Sachverhalt L+L (Anzahlungen)',
            u'EU-Steuersatz (Anzahlungen)',
            u'Erlöskonto (Anzahlungen)',
            u'Herkunft-Kz',
            u'Buchungs GUID',
            u'KOST-Datum',
            u'SEPA-Mandatsreferenz',
            u'Skontosperre',
            u'Gesellschaftername',
            u'Beteiligtennummer',
            u'Identifikationsnummer',
            u'Zeichnernummer',
            u'Postensperre bis',
            u'Bezeichnung SoBil-Sachverhalt',
            u'Kennzeichen SoBil-Buchung',
            u'Festschreibung',
            u'Leistungsdatum',
            u'Datum Zuord.Steuerperiode',
        ]

    def buchungenCreateDatev(self, datevdict):
        """Method that creates the datev csv move line
        """
        if datevdict['Buschluessel'] == '0':
            datevdict['Buschluessel'] = ''
        datevdict['Buchungstext'] = datevdict['Buchungstext'][0:60]

        return [
            datevdict['Umsatz'],
            datevdict['Sollhaben'],
            datevdict['WKZUmsatz'],
            datevdict['Kurs'],
            datevdict['BasisUmsatz'],
            datevdict['WKZBasisUmsatz'],
            datevdict['Konto'],
            datevdict['Gegenkonto'],
            datevdict['Buschluessel'],
            datevdict['Datum'],
            datevdict['Beleg1'],
            datevdict['Beleg2'],
            datevdict['Skonto'],
            datevdict['Buchungstext'],
            datevdict['Postensperre'],
            datevdict['DiverseAdressnummer'],
            datevdict['Geschaeftspartnerbank'],
            datevdict['Sachverhalt'],
            datevdict['Zinssperre'],
            datevdict['Beleglink'],
            datevdict['BeleginfoArt1'],
            datevdict['BeleginfoInhalt1'],
            datevdict['BeleginfoArt2'],
            datevdict['BeleginfoInhalt2'],
            datevdict['BeleginfoArt3'],
            datevdict['BeleginfoInhalt3'],
            datevdict['BeleginfoArt4'],
            datevdict['BeleginfoInhalt4'],
            datevdict['BeleginfoArt5'],
            datevdict['BeleginfoInhalt5'],
            datevdict['BeleginfoArt6'],
            datevdict['BeleginfoInhalt6'],
            datevdict['BeleginfoArt7'],
            datevdict['BeleginfoInhalt7'],
            datevdict['BeleginfoArt8'],
            datevdict['BeleginfoInhalt8'],
            datevdict['Kost1'],
            datevdict['Kost2'],
            datevdict['KostMenge'],
            datevdict['EulandUSTID'],
            datevdict['EUSteuer'],
            datevdict['AbwVersteuerungsart'],
            datevdict['SachverhaltLL'],
            datevdict['FunktionsergänzungLL'],
            datevdict['BU49Hauptfunktionstyp'],
            datevdict['BU49Hauptfunktionsnummer'],
            datevdict['BU49Funktionsergänzung'],
            datevdict['ZusatzinformationArt 1'],
            datevdict['ZusatzinformationInhalt1'],
            datevdict['ZusatzinformationArt2'],
            datevdict['ZusatzinformationInhalt2'],
            datevdict['ZusatzinformationArt3'],
            datevdict['ZusatzinformationInhalt3'],
            datevdict['ZusatzinformationArt4'],
            datevdict['ZusatzinformationInhalt4'],
            datevdict['ZusatzinformationArt5'],
            datevdict['ZusatzinformationInhalt5'],
            datevdict['ZusatzinformationArt6'],
            datevdict['ZusatzinformationInhalt6'],
            datevdict['ZusatzinformationArt7'],
            datevdict['ZusatzinformationInhalt7'],
            datevdict['ZusatzinformationArt8'],
            datevdict['ZusatzinformationInhalt8'],
            datevdict['ZusatzinformationArt9'],
            datevdict['ZusatzinformationInhalt9'],
            datevdict['ZusatzinformationArt10'],
            datevdict['ZusatzinformationInhalt10'],
            datevdict['ZusatzinformationArt11'],
            datevdict['ZusatzinformationInhalt11'],
            datevdict['ZusatzinformationArt12'],
            datevdict['ZusatzinformationInhalt12'],
            datevdict['ZusatzinformationArt13'],
            datevdict['ZusatzinformationInhalt13'],
            datevdict['ZusatzinformationArt14'],
            datevdict['ZusatzinformationInhalt14'],
            datevdict['ZusatzinformationArt15'],
            datevdict['ZusatzinformationInhalt15'],
            datevdict['ZusatzinformationArt16'],
            datevdict['ZusatzinformationInhalt16'],
            datevdict['ZusatzinformationArt17'],
            datevdict['ZusatzinformationInhalt17'],
            datevdict['ZusatzinformationArt18'],
            datevdict['ZusatzinformationInhalt18'],
            datevdict['ZusatzinformationArt19'],
            datevdict['ZusatzinformationInhalt19'],
            datevdict['ZusatzinformationArt20'],
            datevdict['ZusatzinformationInhalt20'],
            datevdict['Stueck'],
            datevdict['Gewicht'],
            datevdict['Zahlweise'],
            datevdict['Forderungsart'],
            datevdict['Veranlagungsjahr'],
            datevdict['ZugeordneteFaelligkeit'],
            datevdict['Skontotyp'],
            datevdict['Auftragsnummer'],
            datevdict['Buchungstyp'],
            datevdict['UStSchluessel'],
            datevdict['EULand'],
            datevdict['SachverhaltLL'],
            datevdict['EUSteuersatzAnzahlungen'],
            datevdict['ErloeskontoAnzahlungen'],
            datevdict['HerkunftKz'],
            datevdict['BuchungsGUID'],
            datevdict['KOSTDatum'],
            datevdict['SEPAMandatsreferenz'],
            datevdict['Skontosperre'],
            datevdict['Gesellschaftername'],
            datevdict['Beteiligtennummer'],
            datevdict['Identifikationsnummer'],
            datevdict['Zeichnernummer'],
            datevdict['Postensperre bis'],
            datevdict['Bezeichnung SoBil-Sachverhalt'],
            datevdict['Kennzeichen SoBil-Buchung'],
            datevdict['Festschreibung'],
            datevdict['Leistungsdatum'],
            datevdict['Datum Zuord.Steuerperiode'],
        ]
