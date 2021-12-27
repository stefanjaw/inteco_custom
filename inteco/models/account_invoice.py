# -*- coding: utf-8 -*-

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    # def action_invoice_sent(self):
    #     """ Open a window to compose an email, with the
    #     edi invoice template message loaded by default
    #     """
    #     res = super(AccountInvoice, self).action_invoice_sent()
    #     ctx = res.get('context', {})
    #     ctx.update(dict(custom_layout="inteco.mail_template_data_notification_email_account_invoice"))
    #     res['context'] = ctx
    #     return res
