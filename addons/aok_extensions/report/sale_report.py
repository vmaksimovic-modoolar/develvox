##############################################################################
#
# Copyright (c) 2018 - Now Modoolar (http://modoolar.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract support@modoolar.com
#
##############################################################################

from odoo import models, fields, api


class SaleReport(models.Model):
    _inherit = "sale.report"

    prev_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Previous Product',
        readonly=True
    )

    def _select(self):
        select_str = super(SaleReport, self)._select()
        index = select_str.find('t.categ_id as categ_id,')
        return '{}{}{}'.format(
            select_str[:index],
            't.prev_product_id AS prev_product_id, ',
            select_str[index:]
        )

    def _group_by(self):
        group_by_str = super(SaleReport, self)._group_by()
        index = group_by_str.find('t.categ_id,')
        return '{}{}{}'.format(
            group_by_str[:index],
            't.prev_product_id,',
            group_by_str[index:]
        )
