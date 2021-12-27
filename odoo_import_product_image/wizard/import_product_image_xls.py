# -*- coding: utf-8 -*-

import base64
import xlrd
import urllib
from urllib.request import Request, urlopen
from odoo.exceptions import ValidationError
from odoo import models, fields, api


class ImportImageProduct(models.TransientModel):
    _name = 'import.product.template'
    
    files = fields.Binary(
        'Select Excel File (.xls / .xlsx supported)',
        required=True,
    )
    data_obj = fields.Selection(
        selection=[('template','Product Template'),
                    ('product','Product'),
        ],
        default='template',
        string='Model',
        required=True,
    )
    operation = fields.Selection(
        selection=[('create','Create Product'),
                    ('update','Update Product'),
        ],
        string="Operation",
        default='create',
        required=True,
    )
    
    # @api.multi #odoo13
    def import_product_file(self):
        product_template_obj = self.env['product.template']
        product_obj = self.env['product.product']
        try:
            workbook = xlrd.open_workbook(file_contents=base64.decodestring(self.files))
        except:
            raise ValidationError("Please select .xls/xlsx file...")
            
        Sheet_name = workbook.sheet_names()
        sheet = workbook.sheet_by_name(Sheet_name[0])
        number_of_rows = sheet.nrows
        aList = []
        row = 1
        while(row < number_of_rows):
            name = sheet.cell(row,0).value
            reference = sheet.cell(row,1).value
            image_medium = sheet.cell(row,2).value
            if 'http' in image_medium or 'https' in image_medium:
                try:
                    # image = base64.encodestring(urllib.request.urlopen(image_medium).read())
                    image_url_header = Request(
                        image_medium, headers={
                            'User-Agent': 'Mozilla/5.0'
                        }
                    ) #odoo13
                    image = base64.encodestring(
                        urllib.request.urlopen(
                            image_url_header
                        ).read()
                    ) #odoo13
                except:
                    image = False
            else:
                try:
#                    image = open(image_medium, 'rb').read().encode('base64')
                    image = base64.b64encode(open(image_medium, 'rb').read())
                except:
                    image = False
            row = row+1
            vals = {
                    'name' : name,
                    'default_code' : reference,
                    }
                    
            #product Template
            if self.data_obj == 'template':
                if self.operation == 'create':
                    template_id = product_template_obj.create(vals)
                    aList.insert(row-1,template_id.id)
                    try:
                        vals_update = {
                            'image_1920' : image,
                            }
                        template_id.write(vals_update)
                    except:
                        continue
                
                elif self.operation == 'update':
                    if image != False:
                        vals_update = {
                                'image_1920' : image,
                                }
                    template_ids = []
                    if reference:
                        template_ids = product_template_obj.search([('default_code','=',reference)])
                    elif name:
                        template_ids = product_template_obj.search([('name','=',name)])
                    else:
                        pass
                    
                    for template_id in template_ids:
                        try:
                            vals_update = {
                            'image_1920' : image,
                            }
                            template_id.write(vals_update)
                            aList.insert(row-1, template_id.id)
                        except:
                            continue
            #product            
            if self.data_obj == 'product':
                if self.operation == 'create':
                    product = product_obj.create(vals)
                    aList.insert(row-1, product.id)
                    try:
                        product_id=True
                        vals = {
                            'image_1920' : image,
                            }
                        product.write(vals)
                    except:
                        continue
                        
                elif self.operation == 'update':
                    product_id=True
                    if image != False:
                        vals_update = {
                                'image_1920' : image,
                                }
                    if reference:
                        product_ids = product_obj.search([('default_code','=',reference)])
                    elif name:
                        product_ids = product_obj.search([('name','=',name)])
                    else:
                        pass
                        
                    for product in product_ids:
                        try:
                            vals_update = {
                            'image_1920' : image,
                            }
                            product_id = product.write(vals_update)
                            aList.insert(row-1, product.id)
                        except:
                            continue
  
        if self.data_obj == 'template':
            action = self.env.ref('product.product_template_action').read()[0]
            action['domain'] = [('id', 'in', aList)]
            
        if self.data_obj == 'product':
            action = self.env.ref('product.product_normal_action_sell').read()[0]
            action['domain'] = [('id', 'in', aList)]
            
        return action
            
