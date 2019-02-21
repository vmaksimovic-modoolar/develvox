# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from datetime import datetime
import os

from odoo import api, fields, models


class EncasingInterface(models.TransientModel):
    _name = 'encasing.interface'
    _description = 'Encasing Interface'
    _rec_name = 'recipient_id'

    recipient_id = fields.Many2one("res.partner", string="Recipient")
    responsible_id = fields.Many2one("res.partner", string="Responsible", default=lambda self: self.env.user.partner_id)
    invoice_lines = fields.Many2many("account.invoice.line", string="Invoice Lines", domain=[('is_encasing', '=', True)])
    # name = fields.Char("File Name")
    date_start = fields.Date(string='Start Date', default=fields.Date.today())
    date_end = fields.Date(string='End Date', default=fields.Date.today())
    # data = fields.Binary('File', readonly=True)

    def get_unb(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        date_today = datetime.now().strftime("%Y %m %d %M:%S")
        counter = ICPSudo.get_param('aok_account.encasing_interface_counter') or 0
        counter = int(counter) + 1
        counter = '{0:05}'.format(counter)
        ICPSudo.set_param("aok_account.encasing_interface_counter", counter)
        filename = 'SL071054S05'
        unb = "UNB+UNOC:3+%s+%s+%s+%s+A+%s+2'" % (self.responsible_id.ref or '', self.recipient_id.ref or '', date_today.replace(" ", ""), counter, filename)
        return unb

    def get_unh(self):
        unh = "UNH+00001+SLGA:11:0:0'"
        return unh

    def get_fkt(self):
        fkt = "FKT+01++%s+%s+%s+%s'" % (self.responsible_id.ref or '', self.recipient_id.ref or '', self.recipient_id.ref or '', self.responsible_id.ref or '')
        return fkt

    def get_rec(self):
        start_date = fields.Date.from_string(self.date_start).strftime('%Y%m%d')
        end_date = fields.Date.from_string(self.date_end).strftime('%Y%m%d')
        rec = "REC+%s:0+%s:0+1'" % (start_date, end_date)
        return rec

    def get_ges(self):
        ges = "GES'"
        return ges

    def get_nam(self):
        nam = "NAM+01+%s+%s %s+%s+Birgit.Ploj@aok-verlag.de'" % (self.responsible_id.company_id.name, self.responsible_id.company_id.name, self.responsible_id.company_id.phone, self.responsible_id.company_id.phone)
        return nam

    def get_unt(self):
        unt = "UNT+%s+00001'" % ('')
        return unt

    def get_unh_1(self):
        unh = "UNH+00002+SLLA:11:0:0'"
        return unh

    def get_fkt_1(self):
        fkt = "FKT+01++%s+%s+%s'" % (self.responsible_id.ref or '', self.recipient_id.ref or '', self.recipient_id.ref or '')
        return fkt

    def get_rec_1(self):
        start_date = fields.Date.from_string(self.date_start).strftime('%Y%m%d')
        end_date = fields.Date.from_string(self.date_end).strftime('%Y%m%d')
        rec = "REC+%s:0+%s:0+1'" % (start_date, end_date)
        return rec

    def get_inv(self, invoice):
        inv = "INV+%s+%s++%s'" % (invoice.partner_id.insured_number, invoice.partner_id.insurance_status.code, invoice.number)
        return inv

    def get_nad(self, invoice):
        birth_date = ''
        if invoice.partner_id.birth_date:
            birth_date = fields.Date.from_string(invoice.partner_id.birth_date).strftime('%Y%m%d')
        nad = "NAD+%s+%s+%s+%s %s+%s+%s'" % (invoice.partner_id.name or '', invoice.partner_id.name or '', birth_date, invoice.partner_id.street or '', invoice.partner_id.street2 or '', invoice.partner_id.zip or '', invoice.partner_id.city or '')
        return nad

    def get_hil(self):
        hil = "HIL+001'"
        return hil

    def get_ehi(self, invoice_line):
        date_invoice = ''
        if invoice_line.invoice_id.date_invoice:
            date_invoice = fields.Date.from_string(invoice_line.invoice_id.date_invoice).strftime('%Y%m%d')
        ehi = "EHI+19:02580+%s+%s+%s+%s+00'" % (invoice_line.product_id.default_code, invoice_line.quantity, invoice_line.price_unit, date_invoice)
        return ehi

    def get_txt(self, invoice_line):
        txt = "TXT+%s'" % (invoice_line.name or '')
        return txt

    def get_mws(self, invoice_line):
        mws = "MWS+1+%s'" % (invoice_line.price_total - invoice_line.price_subtotal)
        return mws

    def get_zhi(self, invoice):
        date_invoice = ''
        if invoice.date_invoice:
            date_invoice = fields.Date.from_string(invoice.date_invoice).strftime('%Y%m%d')
        zhi = "ZHI+999999999+999999999+%s+00'" % (date_invoice)
        return zhi

    def get_bes(self, invoice):
        invoice_amount = sum(invoice.invoice_line_ids.filtered(lambda r: r.is_encasing).mapped('price_total'))
        bes = "BES+%s+0,00+0,00+0,00+'" % (invoice_amount)
        return bes

    # Footer
    def get_unt_1(self):
        unt = "UNT+%s+%s'" % ('', '')
        return unt

    def get_unz(self):
        unz = "UNZ+%s+%s'" % ('', '')
        return unz

    def convert_bytes(self, num):
        """
        this function will convert bytes to MB.... GB... etc
        """
        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return "%3.1f %s" % (num, x)
            num /= 1024.0

    @api.multi
    def generate_txt(self):
        file = open("testfile.txt", "w")

        # Header
        unb = self.get_unb()
        file.write(unb + '\n')
        unh = self.get_unh()
        file.write(unh + '\n')
        fkt = self.get_fkt()
        file.write(fkt + '\n')
        rec = self.get_rec()
        file.write(rec + '\n')
        ges = self.get_ges()
        file.write(ges + '\n')
        nam = self.get_nam()
        file.write(nam + '\n')
        unt = self.get_unt()
        file.write(unt + '\n')
        unh_1 = self.get_unh_1()
        file.write(unh_1 + '\n')
        fkt_1 = self.get_fkt_1()
        file.write(fkt_1 + '\n')
        rec_1 = self.get_rec_1()
        file.write(rec_1 + '\n')

        # Invoice
        invoices = self.invoice_lines.mapped('invoice_id')
        for invoice in invoices:
            inv = self.get_inv(invoice)
            file.write(inv + '\n')
            nad = self.get_nad(invoice)
            file.write(nad + '\n')
            hil = self.get_hil()
            file.write(hil + '\n')

            # Invoice Lines
            for line in self.invoice_lines.filtered(lambda r: r.invoice_id == invoice):
                ehi = self.get_ehi(line)
                file.write(ehi + '\n')
                txt = self.get_txt(line)
                file.write(txt + '\n')
                mws = self.get_mws(line)
                file.write(mws + '\n')

            zhi = self.get_zhi(invoice)
            file.write(zhi + '\n')
            bes = self.get_bes(invoice)
            file.write(bes + '\n')

        # Footer
        unt_1 = self.get_unt_1()
        file.write(unt_1 + '\n')
        unz = self.get_unz()
        file.write(unz + '\n')

        file.close()
        file = open("testfile.txt", "r")
        file_data = file.read()

        # File Size
        statinfo = os.stat('testfile.txt')
        file_size = statinfo.st_size
        self.env['ir.config_parameter'].sudo().set_param("aok_account.encasing_interface_file_size", file_size)
        file.close()

        #Pass your text file data using encoding.
        values = {
                    'name': "Name of text file.txt",
                    'datas_fname': 'print_file_name.txt',
                    'res_model': 'ir.ui.view',
                    'res_id': False,
                    'type': 'binary',
                    'public': True,
                    # 'datas': file_data.encode('utf8').encode('base64'),
                    'datas': base64.b64encode(bytes(file_data, 'utf-8')),
                }

        # Using your data create as attachment
        attachment_id = self.env['ir.attachment'].sudo().create(values)

        #Prepare your download URL
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        # Return so it will download in your system
        return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url),
                "target": "new",
             }

    def get_IDENTIFIKATOR(self):
        return '500000'

    def get_LANGE_AUFTRAG(self):
        return '00000348'

    def get_SEQUENZ_NR(self):
        return '000'

    def get_VERFAHREN_KENNUNG(self):
        return 'ESOL0'

    def get_TRANSFER_NUMMER(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        counter = ICPSudo.get_param('aok_account.encasing_interface_uaf_counter') or 0
        counter = int(counter) + 1
        counter = '{0:03}'.format(counter)
        ICPSudo.set_param("aok_account.encasing_interface_uaf_counter", counter)
        return counter

    def get_VERFAHREN_KENNUNG_SPEZIFIKATION(self):
        return 'RECP'

    def get_ABSENDER_EIGNER(self):
        return ' 590710544'

    def get_ABSENDER_PHYSIKALISCH(self):
        return ' 590710544'

    def get_EMPFANGER_NUTZER(self):
        return '108310400'

    def get_EMPFANGER_PHYSIKALISCH(self):
        return '108310400'

    def get_FEHLER_NUMMER(self):
        return '000000'

    def get_FEHLER_MABNAHME(self):
        return '000000'

    def get_DATEINAME(self):
        return ''

    def get_DATUM_ERSTELLUNG(self):
        return ''

    def get_DATUM_UBERTRAGUNG_GESENDET(self):
        return ''

    def get_DATUM_UBERTRAGUNG_EMPFANGEN_START(self):
        return ''

    def get_DATUM_UBERTRAGUNG_EMPFANGEN_ENDE(self):
        return ''

    def get_DATEIVERSION(self):
        return '000000'

    def get_KORREKTUR(self):
        return '0'

    def get_DATEIGROBE_NUTZDATEN(self):
        """ Size of the txt-file in byte """
        file_size = self.env['ir.config_parameter'].sudo().get_param('aok_account.encasing_interface_file_size') or ''
        return file_size

    def get_DATEIGROBE_UBERTRAGUNG(self):
        """ Size of the txt-file in byte """
        file_size = self.env['ir.config_parameter'].sudo().get_param('aok_account.encasing_interface_file_size') or ''
        return file_size

    def get_ZEICHENSATZ(self):
        return 'I8'

    def get_KOMPRIMIERUNG(self):
        return '00'

    def get_VERSCHLUSSELUNGSART(self):
        return '03'

    def get_ELEKTRONISCHE_UNTERSCHRIFT(self):
        return '00'

    def get_SATZFORMAT(self):
        return '   '

    def get_SATZLANGE(self):
        return '00000'

    def get_BLOCKLANGE(self):
        return '00000000'

    def get_Status(self):
        return '0'

    def get_Wiederholung(self):
        return '00'

    def get_Ubertragungsweg(self):
        return '0'

    def get_Verzogerter_Versand(self):
        return '          '

    def get_Info_und_Fehlerfelder(self):
        return '000000'

    def get_Variables_InfoFeld(self):
        spaces = ''
        spaces += ' ' * 28
        return spaces

    def get_E_MAIL_ADRESSE_ABSENDER(self):
        spaces = ''
        spaces += ' ' * 44
        return spaces

    def get_DATEI_BEZEICHNUNG(self):
        spaces = ''
        spaces += ' ' * 30
        return spaces

    @api.multi
    def generate_auf(self):
        file = open("testfilesuf.txt", "w")

        IDENTIFIKATOR = self.get_IDENTIFIKATOR()
        file.write(IDENTIFIKATOR + ' ')
        LANGE_AUFTRAG = self.get_LANGE_AUFTRAG()
        file.write(LANGE_AUFTRAG + ' ')
        SEQUENZ_NR = self.get_SEQUENZ_NR()
        file.write(SEQUENZ_NR + ' ')
        VERFAHREN_KENNUNG = self.get_VERFAHREN_KENNUNG()
        file.write(VERFAHREN_KENNUNG + ' ')
        TRANSFER_NUMMER = self.get_TRANSFER_NUMMER()
        file.write(TRANSFER_NUMMER + ' ')
        VERFAHREN_KENNUNG_SPEZIFIKATION = self.get_VERFAHREN_KENNUNG_SPEZIFIKATION()
        file.write(VERFAHREN_KENNUNG_SPEZIFIKATION + ' ')
        ABSENDER_EIGNER = self.get_ABSENDER_EIGNER()
        file.write(ABSENDER_EIGNER + ' ')
        ABSENDER_PHYSIKALISCH = self.get_ABSENDER_PHYSIKALISCH()
        file.write(ABSENDER_PHYSIKALISCH + ' ')
        EMPFANGER_NUTZER = self.get_EMPFANGER_NUTZER()
        file.write(EMPFANGER_NUTZER + ' ')
        EMPFANGER_PHYSIKALISCH = self.get_EMPFANGER_PHYSIKALISCH()
        file.write(EMPFANGER_PHYSIKALISCH + ' ')
        FEHLER_NUMMER = self.get_FEHLER_NUMMER()
        file.write(FEHLER_NUMMER + ' ')
        FEHLER_MABNAHME = self.get_FEHLER_MABNAHME()
        file.write(FEHLER_MABNAHME + ' ')
        DATEINAME = self.get_DATEINAME()
        file.write(DATEINAME + ' ')
        DATUM_ERSTELLUNG = self.get_DATUM_ERSTELLUNG()
        file.write(DATUM_ERSTELLUNG + ' ')
        DATUM_UBERTRAGUNG_GESENDET = self.get_DATUM_UBERTRAGUNG_GESENDET()
        file.write(DATUM_UBERTRAGUNG_GESENDET + ' ')
        DATUM_UBERTRAGUNG_EMPFANGEN_START = self.get_DATUM_UBERTRAGUNG_EMPFANGEN_START()
        file.write(DATUM_UBERTRAGUNG_EMPFANGEN_START + ' ')
        DATUM_UBERTRAGUNG_EMPFANGEN_ENDE = self.get_DATUM_UBERTRAGUNG_EMPFANGEN_ENDE()
        file.write(DATUM_UBERTRAGUNG_EMPFANGEN_ENDE + ' ')
        DATEIVERSION = self.get_DATEIVERSION()
        file.write(DATEIVERSION + ' ')
        KORREKTUR = self.get_KORREKTUR()
        file.write(KORREKTUR + ' ')
        DATEIGROBE_NUTZDATEN = self.get_DATEIGROBE_NUTZDATEN()
        file.write(DATEIGROBE_NUTZDATEN + ' ')
        DATEIGROBE_UBERTRAGUNG = self.get_DATEIGROBE_UBERTRAGUNG()
        file.write(DATEIGROBE_UBERTRAGUNG + ' ')
        ZEICHENSATZ = self.get_ZEICHENSATZ()
        file.write(ZEICHENSATZ + ' ')
        KOMPRIMIERUNG = self.get_KOMPRIMIERUNG()
        file.write(KOMPRIMIERUNG + ' ')
        VERSCHLUSSELUNGSART = self.get_VERSCHLUSSELUNGSART()
        file.write(VERSCHLUSSELUNGSART + ' ')
        ELEKTRONISCHE_UNTERSCHRIFT = self.get_ELEKTRONISCHE_UNTERSCHRIFT()
        file.write(ELEKTRONISCHE_UNTERSCHRIFT + ' ')
        SATZFORMAT = self.get_SATZFORMAT()
        file.write(SATZFORMAT + ' ')
        SATZLANGE = self.get_SATZLANGE()
        file.write(SATZLANGE + ' ')
        BLOCKLANGE = self.get_BLOCKLANGE()
        file.write(BLOCKLANGE + ' ')
        Status = self.get_Status()
        file.write(Status + ' ')
        Wiederholung = self.get_Wiederholung()
        file.write(Wiederholung + ' ')
        Ubertragungsweg = self.get_Ubertragungsweg()
        file.write(Ubertragungsweg + ' ')
        Verzogerter_Versand = self.get_Verzogerter_Versand()
        file.write(Verzogerter_Versand + ' ')
        Info_und_Fehlerfelder = self.get_Info_und_Fehlerfelder()
        file.write(Info_und_Fehlerfelder + ' ')
        Variables_InfoFeld = self.get_Variables_InfoFeld()
        file.write(Variables_InfoFeld + ' ')
        E_MAIL_ADRESSE_ABSENDER = self.get_E_MAIL_ADRESSE_ABSENDER()
        file.write(E_MAIL_ADRESSE_ABSENDER + ' ')
        DATEI_BEZEICHNUNG = self.get_DATEI_BEZEICHNUNG()
        file.write(DATEI_BEZEICHNUNG + ' ')

        file.close()
        file = open("testfilesuf.txt", "r")
        file_data = file.read()
        file.close()

        #Pass your text file data using encoding.
        values = {
            'name': "Name of auf file.txt",
            'datas_fname': 'print_auf_file_name.txt',
            'res_model': 'ir.ui.view',
            'res_id': False,
            'type': 'binary',
            'public': True,
            # 'datas': file_data.encode('utf8').encode('base64'),
            'datas': base64.b64encode(bytes(file_data, 'utf-8')),
        }

        # Using your data create as attachment
        attachment_id = self.env['ir.attachment'].sudo().create(values)

        #Prepare your download URL
        download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        # Return so it will download in your system
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }
