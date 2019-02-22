# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'AOK Account',
    'category': 'Accounting',
    'version': "0.4",
    'sequence': 60,
    'summary': 'AOK Account',
    'description': "",
    'website': 'https://www.odoo.com/',
    'depends': ['account_accountant', 'account_banking_sepa_credit_transfer',
                'sale_subscription', 'project', 'account_analytic_default', 'account_asset', 'purchase', 'sale', 'stock_landed_costs'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'views/partner_views.xml',
        'data/account_asset_sequence.xml',
        'data/precision_data.xml',
        'views/account_asset_views.xml',
        'wizard/account_asset_summary_report_view.xml',
        'wizard/account_asset_detail_report_view.xml',
        'wizard/encasing_interface_view.xml',
        'views/account_invoice_views.xml',
        'views/asset_report.xml',
        'views/reports.xml',
        'report/layout_templates.xml',
        'report/report_invoice.xml',
        'report/report_sale.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
