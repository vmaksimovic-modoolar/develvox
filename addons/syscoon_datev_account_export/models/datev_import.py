# -*- coding: utf-8 -*-

##############################################################################
#
#    odoo (formerly known as OpenERP), Open Source Business Applications
#    Copyright (C) 2012-now Josef Kaser (<http://www.pragmasoft.de>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
from io import StringIO
import csv
import datetime
from odoo.tools import ustr

from odoo import api, fields, models, _


class DatevImport(models.TransientModel):
    _name = 'datev.import'

    name = fields.Char('File Name', readonly=True)
    data = fields.Binary('File', readonly=False)
    count = fields.Integer('Count', readonly=True)
    state = fields.Selection([('choose', 'choose'),
                              ('get', 'get')])
    errors = fields.Text('Errors', readonly=True)
    creditor_parent_account_id = fields.Many2one('account.account', 'Kreditor Oberkonto')
    debitor_parent_account_id = fields.Many2one('account.account', 'Debitor Oberkonto')
    creditor_type = fields.Many2one('account.account.type', 'Kreditor Kontoart')
    debitor_type = fields.Many2one('account.account.type', 'Debitor Kontoart')

    defaults = {
        'state': 'choose',
    }

    def create_account(self, accnumber, name, acctype, usertype, parent_id):
        account_obj = self.env['account.account']

        values = {'code': accnumber,
                  'parent_id': parent_id,
                  'name': name,
                  'type': acctype,
                  'user_type': usertype,
                  'active': True,
                  'reconcile': True}

        return account_obj.create(values)

    def row_to_partner(self, this, row, creditor_type, debitor_type):
        partner = {
            'customer': False,
            'active': True,
            'supplier': False
        }

        acctype = 'receivable'
        usertype = False
        parent_id = False

        if int(row[0]) >= 10000 and int(row[0]) <= 69999:
            partner['customer'] = True
            acctype = 'receivable'
            usertype = debitor_type
            parent_id = this.debitor_parent_account_id.id
        elif int(row[0]) >= 70000 and int(row[0]) <= 99999:
            partner['supplier'] = True
            acctype = 'payable'
            usertype = creditor_type
            parent_id = this.creditor_parent_account_id.id
        else:
            return False, False, ("Ungültige Kontonummer: " + str(row[0]))

        if row[6] == "1":
            partner.update({'name': (row[4] + " " + row[3]) if row[3] else "Kein Name",
                            'lname': row[3],
                            'fname': row[4]})
        else:
            partner.update({'name': row[1] or "Leer"})

        acc_id = self.create_account(row[0], partner['name'], acctype, usertype.id, parent_id)

        if not acc_id:
            return False, False, ("Kontonummer existiert bereits. Nr: " + str(row[0]))

        partner_id = False

        if partner_id:
            partner_id.update(
                {
                    (
                    'property_account_receivable_id' if usertype == debitor_type else 'property_account_payable_id'): acc_id,
                    ('customer' if usertype == debitor_type else 'supplier'): True,
                }
            )

            return False, partner, False

        if row[14] == "STR":
            partner.update({'street': row[15] or "",
                            'zip': row[17] or "",
                            'city': row[18] or "",
                            (
                                'property_account_receivable_id' if usertype == debitor_type else 'property_account_payable_id'): acc_id})

        if usertype == debitor_type:
            partner['property_account_receivable_id'] = acc_id
        else:
            partner['property_account_payable_id'] = acc_id

        return True, partner, False

    def parse_file(self, this, datev_file):
        csvReader = csv.reader(StringIO.StringIO(datev_file), delimiter=';', quotechar='"')
        partners = []
        # =======================================================================
        # Für automatische Selektion
        # account_obj = self.pool.get('account.account.type')
        # 
        # creditors = account_obj.search(cr, uid, [('code', '=', 'payable')])
        # creditor_id = account_obj.browse(cr, uid, creditors)
        # 
        # if creditor_id and not isinstance(creditor_id, basestring):
        #     creditor_id = creditor_id[0]
        #     
        # debitors = account_obj.search(cr, uid, [('code', '=', 'receivable')])
        # debitor_id = account_obj.browse(cr, uid, debitors)
        # 
        # if debitor_id and not isinstance(debitor_id, basestring):
        #     debitor_id = debitor_id[0]
        # =======================================================================

        headers = next(csvReader, None)  # Skip Header
        headers = next(csvReader, None)
        count = 0
        errors = []

        for i, row in enumerate(csvReader):
            create, values, error = self.row_to_partner(this, row, this.creditor_type, this.debitor_type)

            if values:
                if create:
                    self.env['res.partner'].create(values)

                count += 1
            else:
                errors.append("Zeile " + str(i) + ":\t" + error)

        return count, errors

    def act_readfile(self):
        this = self

        file_content_decoded = base64.decodestring(this.data)
        count, errors = self.parse_file(this, file_content_decoded)
        now = datetime.datetime.now()
        filename = "DTVF_" + ustr(now.strftime("%Y%m%d%H%M%S")) + ".csv"

        self.update(
            {
                'state': 'get',
                'count': count,
                'errors': errors and "\n".join(errors) or False,
                'name': filename
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'datev.import',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
