##############################################################################
#
# Copyright (c) 2018 - Now Modoolar (http://modoolar.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract support@modoolar.com
#
##############################################################################

{
    'name': "AOK Extension",
    'category': "Sales",
    'version': "0.3",
    'author': 'Modoolar',
    'website': 'https://www.modoolar.com',
    'depends': [
        'partner_firstname',
    ],
    'description': """
    This is my first module created for odoo SH
""",
    'data': [
        'views/res_partner_view.xml',
    ],
    'demo': [
    ],
    'qweb': [
        'static/src/xml/activity.xml',
    ],
}
