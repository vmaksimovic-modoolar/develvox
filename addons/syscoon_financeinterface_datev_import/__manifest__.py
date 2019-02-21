#See LICENSE file for full copyright and licensing details.

{
    'name': 'Finanzinterface - Datev ASCII Import',
    'version': '11.0.2.0.1',
    'licence': 'LGPL-3',
    'author': 'ecoservice, syscoon GmbH',
    'website': 'https://syscoon.com',
    'description': """The module ecoservice_financeinterface_datev_import allows you to import accounting entries.

Details of the module:
* Import of accounting entries
""",
    'category': 'Accounting',
    'summary': 'Import of DATEV Moves.',
    'depends': [
        'syscoon_financeinterface_datev',
    ],
    'data': [
        'views/import_datev.xml',
        'views/account_move.xml',
        'views/import_datev_config.xml',
        'views/import_datev_menu.xml',
        'data/import_config.xml',
        'data/import_datev_sequence.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
