#See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import UserError
import time


class export_ecofi(models.TransientModel):
    _name = 'export.ecofi'
    _description = 'Financeexport'

    vorlauf_id = fields.Many2one('ecofi', 'Vorlauf', readonly=True, default=lambda self: self._get_default_vorlauf())
    journal_id = fields.Many2many('account.journal', 'export_ecofi_journal_rel', 'export_ecofi_id', 'journal_id', 'Journal', default=lambda self: self._get_default_journal())
    export_type = fields.Selection(selection='_get_export_types', string='Export Type', required=True, default='date')
    date_from = fields.Date('Date From', default=lambda *a: time.strftime('%Y-%m-01'))
    date_to = fields.Date('Date To', default=lambda *a: time.strftime('%Y-%m-%d'))
    export_mode = fields.Selection(selection=[], string='Export Mode', required=True)
    export_xml_customer_invoices = fields.Boolean('Customer Invoices')
    export_xml_vendor_invoices = fields.Boolean('Vendor Invoices')

    @api.multi
    def _get_default_journal(self):
        user = self.env['res.users'].browse(self._uid)
        journal_ids = []
        if user.company_id.finance_interface:
            for journal in user.company_id.journal_ids:
                journal_ids.append(journal.id)
        return journal_ids

    @api.multi
    def _get_default_vorlauf(self):
        vorlauf = False
        if 'active_model' in self._context and 'active_id' in self._context:
            if self._context['active_model'] == 'ecofi':
                vorlauf = self._context['active_id']
        return vorlauf

    @api.multi
    def _get_export_types(self):
        """Method that can be used by other Modules to add their export type to the selection of possible export types
        """
        return [('date', 'Datum')]

    @api.multi
    def startexport(self):
        """ Start the export through the wizard
        """
        if self.export_mode == 'none':
            raise UserError(_('No Export-Method selected. Please select one or install further Modules to provide an Export-Method!'))
        if self.export_mode == 'datev_ascii':
            exportecofi = self.env['ecofi']
            for export in self:
                thisvorlauf = export.vorlauf_id and export.vorlauf_id.id or False
                date_from = False
                date_to = False
                if export.export_type == 'date':
                    date_from = export.date_from
                    date_to = export.date_to
                journal_ids = []
                for journal in export.journal_id:
                    journal_ids.append(journal.id)
                vorlauf = exportecofi.ecofi_buchungen(journal_ids=journal_ids, vorlauf_id=thisvorlauf, date_from=date_from, date_to=date_to)
            return {
                'name': 'Financial Export Invoices',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'ecofi',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': vorlauf,
            }
        if self.export_mode == 'datev_xml':
            vorlauf = self.make_export_invoice()
            return {
                'name': 'Financial Export Invoices',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'ecofi',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': vorlauf,
            }
