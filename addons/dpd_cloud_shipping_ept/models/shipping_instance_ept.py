from odoo import models, fields, api,_

class ShippingInstanceEpt(models.Model):
    _inherit = "shipping.instance.ept"
    
    provider = fields.Selection(selection_add=[('dpd_ept', 'DPD Cloud Shipping')])
    partner_name = fields.Char(string='Partner Name',copy=False,help ='Name of your API partner')
    partner_token = fields.Char(string='Partner Token',copy=False,help ='Token of your API partner')
    cloud_user_id = fields.Char(string='Cloud User ID / Customer ID',copy=False,help='Customer ID of the DPD customer. Assigned by DPD.' )
    user_token = fields.Char(string='User Token / Customer Password',copy=False,help='Customer password of the DPD customer. Assigned by DPD.')
    dpd_url=fields.Char(string="API URL",help="API URL indicate the host of API and It will use to the sending the request.")
    
    @api.one
    def dpd_ept_retrive_shipping_services(self, to_add):
        """ Retrieve shipping services from the DPD
            @param: Receiver Address.
            @return: list of dictionaries with shipping service
            @author: Jay Makwana
        """
        shipping_services_obj = self.env['shipping.services.ept']
        services_name = {
                        'Classic': 'Classic',
                        'Classic_Predict': 'Classic_Predict',
                        'Classic_COD': 'Classic_COD',
                        'Classic_COD_Predict': 'Classic_COD_Predict',
                        'Shop_Delivery':'Shop_Delivery',
                        'Shop_Return': 'Shop_Return',
                        'Classic_Return': 'Classic_Return',
                        'Express_830': 'Express_830',
                        'Express_830_COD': 'Express_830_COD',
                        'Express_10': 'Express_10',
                        'Express_10_COD':'Express_10_COD',
                        'Express_10_COD':'Express_10_COD',
                        'Express_12':'Express_12',
                        'Express_12_COD':'Express_12_COD',
                        'Express_18':'Express_18',
                        'Express_18_COD':'Express_18_COD',
                        'Express_12_Saturday':'Express_12_Saturday',
                        'Express_12_COD_Saturday':'Express_12_COD_Saturday',
                        'Express_International':'Express_International'
                        }
        services = shipping_services_obj.search([('shipping_instance_id', '=', self.id)])
        services.unlink()
        # Display Services
        for company in self.company_ids:
            for service in services_name:
                global_code_condition = shipping_services_obj.search(
                    [('service_code', '=', service), ('shipping_instance_id', '=', self.id)])
                if global_code_condition:
                    if shipping_services_obj.search([('company_ids', '=', company.id), ('service_code', '=', service),
                                                     ('shipping_instance_id', '=', self.id)]):
                        return True
                    else:
                        global_code_condition.write({'company_ids': [(4, company.id)]})
                else:
                    vals = {'shipping_instance_id': self.id, 'service_code': service,
                            'service_name': services_name.get(service, False), 'company_ids': [(4, company.id)]}
                    shipping_services_obj.create(vals)
                    
                    
    @api.model
    def dpd_ept_quick_add_shipping_services(self, service_type, service_name):
        """ Allow you to get the default shipping services value while creating quick 
            record from the Shipping Service for DPD
            @param service_type: Service type of DPD
            @return: dict of default value set
            @author: Jay Makwana
        """
        return {'default_dpd_service_type':service_type,
                'default_name':service_name}