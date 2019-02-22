#See LICENSE file for full copyright and licensing details.


from odoo import models, api


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_confirm(self):
        res = super(purchase_order, self).button_confirm()
        config_id = self.env['ecoservice.partner.auto.account.company'].search([('company_id', '=', self.env.user.company_id.id)])
        if config_id.create_auto_account_on == 'orders':
            partner = self.partner_id
            if partner.parent_id:
                partner = partner.parent_id
            if partner:
                partner_default_id = str(partner['property_account_payable_id'].id)
                default_property_id = self.env['ir.property'].search(['&', (
                    'name', '=', 'property_account_payable_id'), ('res_id', '=', None), ('company_id', '=', self.env.user.company_id.id)])
                if default_property_id:
                    property_id = str(default_property_id['value_reference'].split(',')[1])
                    if property_id == partner_default_id:
                        ctx = dict(self._context)
                        ctx['type'] = 'payable'
                        self.env['res.partner'].create_accounts(partner.id, ctx)
        return res

