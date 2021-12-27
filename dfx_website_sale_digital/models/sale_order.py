# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from itertools import groupby


class SaleOrderWatermark(models.Model):

    _inherit = ['sale.order']

    authorize_document = fields.Char(string="Autoriza el uso de este documento a", required=False, )
    watermark_email = fields.Char(string="Correo electrónico", required=False, )



    # def order_lines_layouted(self):
    #     """
    #     Returns this order lines classified by sale_layout_category and separated in
    #     pages according to the category pagebreaks. Used to render the report.
    #     """
    #     self.ensure_one()
    #     report_pages = [[]]
    #     for category, lines in groupby(self.order_line, lambda l: l.layout_category_id):
    #         # If last added category induced a pagebreak, this one will be on a new page
    #         if report_pages[-1] and report_pages[-1][-1]['pagebreak']:
    #             report_pages.append([])
    #         # Append category to current report page
    #         report_pages[-1].append({
    #             'name': category and category.name or _('Uncategorized'),
    #             'subtotal': category and category.subtotal,
    #             'pagebreak': category and category.pagebreak,
    #             'lines': list(lines)
    #         })
    #
    #     return report_pages


class SaleOrderDownload(models.Model):

    _inherit = "sale.order.line"

    isdownload = fields.Boolean(string='Límite de Descarga Alcanzado?')
