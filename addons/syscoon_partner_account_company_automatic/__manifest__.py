#See LICENSE file for full copyright and licensing details.

{
    'name': 'Partner Debitoren- / Kreditorenkonto Automatik',
    'version': '11.0.2.0.1',
    'author': 'ecoservice, syscoon GmbH',
    'category': 'Accounting',
    'website': 'https://syscoon.com',
    'depends': [
        'syscoon_partner_account_company',
        'sale',
        'purchase',
    ],
    'description': """If a partner is created a new debit and credit account will be created automatically.""",
    'data': [
        'views/ecoservice_partner_auto_account_company.xml',
    ],
    'init_xml': [],
    'demo_xml': [],
    'update_xml': [],
    'active': False,
    'installable': True
}
