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

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = _name

    datev_exported = fields.Boolean(_('Exported to DATEV'), compute='_is_datev_exported')

    @api.multi
    def _is_datev_exported(self):
        for person in self:
            receivable = (person.property_account_receivable_id and len(
                person.property_account_receivable_id.code) > 4 and person.property_account_receivable_id.datev_exported)

            payable = (person.property_account_payable_id and len(
                person.property_account_payable_id.code) > 4 and person.property_account_payable_id.datev_exported)

            person.datev_exported = receivable or payable
