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


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    actual_stock = fields.Integer(
        string='Actual Stock',
        compute='_calculate_actual_stock'
    )

    check_point = fields.Float(
        compute="_calculate_check_point",
        search='_search_check_point'
    )

    @api.multi
    def _calculate_stock_qty(self):
        query = """
            SELECT swo.id, qty.v FROM 
            stock_warehouse_orderpoint swo, 
            (
                SELECT sum(quantity) as v, product_id, location_id 
                FROM stock_quant
                WHERE location_id IN %s AND product_id IN %s 
                GROUP BY product_id, location_id
            ) as qty
            WHERE swo.location_id=qty.location_id and 
                  swo.product_id = qty.product_id       

        """

        self.env.cr.execute(
            query,
            [
                tuple(self.mapped("location_id").ids),
                tuple(self.mapped("product_id").ids)
            ]
        )

        return dict((r[0], r[1]) for r in self.env.cr.fetchall())

    @api.multi
    def _calculate_actual_stock(self):
        result = self._calculate_stock_qty()

        for record in self:
            record.actual_stock = result.get(record.id, 0)

    @api.multi
    def _calculate_check_point(self):
        result = self._calculate_stock_qty()

        for record in self:
            record.check_point = result.get(record.id,
                                            0) - record.product_min_qty

    @api.model
    def _search_check_point(self, operator, value):

        if operator not in ('=', '!=', '<', '<=', '>', '>=', 'in', 'not in'):
            return []

        if operator == 'in':
            operator = '='
        elif operator == 'not in':
            operator = '!='

        if not value:
            value = 0

            if operator == '=':
                operator = '<='
            elif operator == '!=':
                operator = '>'

        query = """
        SELECT swo.id FROM 
        stock_warehouse_orderpoint AS swo, 
        (
          SELECT sum(sq.quantity) AS v, sq.product_id, sq.location_id 
          FROM stock_quant sq
          GROUP BY sq.product_id, sq.location_id
        ) AS qty
        WHERE (
          swo.location_id = qty.location_id AND
          swo.product_id = qty.product_id AND
          (qty.v - swo.product_min_qty) {operator} {value}) OR 
          (
            (swo.location_id,swo.product_id) NOT IN 
            (SELECT location_id, product_id FROM stock_quant) AND 
            -swo.product_min_qty {operator} {value}
          ) 
        """.format(operator=operator, value=value)

        self.env.cr.execute(query)
        ids = [r[0] for r in self.env.cr.fetchall()]

        return [('id', 'in', ids)]
