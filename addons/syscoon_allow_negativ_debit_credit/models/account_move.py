#See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    _sql_constraints = [
        ('credit_debit2', 'CHECK (1=1)', 'Wrong credit or debit value in accounting entry !'),
    ]