# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    picking_note = fields.Char(string='Kommissionierhinweis')

    qc_overpacked = fields.Boolean("Palette überpackt")
    qc_unpaletted = fields.Boolean("Unpalettiert geladen")
    qc_false_uom = fields.Boolean("Verp-Einheit falsch")
    qc_mixed_quality = fields.Boolean("Nicht sortenrein")
    qc_no_do = fields.Boolean("Lieferschein fehlt")
    qc_higher_140 = fields.Boolean("Höher als 140 cm")
    qc_oversized = fields.Boolean("Zu Lang / Zu breit")
    qc_unlabeled = fields.Boolean("Karton Unbeschriftet")
    qc_false_label = fields.Boolean("Beschr. Lief.-Hinw.")
    qc_no_reference = fields.Boolean("Best-/Art.-Nr. fehlt")

    qc_note = fields.Text("Fehler/sonstiges")
    qc_time = fields.Float("Zeitbedarf")

    qc_processing = fields.Char("Verarbeitung")
    qc_print = fields.Char("Druck")
    qc_packaging = fields.Char("Verpackung")
    qc_functional_test = fields.Char("Funktionstest")

    picking_nok = fields.Boolean(string="Picking NOK", compute="_compute_picking_nok", store=True)
    picker_id = fields.Many2one('res.users', string="Picker")
    package_count = fields.Integer(compute="_compute_package_count", string="Package Count")
    received_date = fields.Datetime("Empfangsdatum")

    def _compute_package_count(self):
        for picking in self:
            picking.package_count = len(picking.package_ids)

    @api.depends('qc_overpacked', 'qc_unpaletted', 'qc_false_uom', 'qc_mixed_quality', 'qc_no_do',
        'qc_higher_140', 'qc_oversized', 'qc_unlabeled', 'qc_false_label', 'qc_no_reference', 'qc_note',
        'qc_time', 'qc_processing', 'qc_print', 'qc_packaging', 'qc_functional_test')
    def _compute_picking_nok(self):
        for picking in self:
            if picking.qc_overpacked or picking.qc_unpaletted or picking.qc_false_uom or picking.qc_mixed_quality or picking.qc_no_do or\
               picking.qc_higher_140 or picking.qc_oversized or picking.qc_unlabeled or picking.qc_false_label or picking.qc_no_reference or\
               picking.qc_note or picking.qc_time or picking.qc_processing or picking.qc_print or picking.qc_packaging or picking.qc_functional_test:

                picking.picking_nok = True

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        order = self.env['sale.order'].search([('name', '=', res.origin)])
        if order:
            res.picking_note = order.picking_note
        return res


class StockPickingRoute(models.Model):
    _name = "stock.picking.route"
    _order = 'sequence'

    location_id = fields.Many2one('stock.location', string='Location')
    sequence = fields.Integer(required=True, default=10)


class Location(models.Model):
    _inherit = "stock.location"

    height = fields.Float("Height")


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    @api.multi
    def confirm_picking(self):
        self.ensure_one()
        self.mapped('picking_ids').write({'picker_id': self.user_id.id})
        return super(StockPickingBatch, self).confirm_picking()


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    categ_id = fields.Many2one(related="product_id.categ_id", string="Product Category", store=True)
    use_date = fields.Date(string='Best before Date',
        help='This is the date on which the goods with this Serial Number start deteriorating, without being dangerous yet.')
