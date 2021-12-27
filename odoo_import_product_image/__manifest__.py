# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': "Import Product Images from Excel (from Path and URL)",
    'version': '3.0',
    'price': 49.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'summary': """This module allow you to import images from excel using URL and Path.""",
    'description': """
This module help to import product Template or Product from excel.
    In this module for update product image you can add path as LOCAL PATH or URL also

    In this module for import product template you should create .xls or .xlsx,
    Enter product name, reference code and also iimage path of product image,
    
    For Update product image or product template image you should enter product name or product reference code and image path.
    
    Image path should be as "/home/downloads/.../*.jpg or .png or .jpeg etc." or "https://...." or "http://"
Import your products using your import file

Menus Available:
Import Products
        Import Product & Images
CSV Product Images Import
product_image_upload
product_image_from_url
Import Product Images From URL


import product
product import
product images
product image import
product image photos
product image load
product import csv
product import excel
image product
photo product
import product images
product images load odoo
odoo import load

product images upload
upload product image
upload product photo
import script product image
product load
product csv import image
product excel import image
image import product odoo
product csv image import





    
    """,
    'author': "Probuse Consulting Service Pvt. Ltd.",
    'website': "http://www.probuse.com",
    'support': 'contact@probuse.com',
    'images': ['static/description/img1.png'],
     'live_test_url': 'https://youtu.be/9qFxR4QKtb0',
    'category' : 'Sales',
    'depends': [
                'base','sale',
                ],
    'data':[
        'security/ir.model.access.csv',
        'wizard/import_product_image_xls_view.xml',
        'views/import_product_menu.xml',
    ],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
