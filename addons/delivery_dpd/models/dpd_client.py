# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016-TODAY Steigend IT Solutions
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
import time
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT,ustr
#from urllib2 import Request, urlopen, URLError, quote
from urllib import request, error, parse#, urlopen, URLError
from urllib.request import urlopen
from urllib.error import URLError
from urllib.parse import quote
import json
from odoo import fields, _
from odoo.exceptions import except_orm, ValidationError

import requests
import re
import logging
_logger = logging.getLogger(__name__)


class DPDProvider():

    def __init__(self,access_details={}, test_mode=True):
        self.url = False
        test_url = 'https://cloud-stage.dpd.com/api/v1/'
        production_url = 'https://cloud.dpd.com/api/v1/'
        if test_mode:
            self.url = test_url +'setOrder'
            self.zipurl = test_url +'ZipCodeRules'
            self.parcelshopurl = test_url + 'ParcelShopFinder'
        else:
            self.url = production_url +'setOrder'
            self.zipurl = production_url +'ZipCodeRules'
            self.parcelshopurl = production_url + 'ParcelShopFinder'

        #rest_url ='https://cloud-stage.dpd.com/api/v1/ParcelLifeCycle/09980525377734'##
        
        self.headers = {
            'Content-type': 'application/json', 
            'Version':'100','Language':'en_EN',
            'PartnerCredentials-Name': not test_mode and access_details.get('live_partner_name','') or \
                        access_details.get('partner_name',''),
            'PartnerCredentials-Token': not test_mode and access_details.get('live_partner_token','') or \
                        access_details.get('partner_token',''),
            'UserCredentials-cloudUserID': not test_mode and access_details.get('live_user_id','') or \
                        access_details.get('user_id',''),
            'UserCredentials-Token': not test_mode and access_details.get('live_user_token','') or \
                        access_details.get('user_token','')
        }
        self.client = requests.session()

#     def _convert_weight(self, weight, weight_unit):
#         if weight_unit == "LB":
#             return round(weight * 2.20462, 3)
#         else:
#             return round(weight, 3)

    def rate_request(self, order, carrier):
        # DHL DE does not provide rate request api, so returning price as zero
        dict_response = {'price': 0.0,
                         'currency': order.currency_id.name,
                         'error_found': False}
        return dict_response
    
    
    def get_order_action(self, picking,carrier,OrderActionType='startOrder'):
#         Enumeration of different order start types.
#         Possible:
#         . startOrder (Order start)
#         . checkOrderData (Order check only)
        return OrderActionType
        
    def get_shipping_date(self, shipping_date):
        response = self.client.get(url=self.zipurl, headers=self.headers)
        zipdetails = response.json()
        if not shipping_date or shipping_date < fields.Datetime.now():
            shipping_date = fields.Datetime.now()
        ZipCodeRules = zipdetails.get('ZipCodeRules',{}) or {}
        NoPickupDays = ZipCodeRules.get('NoPickupDays','')
        ship_date = datetime.strptime(shipping_date,DEFAULT_SERVER_DATETIME_FORMAT).date()
        if ship_date.weekday() == 6:
            ship_date += timedelta(days=1)
        if NoPickupDays:
            nopickupdays = []
            for nopickupday in NoPickupDays.split(','):
                nopickupdays.append(datetime.strptime(nopickupday,'%d.%m.%Y').date())
            while True:
                if ship_date in nopickupdays:
                    ship_date += timedelta(days=1)
                else:
                    break
        return ship_date and ship_date.strftime(DEFAULT_SERVER_DATE_FORMAT) or ''
    
    def get_order_settings(self, picking, carrier):
#         Shipping date
#         (Format: dd.mm.yyyy)
#         Note:
#         No parcel pick-up on Sunday and public holidays.
#         You get a list of valid ship days for a zip code using
#         „getZipCodeRules“.
#         Possible values:
#         . UpperLeft
#         . UpperRight
#         . LowerLeft
#         . LowerRight
        res = { "ShipDate": self.get_shipping_date(picking.date_done),# and picking.date_done > fields.Datetime.now() and picking.date_done.split(' ')[0] or fields.Date.today(),
                "LabelSize":carrier.dpd_label_size, 
                "LabelStartPosition":carrier.dpd_label_start_position}
        return res
        
    def _split_address(self, address,street_name=False):
        street_number = False
        address = address.strip()
        if address.isdigit():
            street_number = address
            return street_name, street_number
        street_split = address.split()
        if len(street_split) > 1:
            if street_split[-1].isdigit():
                street_number = street_split.pop()
                street_name = ' '.join(street_split)
            elif street_split[0].isdigit():
                street_number = street_split.pop(0)
                street_name = ' '.join(street_split)
            else:
                street_name = ' '.join(street_split)
#         else:
#             street_name = address
        #need to remove the top part in the future
        if not street_number: 
            street_split = address.split('.')
            if len(street_split) > 1:
                if street_split[-1].isdigit():
                    street_number = street_split.pop()
                    street_name = '.'.join(street_split)
                elif street_split[0].isdigit():
                    street_number = street_split.pop(0)
                    street_name = '.'.join(street_split)
                else:
                    street_name = ' '.join(street_split)
        if not street_number:
            nstreet_split = re.findall(r'^(\D+)[\s\.]([\d\-\s]+(\s*[^\d\s]+)*)$', address)
            if nstreet_split:
                street_split = list(nstreet_split[0])
                street_split.pop()
                street_number = street_split.pop()
                street_name = ' '.join(street_split)
        if not street_number:
            nstreet_split = re.findall(r'^([\d\-\s]+)\s(\D+(\s*[^\d\s]+)*)$', address)
            if nstreet_split:
                street_split = list(nstreet_split[0])
                street_split.pop()#3items,last one is the street abrivations
                street_number = street_split.pop(0)
                street_name = ' '.join(street_split)
                #street_number = street_split[1]
                #street_name = street_name and street_name + ' '+ street_split[0] or street_split[0]
        if not street_number and not street_name:
            street_name = address
        return street_name, street_number
    
    def get_street_and_house_no(self, partner):
        street_name, street_number = '', False
        company_name = ''
        if partner.street:
            street_name, street_number = self._split_address(partner.street,street_name)
            if street_name and not street_number:
                company_name = street_name
        if not street_number:
            if partner.street2:
               street_name, street_number = self._split_address(partner.street2,street_name)
        else:
            company_name = partner.street2
        return street_name, street_number,company_name
    
    def get_address(self,partner):
        street_address_details = self.get_street_and_house_no(partner)
        if not street_address_details[0]:
            raise except_orm(_('No Street Name'), _("Please add street name and street number for partner: %s "%partner.name))
        if not street_address_details[1]:
            raise except_orm(_('No Street Number'), _("Please add street number for partner: %s "%partner.name))
        if not partner.zip:
            raise except_orm(_('No Zip Code'),_("Please add zip for partner: %s "%(partner.name)))
        if not partner.country_id:
            raise except_orm(_('No Country'),_("Please add country for partner: %s "%(partner.name))) 
        if not partner.city:
            raise except_orm(_('No City'),_("Please add city for partner: %s "%(partner.name)))
        
        if not partner.email and not (partner.phone or partner.mobile):
            raise except_orm(_('No Phone number or Email'), _("Please add phone number or email for partner: %s "%partner.name))
        res = {
            "Company":street_address_details[2] or (partner.parent_id and partner.parent_id.name) or '',
            "Salutation":partner.title and (partner.title.shortcut or partner.title.name) or '',
            "Name":ustr(partner.name[:35].strip()),#.encode('utf8')),
            "Street":ustr(street_address_details[0][:35].strip()),#.encode('utf8'),
#             "Luitpoldstr.",
            "HouseNo":street_address_details[1],
            "ZipCode": ustr(partner.zip.strip()),#.encode('utf8'),
            "City":ustr(partner.city[:35].strip()),#.encode('utf8'),
            "Country":partner.country_id.code, 
#             "State":partner.state_id.code, State ISO3166-2: exactly 2 characters.
        }
        
        if partner.phone or partner.mobile:
            res.update({"Phone":(partner.phone and ustr(partner.phone[:20].strip())) or (partner.mobile and ustr(partner.mobile[:20].strip())) or "" })
        if partner.email:
            res.update({"Mail":ustr(partner.email.strip())})#.encode('utf8')
        return res
        
    def get_cod_details(self, picking):#TODO
        return {}
    
    def get_product_name(self,picking):
        name = ""
        for move in picking.move_lines:
            name = move.product_id.name or ""
            break
        return name
    
    def get_parcel_data(self, picking, carrier):
        if picking.weight and picking.weight > 31.5:
            raise except_orm(_('Over Weight'), _("Weight must be less than 31.5Kg "))
        res = {
            "YourInternalID": picking.origin and picking.origin[:35] or picking.name[:35],
            "Content": self.get_product_name(picking)[:35] or "Cloths",#[:35]
            "Weight": picking.weight or 1.0,
            "Reference1": picking.partner_id.email and picking.partner_id.email[:35] or "",
            "Reference2": picking.name[:35], 
            "ShipService": carrier.dpd_ship_service
        }
        if not picking.partner_id.email:
            raise except_orm(_('Email'), _("Please specify an email for the customer "))
        res.update(self.get_cod_details(picking))
        return res
    
    def get_parcel_shop(self, picking, carrier): 
        return getattr(picking.group_id, 'parcelshop_id', 0)
    
    def getorder_data(self, picking, carrier):
        res = {
            "ParcelShopID":self.get_parcel_shop(picking, carrier),
            "ShipAddress":self.get_address(picking.partner_id),
            "ParcelData": self.get_parcel_data(picking, carrier),
            
        }
        return res
    
    def create_shipmentorder(self, picking, carrier):
        res = {
            "OrderDataList":[self.getorder_data(picking,carrier)],
            "OrderAction":self.get_order_action(picking,carrier),
            "OrderSettings": self.get_order_settings(picking,carrier),
            
        }
        return res
    
    def validate_shipping(self, picking, carrier):
        res = {
            "OrderDataList":[self.getorder_data(picking,carrier)],
            "OrderAction":self.get_order_action(picking,carrier,OrderActionType='checkOrderData'),
            "OrderSettings": self.get_order_settings(picking,carrier),
            
        }
        order_data_json = json.dumps(res)
        data =  order_data_json
        return self.client.post(url=self.url, data=data, headers=self.headers)
    
    def create_shipment(self, picking, carrier):
        order_data = self.create_shipmentorder(picking, carrier)
#         order_data_dict = dict(self.auth_data,**order_data)
        order_data_dict = order_data
        order_data_json = json.dumps(order_data_dict)
        data =  order_data_json
        return self.client.post(url=self.url, data=data, headers=self.headers)
    
    def shop_finder_url(self, order, carrier, max_return_values, search_mode):
        # SearchByGeoData
        # https://cloud-stage.dpd.com/api/v1/ParcelShopFinder/{MaxReturnValues}/{Longitude}/{Latitude}/{NeedService}/{HideOnClosedAt}
        # SearchByAddressData
        # https://cloud-stage.dpd.com/api/v1/ParcelShopFinder/{MaxReturnValues}/{Street}/{HouseNo}/{ZipCode}/{City}/{Country}/{NeedService}/{HideOnClosedAt}
        res = ""
        if search_mode == "SearchByAddress":
            street_address_details = self.get_street_and_house_no(order.partner_shipping_id)
            res = '/{}/{}/{}/{}/{}/{}/{}/{}'.format(max_return_values,
                                                    ustr(street_address_details[0][:35].strip()) or u'null',
                                                    ustr(street_address_details[1]) or u"null",
                                                    ustr(order.partner_shipping_id.zip.strip()),
                                                    ustr(order.partner_shipping_id.city[:35].strip()),
                                                    order.partner_shipping_id.country_id.code,
                                                    u'StandardService',
                                                    u'null'
                                                    )
        return res

    def get_parcelshop_finder_data(self, order, carrier):
        parcel_shop_finder_url = self.shop_finder_url(order, carrier, max_return_values=10,
                                                      search_mode="SearchByAddress")
        parcel_shop_url = self.parcelshopurl + quote(parcel_shop_finder_url)
        return self.client.get(url=parcel_shop_url, headers=self.headers)
    
     
