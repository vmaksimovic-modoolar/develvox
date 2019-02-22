##############################################################################
#
# Copyright (c) 2018 - Now Modoolar (http://modoolar.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract support@modoolar.com
#
##############################################################################
from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    contact_person_id = fields.Many2one(
        string='Contact Person',
        comodel_name='res.partner',
        domain="[('parent_id', '=', partner_id)]"
    )
