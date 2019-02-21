# -*- coding: utf-8 -*-
#See LICENSE file for full copyright and licensing details.

{
    'name': 'AOK Anpassung zur Debitoren- / Kreditorenkonto Automatik',
    'version': '11.0.1.0.3',
    'author': 'syscoon GmbH',
    'category': 'Accounting',
    'website': 'https://syscoon.com',
    'depends': [
        'syscoon_partner_account_company_automatic',
        'account_bank_statement_import_camt',
    ],
    'description': """""",
    'data': [
        'views/account_account.xml',
        'views/account_invoice.xml',
    ],
    'init_xml': [],
    'demo_xml': [],
    'update_xml': [],
    'active': False,
    'installable': True
}
