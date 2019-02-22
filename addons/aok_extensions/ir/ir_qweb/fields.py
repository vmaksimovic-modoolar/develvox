##############################################################################
#
# Copyright (c) 2018 - Now Modoolar (http://modoolar.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contact support@modoolar.com
#
##############################################################################
from odoo import api, models
from odoo.tools import html_escape as escape


class AokContact(models.AbstractModel):
    _name = 'ir.qweb.field.aok_contact'
    _inherit = 'ir.qweb.field.many2one'

    @api.model
    def value_to_html(self, value, options):
        if not value.exists():
            return False

        values = self.prepare_values(value, options)
        return self.env['ir.qweb'].render('base.contact', values)

    def prepare_values(self, value, options):
        opf = options and options.get('fields') or [
            "name", "address", "phone", "mobile", "email"
        ]
        value = value.sudo().with_context(show_address=True)
        name_get = value.name_get()[0][1]

        return {
            'name': name_get.split("\n")[0].replace(', ', '<br/>'),
            'address': escape("\n".join(name_get.split("\n")[1:])).strip(),
            'phone': value.phone,
            'mobile': value.mobile,
            'city': value.city,
            'country_id': value.country_id.display_name,
            'website': value.website,
            'email': value.email,
            'fields': opf,
            'object': value,
            'options': options
        }
