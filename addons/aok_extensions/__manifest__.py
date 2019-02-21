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
        'sale_management',
        'purchase',
        'aok_stock',
        'aok_account',
        'web_char_domain',
        'partner_firstname',
    ],
    'description': """
    This is my first module created for odoo SH
""",
    'data': [
        'translations.sql',
        'data/default_values.xml',
        'data/sequences.xml',
        'data/email_template_data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',

        'ir/ir_qweb.xml',
        'wizard/send_new_product_wizard_view.xml',

        'views/menu.xml',
        'views/product_status.xml',
        'views/product_template_view.xml',
        'views/product_documents_view.xml',
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'views/stock_view.xml',
        'views/res_config_settings_view.xml',
        'views/sales_territory.xml',

        # 'report/report_templates.xml',
    ],
    'demo': [
    ],
    'qweb': [
        'static/src/xml/activity.xml',
    ],
}
