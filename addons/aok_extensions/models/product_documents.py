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

from odoo import models, fields


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    external_type = fields.Selection(
        selection=[
            ('image', 'Image'),
            ('video', 'Video'),
            ('document', 'Document')
        ],
        string='Link Type',
        index=True
    )


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Documents / Internal

    file_attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[
            ('res_model', '=', _inherit),
            ('type', '=', 'binary'),
            ('external_type', '=', False),
        ],
        string='Attachment'
    )

    url_attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[
            ('res_model', '=', _inherit),
            ('type', '=', 'url'),
            ('external_type', '=', False),
        ],
        string='Attachment'
    )

    # Documents / External

    ext_doc_image_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[
            ('res_model', '=', _inherit),
            ('external_type', '=', 'image'),
        ],
        string='Shop Photos'
    )

    ext_doc_video_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[
            ('res_model', '=', _inherit),
            ('external_type', '=', 'video'),
        ],
        string='Shop Videos'
    )

    ext_doc_documents_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[
            ('res_model', '=', _inherit),
            ('external_type', '=', 'document'),
        ],
        string='Shop Documents'
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Documents / Internal

    file_attachment_prod_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[
            ('res_model', '=', _inherit),
            ('type', '=', 'binary'),
            ('external_type', '=', False),
        ],
        string='Attachment'
    )

    url_attachment_prod_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[
            ('res_model', '=', _inherit),
            ('type', '=', 'url'),
            ('external_type', '=', False),
        ],
        string='Attachment'
    )

    # Documents / External

    ext_doc_image_prod_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[
            ('res_model', '=', _inherit),
            ('external_type', '=', 'image'),
        ],
        string='Shop Photos'
    )

    ext_doc_video_prod_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[
            ('res_model', '=', _inherit),
            ('external_type', '=', 'video'),
        ],
        string='Shop Videos'
    )

    ext_doc_documents_prod_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[
            ('res_model', '=', _inherit),
            ('external_type', '=', 'document'),
        ],
        string='Shop Documents'
    )

    variant_pricelist_ids = fields.One2many(
        comodel_name='product.pricelist.item',
        inverse_name='product_id',
        string='Pricelist Items'
    )

