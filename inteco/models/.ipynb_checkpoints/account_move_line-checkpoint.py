# -*- coding: utf-8 -*-

from odoo import api, fields, models

import logging
_logging = _logger = logging.getLogger(__name__)

class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.product_uom_id = record.product_id.uom_id
                record.name = record.product_id.name
                record.price_unit = record.product_id.lst_price
                if record.product_id.product_tmpl_id.product_analytic_account:
                    an_account = record.product_id.product_tmpl_id.product_analytic_account
                    record.analytic_account_id = an_account
                else:
                    if record.product_id.product_tmpl_id.categ_id.analytic_account_def:
                        an_account = record.product_id.product_tmpl_id.categ_id.analytic_account_def
                        record.analytic_account_id = an_account
                    else:
                        record.analytic_account_id = ''
            else:
                record.analytic_account_id = ''
