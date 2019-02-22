#See LICENSE file for full copyright and licensing details.

from odoo import models, fields

class export_ecofi(models.TransientModel):
    _inherit = 'export.ecofi'

    export_mode = fields.Selection(selection_add=[('datev_ascii', 'DATEV ASCII')])