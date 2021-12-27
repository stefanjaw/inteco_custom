# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    payment_date = fields.Date(string="Estimated payment date",
                               help='Estimated payment date')
    category_name = fields.Char(
        compute="_compute_additional_info", store=True,
        help="Used as a row in the estimated income category graph view."
    )
    product_default_code = fields.Char(
        compute="_compute_additional_info", store=True,
        help="Used as a row in the estimated income internal"
             " reference graph view."
    )
    subservice_name = fields.Char(
        compute='_compute_additional_info', store=True, string='Subservice',
        help="Name of the subservice associated to the product."
    )
    subsubservice_name = fields.Char(
        compute='_compute_additional_info', store=True, string='Subsubservice',
        help="message"
    )

    @api.depends('product_id')
    def _compute_additional_info(self):
        """Gets the category name, internal reference and subservice name
           related to the product."""
        for record in self:
            record.category_name = record.product_id.categ_id.name
            record.product_default_code = record.product_id.default_code
            # if record.product_id.subservice_id.parent_id:
            #     record.subservice_name =\
            #         record.product_id.subservice_id.parent_id.name
            #     record.subsubservice_name =\
            #         record.product_id.subservice_id.name
            # else:
            #     record.subservice_name = record.product_id.subservice_id.name
            #     record.subsubservice_name = ''
