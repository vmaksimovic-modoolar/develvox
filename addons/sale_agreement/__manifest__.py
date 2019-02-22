# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sales Agreement',
    'category': 'Sales',
    'version': "0.2",
    'sequence': 60,
    'summary': 'Sales Agreement',
    'description': "",
    'website': 'https://www.odoo.com/',
    'depends': ['sale_stock'],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/sale_agreement_views.xml',
        'report/sale_agreement_templates.xml',
        'report/sale_agreement_report.xml',

    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
