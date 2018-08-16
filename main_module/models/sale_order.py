##############################################################################
#
# Copyright (c) 2018 Modoolar (http://modoolar.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract support@modoolar.com
#
##############################################################################
from odoo import api, fields, models, exceptions, _
import json


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_rate_so(self, order):
        rate = 0
        if order.currency_id.id == order.company_id.currency_id.id:
            rate = 1
        else:
            if order.rate_so:
                rate = order.rate_so
            else:
                if order.currency_conversion_date:
                    rate = order.company_id.currency_id.with_context({'date': order.currency_conversion_date}).compute(
                        1, order.currency_id, False)
                elif order.confirmation_date:
                    rate = order.company_id.currency_id.with_context({'date': order.confirmation_date}).compute(
                        1, order.currency_id, False)
        return rate

    def get_rate_inv(self, order, inv, date):
        if inv.currency_id.id == order.company_id.currency_id.id:
            rate = 1
        else:
            if inv.inv_rate:
                rate = inv.inv_rate
            else:
                rate = order.company_id.currency_id.with_context({'date': date}).compute(1, inv.currency_id, False)
        return rate

    @api.multi
    def fix_problem(self):
        for record in self.env['sale.order'].search([('state', 'not in', ['draft', 'sent'])]):
            tsum = 0

            if len(record.invoice_ids) > 0:
                for invoice in record.invoice_ids:
                    sum_per_invoice = 0
                    if json.loads(invoice.payments_widget):
                        for element in json.loads(invoice.payments_widget)['content']:
                            amount = element['amount']
                            rate = self.get_rate_inv(record, invoice, element['date'])
                            value = amount / rate
                            sum_per_invoice += value
                            # sum_per_invoice += element['amount'] / self.get_rate_inv(record, invoice, element['date'])

                    tsum += -sum_per_invoice if invoice.type == 'out_refund' else sum_per_invoice

            if self.get_rate_so(record) != 0:
                value = record.amount_total / self.get_rate_so(record) - tsum

                if value < -50:
                    print(record.name)
                    print(record.id)
                    print(record.amount_total / self.get_rate_so(record) - tsum)

                record.rate_difference = record.amount_total / self.get_rate_so(record) - tsum
