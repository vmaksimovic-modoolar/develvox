#See LICENSE file for full copyright and licensing details.

{
    'name': 'Finanzinterface - Datev ASCII Export',
    'version': '11.0.2.0.3',
    'depends': [
        'syscoon_financeinterface'
    ],
    'author': 'ecoservice, syscoon GmbH',
    'website': 'https://syscoon.com',
    'summary': 'Export of account moves to Datev',
    'description': """The module account_financeinterface_datev provides methods to convert account moves to the Datevformat (Datev Dok.-Nr.: 1036228).""",
    'category': 'Accounting',
    'data': [
        'views/account_view.xml',
        'data/account_cron.xml',
        'views/res_company_view.xml',
        'views/account_invoice_view.xml',
    ],
    'active': False,
    'installable': True
}
