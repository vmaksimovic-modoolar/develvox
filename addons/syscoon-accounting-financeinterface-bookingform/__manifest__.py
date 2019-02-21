#See LICENSE file for full copyright and licensing details.

{
    'name': 'Financeinterface Bookingform',
    'version': '11.0.1.0.0',
    'author': 'syscoon GmbH',
    'category': 'Accounting',
    'website': 'https://syscoon.com',
    'depends': [
        'account',
        'syscoon_financeinterface',
        'syscoon_allow_negativ_debit_credit',
    ],
    'description': """The alternative booking for accounting creates a new 
        view for creating moves. Instead of having two or more lines it is possible 
        to have account and counteraccount and a tax rate.""",
    'data': [
        'security/ir.model.access.csv',
        'views/account.xml',
        'wizards/bookingform_wizard.xml',
    ],
    'init_xml': [],
    'demo_xml': [],
    'update_xml': [],
    'installable': True
}