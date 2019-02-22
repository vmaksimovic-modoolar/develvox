# -*- coding: utf-8 -*-

from odoo import api, fields, models
from html2text import html2text


class ProductSupplierinfoFixedCosts(models.Model):
    _name = 'product.supplierinfo.fixed.costs'
    _rec_name = 'cost_category'

    cost_category = fields.Char(string='Kostenkategorie', translate=True)
    amount = fields.Float(string='Betrag')
    supplier_id = fields.Many2one("product.supplierinfo", string="Supplier")


class ProductSupplierinfoVariableCosts(models.Model):
    _name = 'product.supplierinfo.variable.costs'
    _rec_name = 'cost_category'

    cost_category = fields.Char(string='Kostenkategorie', translate=True)
    amount = fields.Float(string='Betrag')
    supplier_id = fields.Many2one("product.supplierinfo", string="Supplier")


class ProductSupplierinfoFixedCostPMM(models.Model):
    _name = 'product.supplierinfo.fixed.cost.pmm'
    _rec_name = 'cost_category'

    cost_category = fields.Char(string='Kostenkategorie', translate=True)
    amount = fields.Float(string='Betrag')
    supplier_id = fields.Many2one("product.supplierinfo", string="Supplier")


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    @api.depends('min_qty', 'fix_cost_ids', 'variable_cost_ids', 'fix_cost_ids.amount', 'variable_cost_ids.amount')
    def _total_uom_amount(self):
        for record in self:
            min_qty = record.min_qty or 1.0
            record.total_uom_amount = record.price + (sum(record.fix_cost_ids.mapped('amount')) / min_qty) + sum(record.variable_cost_ids.mapped('amount'))

    @api.depends('fix_cost_pmm_ids', 'fix_cost_pmm_ids.amount')
    def _compute_total_fix_cost(self):
        for record in self:
            total = 0.0
            for cost in record.fix_cost_pmm_ids:
                total += cost.amount
            record.total_fix_cost = total

    fix_cost_ids = fields.One2many('product.supplierinfo.fixed.costs', 'supplier_id', string='Fix EK', copy=True)
    variable_cost_ids = fields.One2many('product.supplierinfo.variable.costs', 'supplier_id', string='Var EK', copy=True)
    fix_cost_pmm_ids = fields.One2many('product.supplierinfo.fixed.cost.pmm', 'supplier_id', string='Fix PMM', copy=True)
    total_uom_amount = fields.Monetary(string="Gesamt EK/ME", compute='_total_uom_amount')
    sim_sales_price = fields.Float(string='Sim Sales Price')
    margin_per = fields.Float(string='Margin (%)')
    margin = fields.Float(compute="_compute_margin", string='Margin (€)')
    total_fix_cost = fields.Float(compute="_compute_total_fix_cost", string="Fix PMM")
    variable_cost = fields.Float(compute="_compute_variable_cost", string="Var. EK/ME")
    fix_cost = fields.Float(compute="_compute_fix_cost", string="Fix. EK")

    @api.depends('variable_cost_ids', 'variable_cost_ids.amount', 'price')
    def _compute_variable_cost(self):
        for record in self:
            total = 0.0
            for cost in record.variable_cost_ids:
                total += cost.amount
            record.variable_cost = total + record.price

    @api.depends('fix_cost_ids', 'fix_cost_ids.amount')
    def _compute_fix_cost(self):
        for record in self:
            total = 0.0
            for cost in record.fix_cost_ids:
                total += cost.amount
            record.fix_cost = total

    @api.onchange('sim_sales_price', 'total_uom_amount', 'margin_per', 'total_fix_cost')
    def _onchange_margin(self):
        context = dict(self.env.context or {})
        if context.get('from_sales_price'):
            #self.margin_per = (((self.sim_sales_price - self.total_uom_amount) / (self.total_uom_amount or 1.0)) * 100) + (self.total_fix_cost / (self.min_qty or 1.0))
            self.margin_per = ((self.sim_sales_price - (self.total_uom_amount + (self.total_fix_cost / (self.min_qty or 1.0)))) / self.total_uom_amount) * 100
        if context.get('from_margin'):
            self.sim_sales_price = (self.total_uom_amount + self.total_uom_amount * (self.margin_per / 100)) + (self.total_fix_cost / (self.min_qty or 1.0))

    def _compute_margin(self):
        for record in self:
            #record.margin = ((record.sim_sales_price - record.total_uom_amount) * record.min_qty) + (record.total_fix_cost / (record.min_qty or 1.0))
            record.margin = (record.min_qty * (record.sim_sales_price - record.total_uom_amount)) - record.total_fix_cost

class ProductTemplate(models.Model):
    _inherit = "product.template"

    seller_ids = fields.One2many(copy=True)


class ProductProduct(models.Model):
    _inherit = "product.product"

    checklist_category_id = fields.Many2one('attributes.checklist.category', string='Checklist Category')
    checklist_ids = fields.One2many('product.attributes.checklist', 'product_id', string='Checklist Attribute', copy=True)
    description = fields.Html(string='Additional Information')
    sustained = fields.Boolean(string='Nachhaltig')
    tender_until = fields.Date("Angebotsabgabe bis")
    delivery_strategy = fields.Selection([
        ('direktauslieferung', 'Direktauslieferung'),
        ('verteiler', 'Verteiler'),
        ('teil-direktauslieferung', 'Teil-Direktauslieferung'),
        ('einlagerung', 'Einlagerung')], string='Delivery Strategy')

    def add_to_description(self):
        self.ensure_one()
        description = ""
        for checklist in self.checklist_ids:
            description += checklist.name.name or ''
            description += "\t\t\t"
            description += checklist.value or ''
            description += "\n"
        description += "\n\n"
        description += html2text(self.description or '')
        self.write({'description_purchase': description})

    @api.onchange('checklist_category_id')
    def _onchange_checklist_category_id(self):
        self.checklist_ids = False
        if self.checklist_category_id:
            vals = []
            for attribute in self.checklist_category_id.attribute_ids:
                vals.append({'product_id': self.id, 'name': attribute.id, 'require': attribute.require})
            self.checklist_ids = vals
            self.description = self.checklist_category_id.description
