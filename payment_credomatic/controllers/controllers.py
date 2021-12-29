# -*- coding: utf-8 -*-
# from odoo import http


# class PaymentCredomatic(http.Controller):
#     @http.route('/payment_credomatic/payment_credomatic/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/payment_credomatic/payment_credomatic/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('payment_credomatic.listing', {
#             'root': '/payment_credomatic/payment_credomatic',
#             'objects': http.request.env['payment_credomatic.payment_credomatic'].search([]),
#         })

#     @http.route('/payment_credomatic/payment_credomatic/objects/<model("payment_credomatic.payment_credomatic"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('payment_credomatic.object', {
#             'object': obj
#         })
