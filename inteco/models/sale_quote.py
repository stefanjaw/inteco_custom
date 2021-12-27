# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleQuoteTemplate(models.Model):
    _inherit = 'sale.order.template'

    conditions = fields.Html(
        default=False,
        help="Content of the technical and economic conditions section within "
        "the website quote."
    )
