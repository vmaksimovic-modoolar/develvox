#See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    finance_interface = fields.Selection(selection=[('none', 'None')],
        related='company_id.finance_interface', string='Export Method')
    
    