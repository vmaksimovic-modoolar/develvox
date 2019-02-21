# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account Reconciliation: Remove constraint on same type of account',
    'category': 'Accounting',
    'version': '1.0',
    'depends': ['account'],
    'description': """
Remove constraint on same type of account, as some countries allow that.
""",
    'data': [
        'views/res_company.xml',
        'views/account_templates.xml'
    ]
}
