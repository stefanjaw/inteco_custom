# -*- coding: utf-8 -*-
# Copyright 2017 Vauxoo
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models, fields, tools


class EventEvent(models.Model):
    _inherit = 'event.event'

    image = fields.Binary(
        attachment=True,
        help="This field holds the image used as event cover, limited to "
        "1024x1024px.")
    image_medium = fields.Binary(
        string="Medium-sized image", attachment=True,
        help="Medium-sized image of the event cover. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        string="Small-sized image", attachment=True,
        help="Small-sized image of the event cover. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")

    # @api.model
    # def create(self, vals):
    #     tools.image_resize_images(vals)
    #     return super(EventEvent, self).create(vals)
    #
    # #TODO QUITAR @api.multi
    # def write(self, vals):
    #     tools.image_resize_images(vals)
    #     return super(EventEvent, self).write(vals)
