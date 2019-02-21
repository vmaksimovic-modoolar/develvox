# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016-TODAY Steigend IT Solutions
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
{
    'name': "Dynamic Parcel Distribution (DPD) Shipping",
    'summary':"Dynamic Parcel Distribution (DPD) - ODOO Shipping Integration",
    'description': """
Dynamic Parcel Distribution (DPD) -ODOO Shipping Integration
============================================================    
Send your shipping through Dynamic Parcel Distribution (DPD) and track them online.

You need to create a new delivery method with delivery type as 'DPD' and specify the 
* DPD Partner name
* DPD Partner Token
* DPD User ID
* DPD User Token

There is ablility to print the label from ODOO.

* For Activation for Live Web service (Partner Name, Partner Token, Cloud User ID, User Token)
 
Please contact their IT team via DPD eSolutions using it@dpd.com or by using their Germany-wide hotline under 0180 6 373200*.
 
Note Within the activation you’ll receive both new webservice access data (credentials) from the webservice administration and the live URLs of the DPD Cloud Service.
 
For registering for sanbox detail
 
Register at DPD Developer https://esolutions.dpd.com/entwickler/registrieren.aspx?lng=eng

For any support contact support@steigendit.com or omalbastin@steigendit.com
    """,
    'author': "Steigend IT Solutions",
    'license': 'LGPL-3',
    'website': "https://www.steigendit.com",
    'category': 'Technical Settings',
    'version': '11.0.1.3.3',
    'depends': ['delivery', 'mail'],
    'data': [
        'views/delivery_dpd_view.xml',
    ],
    'application':True,
    'currency': 'EUR',
    'price': '125.0',
    'images': ['static/description/dpd10.png'],
    'demo': [
    ],
    
}
