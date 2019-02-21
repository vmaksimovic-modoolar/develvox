# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016-TODAY Steigend IT Solutions
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
from .dpd_client import DPDProvider

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    dpd_label_name = fields.Char('DPD Label File Name',copy=False)
    dpd_label_bin = fields.Binary('DPD Label',copy=False)
     
class ProviderDPD(models.Model):
    _inherit = 'delivery.carrier'


    delivery_type = fields.Selection(selection_add=[('dpd', "DPD")])
    dpd_partner_name = fields.Char(string="Partner Name", groups="base.group_system", help="Partner Name from the sandbox access data",)
    dpd_partner_token = fields.Char(string="Partner Token", groups="base.group_system", help="Partner Token from the sandbox access data",)
    dpd_live_partner_name = fields.Char(string="Partner Name", groups="base.group_system", help="Partner Name from the live access data",)
    dpd_live_partner_token = fields.Char(string="Partner Token", groups="base.group_system", help="Partner Token from the live access data",)
    dpd_user_id = fields.Char(string="Cloud User ID", groups="base.group_system", help="Cloud User ID from the sandbox access data",)
    dpd_user_token = fields.Char(string="User Token", groups="base.group_system", help="User Token from the sandbox access data",)
    dpd_live_user_id = fields.Char(string="Cloud User ID", groups="base.group_system", help="Cloud User ID for the live access data",)
    dpd_live_user_token = fields.Char(string="User Token", groups="base.group_system", help="User Token for the live access data",)
    dpd_label_size = fields.Selection([('PDF_A4','A4'),('PDF_A6','A6'),
                                       ('ZPL_A6','ZPL_A6(not supported)')],'PDF Format Size', default = 'PDF_A4')
    dpd_label_start_position = fields.Selection([('UpperLeft','Upper Left'),('UpperRight','Upper Right'),
                                                 ('LowerLeft','Lower Left'),('LowerRight','Lower Right')],
                                                'PDF Label Start Position', default = 'UpperLeft')
    
    dpd_ship_service = fields.Selection(list(map(lambda x:(x,x),('Classic','Classic_Predict','Classic_COD',\
                                                                 'Classic_COD_Predict','Shop_Delivery','Shop_Return',\
                                                                 'Classic_Return','Express_830','Express_830_COD',\
                                                                 'Express_10','Express_10_COD','Express_12',\
                                                                 'Express_12_COD','Express_18','Express_18_COD'))),\
                                                 'DPD Ship Service Type', default = 'Classic')
    dpd_shipping_cost = fields.Float('Fixed Shipping Cost',help='As DPD doesnot provide the shipping cost, you can manually specify the shipping price here.')
 
    def dpd_rate_shipment(self, order):
        res = {}
        if self.delivery_type == 'dpd':
            res['price'] = self.dpd_shipping_cost or 0.0
            res['success'] = True
            res['warning_message'] = ''
            res['error_message'] = ''
        else:
            res['price'] = 0.0           
        return res



#     @api.one
#     def get_price(self):
#         super(ProviderDPD, self).get_price()
#         if self.delivery_type == 'dpd' and not self.price:
#             self.price = self.dpd_shipping_cost * (1.0 + (float(self.margin) / 100.0))

    def dpd_access_details(self):
        return {
            'partner_name': self.dpd_partner_name,
            'partner_token':self.dpd_partner_token,
            'live_partner_name': self.dpd_live_partner_name,
            'live_partner_token':self.dpd_live_partner_token,
            'user_id':self.dpd_user_id,
            'user_token':self.dpd_user_token,
            'live_user_id': self.dpd_live_user_id,
            'live_user_token':self.dpd_live_user_token,
        }
        
    def dpd_send_shipping(self, pickings):
        res = []
        access_details = self.dpd_access_details()
        srm = DPDProvider(access_details, test_mode=not self.prod_environment)
        for picking in pickings:
            shipping_data = {
                'tracking_number': "",
                'dhl_paket_label_url': "",
                'exact_price': 0.0
            }
            response = srm.validate_shipping(picking, self)
            resp = response.json()
            if resp.get('ErrorDataList',False):
                logmessage = "An error occured."
                logmessage += "\nFull Response:%s\n"%resp.get('ErrorDataList',False)
                picking.message_post(body=logmessage) 
                res = res + [shipping_data]
                return res 
            response = srm.create_shipment(picking, self)
            resp = response.json()
            dhl_paket_label_url = ""
            if not resp.get('ErrorDataList',False):
                parcel_no = resp.get('LabelResponse',False) and resp['LabelResponse'].get('LabelDataList',False) and \
                        resp['LabelResponse']['LabelDataList'][0].get('ParcelNo','') or ''
                label_pdf = resp.get('LabelResponse',False) and resp['LabelResponse'].get('LabelPDF',False) or False
                logmessage = (_("Shipment created into DPD <br/> <b>Tracking Number(s): </b>%s") %parcel_no)
                picking.message_post(body=logmessage)
                shipping_data = {
                    'tracking_number': parcel_no,
                    'exact_price':0.0,
                    'dpd_label_bin': label_pdf
                }
                picking.dpd_label_bin = label_pdf
                picking.dpd_label_name = "DPD Label for %s.pdf"%(picking.origin or picking.name)
            else:
                if not response:
                    logmessage = (_("No Response from DPD") )
                else:
                    logmessage = "An error occured."
                    logmessage += "\nFull Response:%s\n"%resp.get('ErrorDataList',False)
                picking.message_post(body=logmessage)   
            res = res + [shipping_data]

        return res

    def dpd_get_tracking_link(self, picking):
        res = False
        self.ensure_one()
        if picking.carrier_tracking_ref:
            res = "https://tracking.dpd.de/parcelstatus?query=%s"%picking.carrier_tracking_ref
        return res
    
    def dpd_cancel_shipment(self, picking):
        logmessage = _("Shipment has been deleted")
        picking.message_post(body=logmessage)
        #picking.sale_id.message_post(bosy=logmessage)
        picking.dpd_label_bin = False
            #picking.sale_id.message_post(body=logmessage)
#             raise except_orm("Error !!!", error_message)
        return True
    
    def dpd_get_parcelshops_data(self, order):
        access_details = self.dpd_access_details()
        srm = DPDProvider(access_details, test_mode=not self.prod_environment)
        response = srm.get_parcelshop_finder_data(order, self)
        resp = response.json()
        if resp['ErrorDataList']:
            error_message = []
            errors = {}
            for error_msg in resp['ErrorDataList']:
                error_message.append(_('%s') % error_msg['ErrorMsgLong'])
            errors['error_message'] = error_message
            resp.update({'errors': errors})
        return resp

