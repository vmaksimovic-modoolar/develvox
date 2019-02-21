# -*- coding: utf-8 -*-
# This file is part of Odoo. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.

from odoo import models, api

taxkeys = {
    'l10n_de_skr03.tax_eu_19_purchase_skr03': 19,
    'l10n_de_skr03.tax_eu_7_purchase_skr03': 18,
    'l10n_de_skr03.tax_eu_sale_skr03': 10,
    'l10n_de_skr03.tax_export_skr03': 1,
    'l10n_de_skr03.tax_import_19_skr03': 1,
    'l10n_de_skr03.tax_import_7_skr03': 1,
    'l10n_de_skr03.tax_not_taxable_skr03': 1,
    'l10n_de_skr03.tax_ust_19_skr03': 3,
    'l10n_de_skr03.tax_ust_7_skr03': 2,
    'l10n_de_skr03.tax_vst_19_skr03': 9,
    'l10n_de_skr03.tax_vst_7_skr03': 8,
    'l10n_de_skr03.tax_ust_19_eu_skr03': 3,
    'l10n_de_skr03.tax_ust_eu_skr03': 2,
    'l10n_de_skr03.tax_free_eu_skr03': 10,
    'l10n_de_skr03.tax_free_third_country_skr03': 1,
    'l10n_de_skr03.tax_eu_19_purchase_goods_skr03': 94,
    'l10n_de_skr03.tax_eu_19_purchase_dritland_skr03': 91,
}


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.multi
    def _set_taxkeys(self, company_id):
        for key, value in taxkeys.items():
            template_id = self.env.ref(key)
            tax_id = self.env['account.tax'].search([('name', '=', template_id.name), ('company_id', '=', company_id)])
            if tax_id and tax_id.buchungsschluessel == -1:
                tax_id.update({
                    'buchungsschluessel': value,
            })