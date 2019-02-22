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


class SalesTerritory(models.Model):
    _name = "res.partner.territory"

    name = fields.Char()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sales_territory_id = fields.Many2one(
        comodel_name="res.partner.territory"
    )
    free_of_charge = fields.Boolean(
        string='Free of Charge'
    )
    no_magazines = fields.Integer(
        string='No. magazines G+G'
    )
    no_magazines_aok_service = fields.Integer(
        string='No. magazines AOK-Service'
    )
    sum_no_magazines = fields.Integer(
        string='Sum of no. magazines G+G',
        compute='_compute_sum_no_magazines'
    )
    sum_no_magazines_aok_service = fields.Integer(
        string='Sum of no. magazines AOK-Service',
        compute='_compute_sum_no_magazines_aok_service'
    )
    crm_lead = fields.Char(
        string='CRM-ID'
    )
    enc_name = fields.Char(
        string='Name'
    )
    enc_lastname = fields.Char(
        string='Lastname'
    )
    enc_date = fields.Date(
        string='Date of Birth'
    )
    enc_insurance_number = fields.Char(
        string='Insurance Number',
    )
    enc_insurance_status = fields.Integer(
        string='Insurance Status'
    )
    aok_address = fields.Char(
        string="Address",
        compute="_compute_aok_address",
    )
    parent_id_domain = fields.Char(
        string="Parent Domain",
        compute="_compute_parent_id_domain",
    )
    level_0 = fields.Many2one(
        string='Organisation',
        comodel_name="res.partner",
        compute='_compute_structure',
        readonly=True,
        store=True
    )
    level_1 = fields.Many2one(
        string='Organisation',
        comodel_name="res.partner",
        compute='_compute_structure',
        readonly=True,
        store=True
    )
    level_2 = fields.Many2one(
        string='Organisation',
        comodel_name="res.partner",
        compute='_compute_structure',
        readonly=True,
        store=True
    )
    level_3 = fields.Many2one(
        string='Organisation',
        comodel_name="res.partner",
        compute='_compute_structure',
        readonly=True,
        store=True
    )
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

    @api.multi
    def _compute_sum_no_magazines_aok_service(self):
        for record in self:
            record.sum_no_magazines_aok_service = sum(
                self.env['res.partner'].search([
                    ('id', 'child_of', record.id),
                    ('free_of_charge', '!=', True),
                ]).mapped('no_magazines_aok_service'))

    @api.multi
    @api.depends("city", "zip", "street")
    def _compute_aok_address(self):
        for record in self:
            record.aok_address = (record.street and str(
                record.street) + ", " or '') + (
                                         record.zip and str(
                                     record.zip) + " " or '') + str(
                record.city or '')

    @api.depends('is_company', 'parent_id.commercial_partner_id')
    def _compute_commercial_partner(self):
        for partner in self:
            if partner.is_company or not partner.parent_id:
                partner.commercial_partner_id = partner
            else:
                partner.commercial_partner_id = partner.parent_id.commercial_partner_id

    @api.multi
    @api.constrains('enc_insurance_number')
    def _insurance_number_limit(self):
        for record in self:
            if record.enc_insurance_number and len(
                    record.enc_insurance_number) not in [9, 10]:
                raise ValidationError(_(
                    'Insurance Number must be minimum 9 and maximum 10 characters.'))

    _sql_constraints = [
        ('email_uniq', 'unique (email)', "Email address already exists!"),
    ]

    @api.multi
    def name_get(self):
        results = super(ResPartner, self).name_get()

        results_dict = dict(results)

        for record in self:
            name_parts = results_dict[record.id].split("\n")

            name = ''
            current = record
            while current:
                name = current.name + ', ' + name
                current = current.parent_id

            name_parts[0] = name[:len(name) - 2]

            results_dict[record.id] = "\n".join(name_parts).strip()

        return list(results_dict.items())

    def _fields_sync(self, values):
        """ Sync commercial fields and address fields from company and to children after create/update,
        just as if those were all modeled as fields.related to the parent """
        # 1. From UPSTREAM: sync from parent
        if values.get('parent_id') or values.get('type', 'contact'):
            # 1a. Commercial fields: sync if parent changed
            if values.get('parent_id'):
                self._commercial_sync_from_company()

        # 2. To DOWNSTREAM: sync children
        if self.child_ids:
            # 2a. Commercial Fields: sync if commercial entity
            if self.commercial_partner_id == self:
                commercial_fields = self._commercial_fields()
                if any(field in values for field in commercial_fields):
                    self._commercial_sync_to_children()
            for child in self.child_ids.filtered(lambda c: not c.is_company):
                if child.commercial_partner_id != self.commercial_partner_id:
                    self._commercial_sync_to_children()
                    break

    @api.multi
    @api.depends(
        'parent_id',
        'level_0', 'level_1', 'level_2', 'level_3',
        'level_0.parent_id', 'level_1.parent_id', 'level_2.parent_id',
        'level_3.parent_id',
    )
    def _compute_structure(self):
        for record in self:

            values = dict.fromkeys([0, 1, 2, 3], False)

            lst = []
            current = record.parent_id
            while current:
                lst.insert(0, current.id)
                current = current.parent_id

            for i, value in enumerate(lst[:4]):
                values[i] = value

            for key, value in values.items():
                record["level_%s" % key] = value

    @api.multi
    @api.depends(
        'is_company', 'name', 'parent_id.name', 'type', 'company_name',
        'level_0', 'level_0.name', 'level_0.display_name', 'level_0.parent_id',
        'level_0.parent_id.name', 'level_0.parent_id.display_name',
        'level_1', 'level_1.name', 'level_1.display_name', 'level_1.parent_id',
        'level_1.parent_id.name', 'level_0.parent_id.display_name',
        'level_2', 'level_2.name', 'level_2.display_name', 'level_2.parent_id',
        'level_2.parent_id.name', 'level_0.parent_id.display_name',
        'level_3', 'level_3.name', 'level_3.display_name', 'level_3.parent_id',
        'level_3.parent_id.name', 'level_0.parent_id.display_name',
    )
    def _compute_display_name(self):
        super(ResPartner, self)._compute_display_name()
