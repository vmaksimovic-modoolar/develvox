# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'AOK Purchase',
    'category': 'Purchases',
    'sequence': 60,
    'summary': 'AOK Purchase',
    'description': "",
    'website': 'https://www.odoo.com/',
    'depends': ['sale', 'purchase_requisition'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_requisition_views.xml',
        'views/product_views.xml',
        'views/product_attribute_views.xml',
        'report/report_purchaserequisition.xml',
    ],
    'test': [
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
