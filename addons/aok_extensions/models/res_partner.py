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

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    name_1 = fields.Char(
    )
    name_2 = fields.Char(
    )
    name_3 = fields.Char(
    )

    @api.onchange('parent_id', 'name_1', 'name_2', 'name_3')
    def _on_change_parent_id_names(self):
        if self.is_company and not self.parent_id and (self.name_1 or self.name_2 or self.name_3):
            self.name = " ".join((p for p in (self.name_1, self.name_2, self.name_3) if p))

    @api.multi
    @api.depends("firstname", "lastname", "name_1", "name_2", "name_3")
    def _compute_name(self):

        for record in self:
            if record.parent_id or not (record.name_1 or record.name_2 or record.name_3):
                record.name = record._get_computed_name(
                    record.lastname,
                    record.firstname
                )
            else:
                record.name = record._get_computed_name123(
                    record.lastname,
                    record.firstname,
                    record.name_1,
                    record.name_2,
                    record.name_3
                )

    @api.model
    def _get_computed_name123(self, lastname, firstname, name_1, name_2, name_3):

            last_first = self._get_computed_name(lastname, firstname)
            name_123 = " ".join((p for p in (name_1, name_2, name_3) if p))

            return name_123 and name_123 + ', ' + last_first or last_first

    @api.model
    def _get_inverse_name(self, name, is_company=False):

        name123 = name.split(',')

        if len(name123) > 1 and not self.parent_id and (self.name_1 or self.name_2 or self.name_3):
            return super(ResPartner, self)._get_inverse_name(
                name.replace(name123[0] + ',', ''),
                is_company
            )
        return super(ResPartner, self)._get_inverse_name(
            name,
            is_company
        )

    @api.multi
    def _compute_sum_no_magazines(self):
        for record in self:
            record.sum_no_magazines = sum(
                self.env['res.partner'].search([
                    ('id', 'child_of', record.id),
                    ('free_of_charge', '!=', True),
                ]).mapped('no_magazines'))
