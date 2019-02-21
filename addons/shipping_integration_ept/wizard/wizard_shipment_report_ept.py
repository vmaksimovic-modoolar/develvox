# Copyright (c) 2017 Emipro Technologies Pvt Ltd (www.emiprotechnologies.com). All rights reserved.
import time
from odoo import models, fields, api, _

class ShipmentReportEpt(models.TransientModel):
    _name = "shipment.report.ept"
    
    from_date = fields.Datetime('From')
    to_date = fields.Datetime('To')
    carrier_id = fields.Many2one('delivery.carrier', string="Carrier") 
    
    @api.multi
    def get_report_action(self):
        """To get the wizard data and print the report
        @return : return report
        """
        data = self.read()[0]    
        datas = {
            'ids': self._ids,
            'model': 'shipment.report.ept',
            'form': data,
            'docs':self
        }            
        shipment_id = self._context.get('active_id')        
        shipment_obj = self.env['shipping.instance.ept'].browse(shipment_id)        
        return self.env.ref('shipping_integration_ept.shipping_instance_report_ept').report_action(shipment_obj,data=datas)        