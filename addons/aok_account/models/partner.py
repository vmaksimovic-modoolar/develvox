# -*- coding: utf-8 -*-

from odoo import api, fields, models


class InsuranceStatus(models.Model):
    _name = 'insurance.status'
    _description = "Insurance Status"

    name = fields.Char()
    code = fields.Char()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    organisation_id = fields.Many2one('res.partner', string='Organisation')
    send_list = fields.Boolean(string='Send list')
    subscription_id = fields.Many2one("sale.subscription", string="Verkauf über Abonnement")
    sub_from = fields.Date(string="Sub-Subscription From")
    sub_until = fields.Date(string="Sub-Subscription Until")
    insured_number = fields.Char("Insured Number")
    insurance_status = fields.Many2one("insurance.status", string="Insurance Status")
    birth_date = fields.Date("Birth Date")

    @api.depends('is_company', 'parent_id.commercial_partner_id', 'organisation_id')
    def _compute_commercial_partner(self):
        for partner in self:
            if partner.is_company or not partner.parent_id:
                partner.commercial_partner_id = partner.organisation_id or partner
            else:
                partner.commercial_partner_id = partner.organisation_id or partner.parent_id.commercial_partner_id


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    contacts = fields.One2many("res.partner", "subscription_id", string="Unterbezieher")
