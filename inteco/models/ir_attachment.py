# -*- coding: utf-8 -*-
# Copyright 2017 Vauxoo
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    frequently = fields.Boolean(
        string="Loaded Frequently",
        help="When a document will be loaded frequently.")

    @api.model
    def create(self, vals):
        """ Prevents the user from attaching more than one portal file per product """
        if (self._context.get('default_res_model') == 'product.product'
                and self._context.get('default_product_downloadable')
                and self.env.uid != SUPERUSER_ID):
            product_id = self._context.get('default_res_id')
            product = self.env['product.product'].browse(product_id)
            if product.attachment_count > 0:
                raise ValidationError(_(
                    "The product '%s' already has a portal file.\n"
                    "You can attach only one portal file per product.\n"
                    "If you would like to use this attachment instead, "
                    "please first remove the currently attached one."
                    ) % product.name)
        return super(IrAttachment, self).create(vals)
