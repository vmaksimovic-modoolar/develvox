import pytz
import re
from datetime import datetime
import binascii
import requests
import binascii
from odoo import models, fields, api, _
import xml.etree.ElementTree as etree
from odoo.exceptions import Warning
from odoo.addons.dpd_cloud_shipping_ept.dpd_api.dpd_response import Response
import logging

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("dpd_ept", "DPD Cloud Shipping")])
    dpd_service_type = fields.Selection([('Classic', 'Classic'),
                                         ('Classic_Predict', 'Classic_Predict'),
                                         ('Classic_COD', 'Classic_COD'),
                                         ('Classic_COD_Predict', 'Classic_COD_Predict'),
                                         ('Shop_Delivery', 'Shop_Delivery'),#this service can't worked without call getParcelShopFinder() api because it was not get picking no. as ParcelShopID
                                         ('Shop_Return', 'Shop_Return'),
                                         ('Classic_Return', 'Classic_Return'),# this service can't generate label & multiple tracking number
                                         ('Express_830', 'Express_830'),
                                         ('Express_830_COD', 'Express_830_COD'),
                                         ('Express_10', 'Express_10'),
                                         ('Express_10_COD', 'Express_10_COD'),
                                         ('Express_10_COD', 'Express_10_COD'),
                                         ('Express_12', 'Express_12'),
                                         ('Express_12_COD', 'Express_12_COD'),
                                         ('Express_18', 'Express_18'),
                                         ('Express_18_COD', 'Express_18_COD'),
                                         ('Express_12_Saturday', 'Express_12_Saturday'),
                                         ('Express_12_COD_Saturday', 'Express_12_COD_Saturday'),
                                         ('Express_International', 'Express_International')], string="Service Type", help="Shipping Services those are accepted by DPD")
    dpd_shipping_label_size = fields.Selection([('PDF_A4', 'PDF_A4')
                                                , ('PDF_A6', 'PDF_A6'),
                                                ], string="Shipping Label Size",help="Different label size types.")

    dpd_shipping_language = fields.Selection([('de_DE','de_DE'), ('en_EN', 'en_EN')], string="Shipping Label Language", help="DPD Acceptable Message Language" ,default="de_DE")

    dpd_shipping_label_position = fields.Selection([
                                                    ('UpperLeft', 'UpperLeft'),
                                                    ('UpperRight', 'UpperRight'),
                                                    ('LowerLeft', 'LowerLeft'),
                                                    ('LowerRight', 'LowerRight'),
                                                    ], string="Shipping Label Position" ,help="Different label printing positions.")

    delivery_type_dpd_cloud_ept = fields.Selection(
        [('fixed_ept', 'DPD Cloud Fixed Price'), ('base_on_rule_ept', 'DPD Cloud Based on Rules')],
        string='DPD Cloud Pricing', default='fixed_ept')

    @api.onchange("delivery_type")
    def onchange_delivery_type(self):
        """If Delivery Type is dpd_local_ept than move further process.
            @param: none
            @return: Set appropriate value.
            @author: Jigar vagadiya on dated 20-July-2017.
        """
        if self.delivery_type != 'dpd_ept':
            self.delivery_type_dpd_cloud_ept = ''
        else:
            self.delivery_type_dpd_cloud_ept = 'fixed_ept'

    def dpd_ept_rate_shipment(self, order):
        """Rate API When click on set price in sale order.
            @param: Order
            @return: Set appropriate rate inside the sale order and sale order line add according to            rate.
            @author: Jigar vagadiya on dated 19-July-2017.
        """
        if self.delivery_type_dpd_cloud_ept == 'fixed_ept':
            return self.fixed_rate_shipment(order)
        if self.delivery_type_dpd_cloud_ept == 'base_on_rule_ept':
            return self.base_on_rule_rate_shipment(order)


    @api.model
    def dpd_ept_send_shipping(self, pickings):
        """ Genrate the Lable of perticular shipping service for DPD
            @param : Delivery orders.
            @return: Lable data pass in to DDP
            @author: jay makwana
        """
        response = []
        total_weight = 0.0
        for picking in pickings :

            self.check_instance_state()
            self.check_appropriate_data(picking)

            partner_id = picking.partner_id
            shipping_instance_id = self.shipping_instance_id
            total_bulk_weight = picking.weight_bulk

            master_node = etree.Element('Envelope')
            master_node.attrib['xmlns'] = "http://www.w3.org/2003/05/soap-envelope"
            sub_master_node = etree.SubElement(master_node, 'Body')
            set_order=etree.SubElement(sub_master_node, "setOrder")
            set_order.attrib['xmlns'] =  "https://cloud.dpd.com/"
            set_order_request = etree.SubElement(set_order, "setOrderRequest")
            etree.SubElement(set_order_request, "Version").text = "100"
            etree.SubElement(set_order_request, "Language").text = "%s"%(self.dpd_shipping_language)
            partner_credential = etree.SubElement(set_order_request, "PartnerCredentials")
            etree.SubElement(partner_credential, "Name").text = shipping_instance_id.partner_name or ""
            etree.SubElement(partner_credential, "Token").text = shipping_instance_id.partner_token or ""
            user_credential = etree.SubElement(set_order_request, "UserCredentials")
            etree.SubElement(user_credential, "cloudUserID").text = shipping_instance_id.cloud_user_id or ""
            etree.SubElement(user_credential, "Token").text = shipping_instance_id.user_token or ""
            etree.SubElement(set_order_request, "OrderAction").text = "startOrder"
            order_settings = etree.SubElement(set_order_request, "OrderSettings")
            current_date = datetime.strftime(datetime.now(pytz.utc), "%Y-%m-%dT%H:%M:%S")
            # current_date="2018-07-25T11:02:10"
            etree.SubElement(order_settings, "ShipDate").text = "%s" % (current_date)
            etree.SubElement(order_settings, "LabelSize").text = self.dpd_shipping_label_size
            etree.SubElement(order_settings, "LabelStartPosition").text = self.dpd_shipping_label_position
            order_data_lists = etree.SubElement(set_order_request, "OrderDataList")
            for package in picking.package_ids:
                total_weight = package.shipping_weight
                #add condition for check package has shipping weight or not
                if total_weight:
                    self.create_packages(order_data_lists,picking, total_weight,package.name)
                else:
                    error = "Please Enter the shipping weight for : %s " % (package.name)
                    raise Warning(_(error))

            if total_bulk_weight:
                package=1
                self.create_packages(order_data_lists, picking, total_bulk_weight,package)

            headers = {"Content-Type": "application/soap+xml","SOAPAction":"https://cloud.dpd.com/setOrder"}
            request_data = etree.tostring(master_node).decode('utf-8')
            url = self.shipping_instance_id.dpd_url

            try:
                _logger.info("DPD Cloud Shipment Request: %s" % (request_data))
                response_body = requests.request("POST",url=url, data=request_data, headers=headers)
            except Exception as e:
                raise Warning(_(e))

            if response_body.status_code != 200:
                error = "Error Code : %s - %s" % (response_body.status_code, response_body.reason)
                raise Warning(_(error))

            api = Response(response_body)
            result = api.dict()
            _logger.info("DPD Cloud Shipment Response: %s" %(result ))
            set_order_response=result.get('Envelope',{}).get('Body',{}).get('setOrderResponse',{}).get('setOrderResult',{})
            final_tracking_no = []
            ack = set_order_response.get('Ack', {})
            if ack == "false":
                raise Warning(_(set_order_response))
            if set_order_response:

                labelresponse = set_order_response.get('LabelResponse').get('LabelPDF')
                label_binary_data = binascii.a2b_base64(str(labelresponse))

                lable_data_list = set_order_response.get('LabelResponse').get('LabelDataList').get('LabelData')
                if isinstance(lable_data_list , dict):
                    lable_data_list = [lable_data_list ]
                    
                #add for multiple tracking number generate when there is multiple package available                    
                for lable_list in lable_data_list:
                    tracking_no = lable_list.get('ParcelNo')
                    message_ept = (_("Shipment created!<br/> <b>Shipment Tracking Number : </b>%s") % (tracking_no))
                    final_tracking_no.append(tracking_no)
                
                #add condition for classic_return service because in that can't generate label    
                if labelresponse:
                    picking.message_post(body=message_ept, attachments=[
                    ('DPD Label-%s.%s' % (tracking_no, "pdf"), label_binary_data)])
            else :
                raise Warning(_("Response Data : %s")%(set_order_response))
            shipping_data = {
                 'exact_price':0.0,
                 'tracking_number':",".join(final_tracking_no)}
            response += [shipping_data]
        return response

    @api.multi
    def create_packages(self,order_data_list,picking,weight,package):
        def _partner_split_name(partner_name):
            return [' '.join(partner_name.split()[:-1]), ' '.join(partner_name.split()[-1:])]

        partner_id=picking.partner_id
        order_data = etree.SubElement(order_data_list,"OrderData")
        ship_address = etree.SubElement(order_data, "ShipAddress")

        parent_id_exists=False
        parent_id=picking.partner_id

        company_name=""
        while(not parent_id_exists):
            if parent_id and parent_id.parent_id:
                parent_id = parent_id.parent_id
            else:
                company_name = parent_id.name
                parent_id_exists=True

        etree.SubElement(ship_address, "Company").text ='' if company_name == picking.partner_id.name else company_name
        etree.SubElement(ship_address, "Salutation").text = ""

        etree.SubElement(ship_address, "Name").text =picking.partner_id.name
        etree.SubElement(ship_address, "FirstName").text =""
        etree.SubElement(ship_address, "LastName").text =""
        # etree.SubElement(ship_address, "FirstName").text =  "%s" % \
        # _partner_split_name(partner_name)[0] if _partner_split_name(partner_name)[0] else _partner_split_name(partner_name)[1]
        #
        # etree.SubElement(ship_address, "LastName").text =  "%s" % \
        # _partner_split_name(partner_name)[1] if _partner_split_name(partner_name)[0] else _partner_split_name(partner_name)[1]
        house_number = re.search(r'\d{1,5}', partner_id.street)
        house_number = str(house_number.group()) if house_number else ""
        address_line1 = partner_id.street or ""
        etree.SubElement(ship_address, "Street").text = "%s %s" % (
        address_line1.replace(house_number, ''), partner_id.street2) if partner_id.street2 else address_line1.replace(house_number, '')
        etree.SubElement(ship_address, "HouseNo").text = house_number
        etree.SubElement(ship_address, "Country").text = partner_id.country_id and partner_id.country_id.code or ""
        etree.SubElement(ship_address, "ZipCode").text = partner_id.zip
        etree.SubElement(ship_address, "City").text = partner_id.city
        etree.SubElement(ship_address, "State").text = partner_id.state_id and partner_id.state_id.code
        etree.SubElement(ship_address, "Phone").text = partner_id.phone or ""
        etree.SubElement(ship_address, "Mail").text = partner_id.email or ""
        etree.SubElement(order_data, "ParcelShopID").text = "%s"%(picking.id)
        parcel_data = etree.SubElement(order_data, "ParcelData")
        etree.SubElement(parcel_data, "ShipService").text = self.dpd_service_type
        etree.SubElement(parcel_data, "Weight").text = "%s" % (weight)
        etree.SubElement(parcel_data, "Content").text = picking.note or picking.origin or ""
        etree.SubElement(parcel_data, "YourInternalID").text = "%s" % (picking.id)
        etree.SubElement(parcel_data, "Reference1").text = "%s" % (package)

    @api.multi
    def dpd_ept_get_tracking_link(self, pickings):
        """ Tracking the shipment from DPD
            @param: Delivery Orders.
            @return: Redirect from DPD site
            @author: Jay Makwana
        """
        res = ""
        for picking in pickings:
                link = picking.carrier_id and picking.carrier_id.shipping_instance_id and picking.carrier_id.shipping_instance_id.tracking_link or "https://tracking.dpd.de/parcelstatus?query="
                tracking_no_lists = str(picking.carrier_tracking_ref)
                tracking = tracking_no_lists.replace(',', '&')
                res = res + '%s%s' % (link, tracking)
        return res

    @api.multi
    def check_instance_state(self):
        '''Check the instance and method are active or not.
            @return:Generate the warning instance and method are active or not.
            @author: Jay makwana
        '''
        if self.shipping_instance_id.active != True:
            raise Warning(_("Shipping instance inactive !"))
        if self.active != True:
            raise Warning(_("Delivery method inactive !"))

    @api.multi
    def check_appropriate_data(self, picking):
        """ When data is incorrect genrate the error and check data is appropriate or not.
            @param : picking
            @return: Incorrect data than error want to genrate.
            @author: Jay Makwana.
        """
        for picking_id in picking.move_lines:
            if picking_id.product_id.weight == 0:
                error = "Enter the product weight : %s " % (picking_id.product_id.name)
                raise Warning(_(error))

        missing_value = self.validating_address(picking.partner_id)
        if missing_value:
            fields = ", ".join(missing_value)
            raise Warning(_("Missing the values of the Customer address. \n Missing field(s) : %s  ") % fields)

        # validation shipper address
        missing_value = self.validating_address(picking.picking_type_id.warehouse_id.partner_id)
        if missing_value:
            fields = ", ".join(missing_value)
            raise Warning(_("Missing the values of the Warehouse address. \n Missing field(s) : %s  ") % fields)

        return True

    @api.multi
    def validating_address(self, partner, additional_fields=[]):
        """ Check the Address when validate the sale order
            @param : address information
            @return: Check the sale order address .
            @author: Jay Makwana
        """
        missing_value = []
        mandatory_fields = ['country_id', 'city', 'zip']
        mandatory_fields.extend(additional_fields)
        if not partner.street and not partner.street2:
            mandatory_fields.append('street')
        for field in mandatory_fields:
            if not getattr(partner, field):
                missing_value.append(field)
        return missing_value