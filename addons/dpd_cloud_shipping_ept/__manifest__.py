# -*- coding: utf-8 -*-
{

    # App information

    'name': 'DPD Cloud Odoo Shipping Connector',
    'category': 'Website',
    'version': '11.0',
    'summary': 'DPD Cloud Odoo Shipping Connector helps to connect Odoo with DPD Cloud and manage your Shipping operations directly from Odoo.',
    'license': 'OPL-1',
    
    # Dependencies
    'depends': ['shipping_integration_ept'],

    # Views

    'data': [
            'views/view_shipping_instance_ept.xml',
            'views/delivery_carrier_view.xml',
            ],

    # Odoo Store Specific
    'images': ['static/description/DPD_Cloud_Cover.jpg'],     

    # Author

    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',

    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url':'http://www.emiprotechnologies.com/free-trial?app=dpd-cloud-shipping-ept&version=11&edition=enterprise',
    'price': '149',
    'currency': 'EUR',

}
