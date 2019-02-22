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

from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def write(self, vals):

        edited_lines = self._get_edited_lines(vals)

        res = super(PurchaseOrder, self).write(vals)

        for record in self:
            record._notify_changed_dates(edited_lines)

        return res

    @api.model
    def _get_edited_lines(self, vals):
        """ This function calculate edited lines with edited 'date_planned'. It's some kind of patch
            because odoo has a problem: If we edit anything at purchase.order.line, odoo sends data for
            all lines to write method of purchase.order.
            Problem comes from :
            @file odoo/models.py line 5003
            @method def onchange(self, values, field_name, field_onchange)
        """

        PurchaseOrderLineModel = self.env['purchase.order.line']

        if 'order_line' not in vals:
            return []

        lines = PurchaseOrderLineModel
        for k, id, v in vals['order_line']:
            if k == 1 and 'date_planned' in v:
                line = PurchaseOrderLineModel.browse(id)
                if v['date_planned'] != line.date_planned:
                    lines |= line

        return lines

    @api.multi
    def _notify_changed_dates(self, edited_lines):
        self.ensure_one()

        if not self.origin:
            return

        SaleOrderModel = self.env['sale.order']
        MailMailModel = self.env['mail.mail']

        if not len(edited_lines):
            return

        template = self.env.ref('aok_extensions.send_changed_scheduled_dates')

        mails = list()

        for name in self.origin.split(', '):
            order = SaleOrderModel.search([('name', '=', name)])
            curr_lines = edited_lines.filtered(
                lambda x: x.product_id in order.order_line.mapped('product_id')
            )

            if not len(curr_lines):
                continue

            mails.append(template.with_context(
                edited_lines=curr_lines,
                email_to=order.user_id.email
            ).send_mail(self.id))

        return MailMailModel.browse(mails)
