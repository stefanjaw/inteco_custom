# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import os
import mimetypes
from werkzeug.utils import redirect

from odoo import http
from odoo.http import request
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale

from odoo.addons.website_sale_digital.controllers.main import WebsiteSaleDigital
import logging

_logger = logging.getLogger(__name__)

try:
	from PyPDF2 import PdfFileWriter, PdfFileReader
except (ImportError, IOError) as err:
	_logger.debug(err)


class WebsiteSaleWatermark(WebsiteSale):
	REQUIRED_FIELDS_WATERMARK = ['authorize_document', 'watermark_email']

	@http.route(['/shop/checkout'], type='http', auth="public", website=True, sitemap=False)
	def checkout(self, **post):
		if 'express' in post:
			order = request.website.sale_get_order()
			if 'watermark' not in post and order.amount_total != 0:
				values = {
					'website_sale_order': order,
					'error': {},
				}
				return request.render("dfx_website_sale_digital.website_form_watermark", values)

		return super(WebsiteSaleWatermark, self).checkout(**post)

	@http.route('/shop/watermark', type='http', auth="public", methods=['POST'], website=True)
	def website_form_watermark(self, **post):
		order = request.website.sale_get_order()
		values = {
			'website_sale_order': order,
		}

		order.authorize_document = post.get('authorize_document')
		order.watermark_email = post.get('watermark_email')

		errors = {}
		for field in self.REQUIRED_FIELDS_WATERMARK:
			if not post.get(field):
				errors.update({field: 'missing'})

		if errors:
			values.update(error=errors)
			return request.render("dfx_website_sale_digital.website_form_watermark", values)

		return request.redirect("/shop/checkout?express=1&watermark=1")


class WebsiteSaleDigitalWatermark(WebsiteSaleDigital):

	@http.route([
		'/my/download',
	], type='http', auth='public')
	def download_attachment(self, attachment_id, sale_id=None, line_id=None):
		""" This method was taken from website_sale_digital module ->
		odoo/addons/website_sale_digital/controllers/main.py
		The method was overwritten because we need change the coditional
		when the attach is a document. (if attachmente['data'])
		When the attach is a document should be a watermark in all the
		pages of the document.
		"""
		t = request.env['sale.order.line'].sudo().search([('id', '=', int(line_id))])
		u = request.env['sale.order'].sudo().search([('id', '=', t.order_id.id)])
		# if t.isdownload == False:
		name = u.partner_id.name
		pro_name = t.product_template_id.name
		pro_code = t.product_template_id.default_code
		u.message_post(
			body=name + ' ' + "realizó la descarga de la norma:" + " " + "[" + str(pro_code) + "]" + " " + pro_name)
		t.isdownload = True
		# Check if this is a valid attachment id
		attachment = request.env['ir.attachment'].sudo().search_read(
			[('id', '=', int(attachment_id))],
			["name", "datas", "store_fname", "mimetype", "res_model", "res_id", "type", "url", "watermark"]
		)

		if attachment:
			attachment = attachment[0]
		else:
			return redirect(self.orders_page)

		# Check if the user has bought the associated product
		res_model = attachment['res_model']
		res_id = attachment['res_id']
		purchased_products = request.env['account.move.line'].get_digital_purchases()

		# if res_model == 'product.product':
		# 	if res_id not in purchased_products:
		# 		return redirect(self.orders_page)
		#
		# # Also check for attachments in the product templates
		# elif res_model == 'product.template':
		# 	template_ids = request.env['product.product'].sudo().browse(purchased_products).mapped('product_tmpl_id').ids
		# 	if res_id not in template_ids:
		# 		return redirect(self.orders_page)
		#
		# else:
		# 	return redirect(self.orders_page)

		# The client has bought the product, otherwise it would have been blocked by now
		if attachment["type"] == "url":
			if attachment["url"]:
				return redirect(attachment["url"])
			else:
				return request.not_found()
		elif attachment["datas"]:
			data = io.BytesIO(base64.standard_b64decode(attachment["datas"]))
			# we follow what is done in ir_http's binary_content for the extension management

			final_pdf = False
			if attachment["watermark"]:
				# We have a report in Odoo and get the pdf content too, this gets
				# a bytes object

				order = request.env['sale.order'].sudo().search([('id', '=', int(sale_id))])

				free_download = False
				for line in order.order_line:
					if line.id == int(line_id) and line.price_subtotal == 0:
						free_download = True
						break

				context = {
					'free_download': free_download,
				}

				report_watermark = request.env.ref('dfx_website_sale_digital.action_report_watermark_2')
				pdf_watermark = report_watermark.sudo().with_context(context)._render_qweb_pdf(int(sale_id))[0]

				# BytesIO is a file-like API for reading and writing bytes objects.
				# bytes object is pass to in-memory bytes buffer
				data_pdf_watermark = io.BytesIO(pdf_watermark)

				# file object is transform to PdfFileReader
				data_pdf_base = PdfFileReader(data)

				output = PdfFileWriter()
				page = data_pdf_base.getPage(0)
				if page:
					output.addPage(page)

				num = 1
				while num < data_pdf_base.getNumPages():
					# The watermark is overlaped in all pages
					# (except the first page) in the product digital document
					page = data_pdf_base.getPage(num)
					# The page_pdf have overlapped the page before
					# here the watermark page_pdf is created clean again
					pdf = PdfFileReader(data_pdf_watermark)
					page_pdf = pdf.getPage(0)
					page_pdf.mergePage(page)
					output.addPage(page_pdf)
					num += 1

				# a bytes buffer is created to write the new product pdf
				# with the watermark
				final_pdf = io.BytesIO()
				# The PdfFileWriter is written in buffer to be export
				# (dowloaded)
				output.write(final_pdf)

			extension = os.path.splitext(attachment["store_fname"] or '')[1]
			extension = extension if extension else mimetypes.guess_extension(attachment["mimetype"] or '')
			filename = attachment['name']
			filename = filename if os.path.splitext(filename)[1] else filename + extension
			return http.send_file(final_pdf or data, filename=filename, as_attachment=True)
		else:
			return request.not_found()
		# else:
		# 	return request.render("dfx_website_sale_digital.max_download_reach", {})
