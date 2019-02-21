#See LICENSE file for full copyright and licensing details.

{
    'name': 'Finanzinterface - DATEV Account Export',
    'description': """Exporting account data in DATEV CSV format""",
    'version': '11.0.1.0.3',
    'author': 'syscoon GmbH',
    'category': 'Accounting',
    'website': 'https://syscoon.com',
    'depends': [
        'base',
        'account',
        'syscoon_financeinterface_datev',
    ],
    'data': [
        'views/datev_export_view.xml',
        'views/partner_view.xml',
        'views/account_view.xml',
    ],
    'auto_install': False,
    'installable': True,
}
