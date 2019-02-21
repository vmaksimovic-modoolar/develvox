# -*- coding: utf-8 -*-
# This file is part of Odoo. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
{
    'name': 'Finanzinterface - Automatic Configuration SKR03',
    'version': '11.0.1.0.0',
    'author': 'syscoon GmbH',
    'category': 'Accounting',
    'website': 'https://syscoon.com',
    'summary': 'Interface for DATEV Connect',
    'depends': [
        'base',
        'account',
        'syscoon_financeinterface_datev',
    ],
    'data': [
        'views/res_company.xml',
    ],
    'installable': True,
    'application': False,
}
