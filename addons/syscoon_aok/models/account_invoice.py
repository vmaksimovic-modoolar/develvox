# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        receiveable = False
        payable = False
        if res.partner_id:
            partner = res.partner_id
            if partner:
                if partner.company_type == 'company' or partner.company_type == 'company' and partner.type == 'contact':
                    if partner.customer and res.type in ['out_invoice', 'out_refund']:
                        partner_default_id = str(partner['property_account_receivable_id'].id)
                        default_property_id = self.env['ir.property'].search(['&', (
                            'name', '=', 'property_account_receivable_id'), ('res_id', '=', None), ('company_id', '=', self.env.user.company_id.id)])
                        if default_property_id:
                            property_id = str(default_property_id['value_reference'].split(',')[1])
                            if property_id == partner_default_id:
                                ctx = dict(self._context)
                                ctx['type'] = 'receivable'
                                receiveable, payable = self.env['res.partner'].create_accounts(res.partner_id.id, ctx)
                                if receiveable:
                                    res['account_id'] = receiveable
                    if partner.supplier and res['type'] in ['in_invoice', 'in_refund']:
                        partner_default_id = str(partner['property_account_payable_id'].id)
                        default_property_id = self.env['ir.property'].search(['&', (
                            'name', '=', 'property_account_payable_id'), ('res_id', '=', None), ('company_id', '=', self.env.user.company_id.id)])
                        if default_property_id:
                            property_id = str(default_property_id[0]['value_reference'].split(',')[1])
                            if property_id == partner_default_id:
                                ctx = dict(self._context)
                                ctx['type'] = 'payable'
                                receiveable, payable = self.env['res.partner'].create_accounts(res.partner_id.id, ctx)
                                if payable:
                                    res['account_id'] = payable
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    analytic_id_obligatory = fields.Boolean(related='account_id.analytic_id_obligatory', store=True, readonly=True, copy=False)