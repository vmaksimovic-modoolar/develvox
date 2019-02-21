from odoo import api, models
from odoo.exceptions import UserError
from datetime import datetime
class report_shipping_instance_parser(models.AbstractModel):
    _name = 'report.shipping_integration_ept.report_shipping_instance_ept'

    @api.model
    def get_report_values(self, docids, data):   
        docids = data.get('context').get('active_ids')     
        docs = self.env['shipping.instance.ept'].browse(docids)                        
        return {
            'doc_ids': docids,
            'doc_model': 'shipping.instance.ept',
            'docs': docs,
            'data': data,
            'display_delivery_method': self.display_delivery_method,
            'display_stock_picking_attribute': self.display_stock_picking_attribute,
        }
    @api.multi
    def display_delivery_method(self,data):
        """Give delivery carrier name according to shipping_instance_id
           @param: data contains wizard data
           @return: delivery carrier name        
        """  
        delivery_carrier = data.get('form').get('carrier_id')
        if delivery_carrier:                        
            services = self.env['delivery.carrier'].browse(delivery_carrier[0])                
        else:
            shipping_instance_id = data.get('context').get('active_ids')       
            shipping_services_obj = self.env['delivery.carrier']
            services = shipping_services_obj.search([('shipping_instance_id','=',shipping_instance_id)])            
        return services
    
    @api.multi
    def display_stock_picking_attribute(self,id,data):
        """Filter the stock picking data according to carrier_id
           @param: id of delivery_carrier,data contains wizard data
           @return: stock_picking obj with such filter        
        """        
        from_date = data.get('form').get('from_date')
        to_date = data.get('form').get('to_date')                        
        picking_obj = self.env['stock.picking']        
        order_information = picking_obj.search([('carrier_id','=',id),('state','=',"done"),('carrier_tracking_ref' ,'!=',False),('scheduled_date','>=',from_date),('scheduled_date','<=',to_date)])                            
        return order_information