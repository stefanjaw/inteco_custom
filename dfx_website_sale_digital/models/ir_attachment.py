# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AttachmentWatermark(models.Model):

    _inherit = ['ir.attachment']

    watermark = fields.Boolean("Agregar marca de agua", default=True)
