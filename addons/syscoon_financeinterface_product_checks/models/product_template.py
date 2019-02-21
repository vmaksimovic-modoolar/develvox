#See LICENSE file for full copyright and licensing details.

from odoo import models, api, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        if not vals['taxes_id']:
            raise UserError(_('There is no income tax set. Please define one.'))
        if not vals['supplier_taxes_id']:
            raise UserError(_('There is no expense tax set. Please define one.'))
        categ = self.env['product.category'].search([('id', '=', vals['categ_id'])])
        if vals['property_account_income_id']:
            income_account = self.env['account.account'].search([('id', '=', vals['property_account_income_id'])])
            income_taxes = income_account.datev_steuer
        elif categ:
            income_taxes = categ.property_account_income_categ_id.datev_steuer
        else:
            raise UserError(_('There is no income account set. Please define one.'))
        if income_taxes.ids != vals['taxes_id'][0][2]:
            itaxes = []
            for tax in income_taxes:
                itaxes.append(tax.name)
            raise UserError(_('The tax in product is not equal to the tax in the income account. You can only use this tax: %s.' % ', '.join(itaxes)))
        if not income_taxes:
            raise UserError(_('The income account has no tax. You must set a tax rate in this account: %s.' % income_account.code))
        if vals['property_account_expense_id']:
            expense_account = self.env['account.account'].search([('id', '=', vals['property_account_expense_id'])])
            expense_taxes = expense_account.datev_steuer
        elif categ:
            expense_taxes = categ.property_account_expense_categ_id.datev_steuer
        else:
            raise UserError(_('There is no expense account set. Please define one.'))
        if expense_taxes.ids != vals['supplier_taxes_id'][0][2]:
            etaxes = []
            for tax in expense_taxes:
                etaxes.append(tax.name)
            raise UserError(_('The tax in the Product is not equal to the tax in the expense account. You can only use this tax: %s.' % ', '.join(etaxes)))
        return super(ProductTemplate, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'taxes_id' in vals and vals['taxes_id']:
            taxes = self.env['account.tax'].browse(vals['taxes_id'][0][2])
        if not 'taxes_id' in vals:
            taxes = self.taxes_id
        if 'categ_id' in vals and vals['categ_id']:
            categ = self.env['product.category'].search([('id', '=', vals['categ_id'])])
        if not 'categ_id' in vals:
            categ = self.categ_id
        if 'property_account_income_id' in vals and vals['property_account_income_id']:
            income_account = self.env['account.account'].search([('id', '=', vals['property_account_income_id'])])
        if not 'property_account_income_id' in vals:
            income_account = categ.property_account_income_categ_id
        if 'supplier_taxes_id' in vals and vals['supplier_taxes_id']:
            supplier_taxes = self.env['account.tax'].browse(vals['supplier_taxes_id'][0][2])
        if not 'supplier_taxes_id' in vals:
            supplier_taxes = self.supplier_taxes_id
        if 'property_account_expense_id' in vals and vals['property_account_expense_id']:
            expense_account = self.env['account.account'].search([('id', '=', vals['property_account_expense_id'])])
        if not 'property_account_expense_id' in vals:
            expense_account = categ.property_account_expense_categ_id

        if not income_account:
            raise UserError(_('There is no income account set. Please define one.'))
        if not expense_account:
            raise UserError(_('There is no expense account set. Please define one.'))

        if not income_account.datev_steuer:
            raise UserError(_('The income account has no tax. You must set a tax rate in this account: %s.' % income_account.code))
        if not expense_account.datev_steuer:
            raise UserError(_('The expense account has no tax. You must set a tax rate in this account: %s.' % expense_account.code))

        if income_account.datev_steuer and not taxes.ids:
            itaxes = []
            for tax in income_account.datev_steuer:
                itaxes.append(tax.name)
            raise UserError(_('You have no income taxes defined. Please set this tax: %s.' % ', '.join(itaxes)))

        if expense_account.datev_steuer.ids and not supplier_taxes.ids:
            etaxes = []
            for tax in expense_account.datev_steuer:
                etaxes.append(tax.name)
            raise UserError(_('You have no expense taxes defined. Please set this tax: %s.' % ', '.join(etaxes)))

        if taxes and income_account.datev_steuer.ids != taxes.ids:
            itaxes = []
            for tax in income_account.datev_steuer:
                itaxes.append(tax.name)
            raise UserError(_('The tax in the product is not equal to the tax in the income account. You can only use this tax: %s.' % ', '.join(itaxes)))

        if supplier_taxes and expense_account.datev_steuer.ids != supplier_taxes.ids:
            etaxes = []
            for tax in expense_account.datev_steuer:
                etaxes.append(tax.name)
            raise UserError(_('The tax in the Product is not equal to the tax in the expense account. You can only use this tax: %s.' % ', '.join(etaxes)))
        return super(ProductTemplate, self).write(vals)