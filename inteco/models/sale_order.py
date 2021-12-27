# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    conditions = fields.Html(
        default=False,
        help="This field is automatically filled with the technical and "
        "economic conditions when are available from the selected quote "
        "template."
    )

    # #TODO Se quita para corregir error de envio de correo en SO
    # def action_quotation_send(self):
    #     res = super(SaleOrder, self).action_quotation_send()
    #     ctx = res.get('context', {})
    #     ctx.update(dict(
    #         custom_layout="inteco.mail_template_data_notification_email_sale_order"
    #     ))
    #     res['context'] = ctx
    #     return res


    @api.onchange('template_id')
    def onchange_template_id(self):
        res = super(SaleOrder, self).onchange_template_id()
        if self.template_id:
            template = self.template_id.with_context(lang=self.partner_id.lang)
            self.conditions = template.conditions or False
        return res
