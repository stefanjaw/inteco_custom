# -*- coding: utf-8 -*-

from odoo import fields, models, _


class ProductConfirm(models.TransientModel):
    _name = "new.product.confirm"

    confirmation_date = fields.Date(
        help="Date of the last review and confirmation."
    )

    def new_action_confirm_product(self):
        """Allows to confirm an specific product."""
        product = self.env['product.template'].browse(
            self._context.get('active_id')
        )
        product.update({
            'confirmation_date': self.confirmation_date,
        })
        product._onchange_confirmation_date()
        product.message_post(body=_(
            "This product was successfully reviewed and confirmed."))
