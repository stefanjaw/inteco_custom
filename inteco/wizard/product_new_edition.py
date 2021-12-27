# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductNewEdition(models.TransientModel):
    _name = "product.new.edition"
    _inherit = "product.common.wizard"

    @api.model
    def default_get(self, fields_list):
        """Sets the approval date when the wizard is called
        """
        res = super(ProductNewEdition, self).default_get(fields_list)
        res.update({
            'approval_date': fields.Date.today(),
        })
        return res

    def action_create_edition(self):
        """Creates a new edition of a standard."""
        product = self.env['product.product'].browse(
            self._context.get('active_id')
        )

        vals = {
            'state': self.state,
            'pages': self.pages,
            'approval': self.approval_date,
            'standards_ref': self.standards_ref,
            'attribute_value_ids': [],
            'categ_id': product.categ_id.id,
        }

        new_product = product.copy(default=vals)

        product.write({
            'state': 'R',
            'replaced_by': new_product.id,
        })

        product.message_post(body=_(
            "A new edition was recently created for this product: "
            "<a href=#id=%s&view_type=form&model=product.product>%s</a>"
        ) % (new_product.id, new_product.default_code))
