from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'purchase.order'

    def action_view_invoice(self, invoices=False):
        for invoice in invoices:
            invoice._get_change_account()
        res = super(SaleOrder, self).action_view_invoice(invoices)
        return res
