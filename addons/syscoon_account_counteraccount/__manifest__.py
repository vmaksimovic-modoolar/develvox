# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Gegenkonto in Buchungszeilen',
    'version': '11.0.1.0.0',
    'author': 'syscoon GmbH',
    'category': 'Accounting',
    'website': 'https://syscoon.com',
    'depends': [
        'account',
    ],
    'description': """Blendet das Gegenkonto in den Buchungszeilen ein""",
    'data': [
        'views/account.xml',
    ],
    'init_xml': [],
    'demo_xml': [],
    'update_xml': [],
    'installable': True
}
