#See LICENSE file for full copyright and licensing details.

{
    'name': 'Partner Debitoren- / Kreditorenkonto',
    'version': '11.0.2.0.2',
    'author': 'ecoservice, syscoon GmbH',
    'category': 'Accounting',
    'website': 'https://syscoon.com',
    'depends': [
        'base',
        'account'
    ],
    'description': """If a partner is created a new debit and credit account will be created following a 
    sequence that can be created individually per company.""",
    'init_xml': [],
    'demo_xml': [],
    'data': [
        'data/ecoservice_partner_auto_account_company_data.xml',
        'views/ecoservice_partner_auto_account_company_views.xml',
        'security/ir.model.access.csv',
    ],
    'active': False,
    'installable': True
}
