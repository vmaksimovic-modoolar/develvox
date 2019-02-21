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
from odoo import models, api, fields,_


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    multi_sales_price_method = fields.Selection(
        selection_add=[
            ('percentage_variant', _('Multiple prices per product variant'))
        ]
    )

    sale_pricelist_setting = fields.Selection(
        selection_add=[
            ('percentage_variant', _('Multiple prices per product variant'))
        ]
    )

    group_variant_pricelist = fields.Boolean(
        string="Show pricelists On Product Variants",
        implied_group='aok_extensions.group_variant_pricelist'
    )

    @api.onchange('sale_pricelist_setting')
    def _onchange_sale_pricelist_setting_inherit(self):
        if self.sale_pricelist_setting == 'percentage_variant':
            self.update({
                'group_variant_pricelist': True,
                'group_sale_pricelist': True
            })
        else:
            self.update({
                'group_variant_pricelist': False,
                'group_sale_pricelist': True
            })

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res.update(
            multi_sales_price=res['sale_pricelist_setting'] in [
                'percentage',
                'formula',
                'percentage_variant'
            ],
            multi_sales_price_method=res['sale_pricelist_setting'] in [
                'percentage',
                'formula',
                'percentage_variant'
            ] and res['sale_pricelist_setting'] or False,

        )
        return res
