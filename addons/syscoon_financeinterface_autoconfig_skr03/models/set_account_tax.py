# -*- coding: utf-8 -*-
# This file is part of Odoo. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from odoo import models, api


autoaccounts = {
    'l10n_de_skr03.account_1518': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_1718': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_2406': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_2408': ['l10n_de_skr03.tax_ust_19_eu_skr03'],
    'l10n_de_skr03.account_2436': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_3010': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3030': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3060': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3060': ['l10n_de_skr03.tax_eu_7_purchase_skr03'],
    'l10n_de_skr03.account_3062': ['l10n_de_skr03.tax_eu_19_purchase_skr03'],
    'l10n_de_skr03.account_3091': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3092': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3106': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3108': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3123': ['l10n_de_skr03.tax_eu_19_purchase_goods_skr03'],
    'l10n_de_skr03.account_3125': ['l10n_de_skr03.tax_eu_19_purchase_dritland_skr03'],
    'l10n_de_skr03.account_3150': ['l10n_de_skr03.tax_eu_19_purchase_dritland_skr03', 'l10n_de_skr03.tax_eu_19_purchase_goods_skr03'],
    'l10n_de_skr03.account_3151': ['l10n_de_skr03.tax_eu_19_purchase_dritland_skr03', 'l10n_de_skr03.tax_eu_19_purchase_goods_skr03'],
    'l10n_de_skr03.account_3300': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3400': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3420': ['l10n_de_skr03.tax_eu_7_purchase_skr03'],
    'l10n_de_skr03.account_3425': ['l10n_de_skr03.tax_eu_19_purchase_skr03'],
    'l10n_de_skr03.account_3430': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_3435': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_3440': ['l10n_de_skr03.tax_eu_19_purchase_skr03'],
    'l10n_de_skr03.account_3553': ['l10n_de_skr03.tax_eu_19_purchase_skr03'],
    'l10n_de_skr03.account_3710': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3714': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3715': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3717': ['l10n_de_skr03.tax_eu_7_purchase_skr03'],
    'l10n_de_skr03.account_3718': ['l10n_de_skr03.tax_eu_19_purchase_skr03'],
    'l10n_de_skr03.account_3720': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3724': ['l10n_de_skr03.tax_eu_7_purchase_skr03'],
    'l10n_de_skr03.account_3725': ['l10n_de_skr03.tax_eu_19_purchase_skr03'],
    'l10n_de_skr03.account_3731': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3734': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3736': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3738': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3741': ['l10n_de_skr03.tax_eu_19_purchase_skr03'],
    'l10n_de_skr03.account_3743': ['l10n_de_skr03.tax_eu_7_purchase_skr03'],
    'l10n_de_skr03.account_3744': ['l10n_de_skr03.tax_eu_19_purchase_skr03'],
    'l10n_de_skr03.account_3750': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3754': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3755': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3760': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3780': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3784': ['l10n_de_skr03.tax_vst_7_skr03'],
    'l10n_de_skr03.account_3785': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3790': ['l10n_de_skr03.tax_vst_19_skr03'],
    'l10n_de_skr03.account_3792': ['l10n_de_skr03.tax_eu_19_purchase_skr03'],
    'l10n_de_skr03.account_3793': ['l10n_de_skr03.tax_eu_19_purchase_skr03'],
    'l10n_de_skr03.account_8191': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8196': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8300': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8310': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8315': ['l10n_de_skr03.tax_ust_19_eu_skr03'],
    'l10n_de_skr03.account_8400': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8516': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8519': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8576': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8579': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8591': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8595': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8611': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8613': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8630': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8640': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8710': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8720': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8724': ['l10n_de_skr03.tax_eu_sale_skr03'],
    'l10n_de_skr03.account_8725': ['l10n_de_skr03.tax_ust_eu_skr03'],
    'l10n_de_skr03.account_8726': ['l10n_de_skr03.tax_ust_19_eu_skr03'],
    'l10n_de_skr03.account_8731': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8736': ['l10n_de_skr03.tax_ust_19_eu_skr03'],
    'l10n_de_skr03.account_8741': ['l10n_de_skr03.tax_free_third_country_skr03'],
    'l10n_de_skr03.account_8742': ['l10n_de_skr03.tax_free_eu_skr03'],
    'l10n_de_skr03.account_8743': ['l10n_de_skr03.tax_eu_sale_skr03'],
    'l10n_de_skr03.account_8746': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8748': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8750': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8760': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8780': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8790': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8801': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8820': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8910': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8915': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8920': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8921': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8922': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8925': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8930': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8932': ['l10n_de_skr03.tax_ust_7_skr03'],
    'l10n_de_skr03.account_8935': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8940': ['l10n_de_skr03.tax_ust_19_skr03'],
    'l10n_de_skr03.account_8945': ['l10n_de_skr03.tax_ust_7_skr03'],
}


class AccountAccount(models.Model):
    _inherit = 'account.account'

    def _set_account_autoaccount(self, company_id):
        for key, values in autoaccounts.items():
            template_id = self.env.ref(key)
            account_id = self.env['account.account'].search([('name', '=', template_id.name), ('company_id', '=', company_id)])
            if account_id and not account_id.automatic:
                tax_keys = []
                for value in values:
                    tax_templ_id = self.env.ref(value)
                    tax_id = self.env['account.tax'].search([('name', '=', tax_templ_id.name), ('company_id', '=', company_id)])
                    if tax_id:
                        tax_keys.append(tax_id.id)
                account_id.update({
                    'automatic': True,
                    'datev_steuer': [(6, 0, tax_keys)],
                    'datev_steuer_erforderlich': True,
                })
                