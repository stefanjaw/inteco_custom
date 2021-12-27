# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons.inteco.models.product import STANDARD_STATES


class ProductNewEdition(models.TransientModel):
    _name = "new.product.new.edition"
    # _inherit = "new.product.common.wizard"

    state = fields.Selection(
        selection=STANDARD_STATES,
        help="current state.", default="C"
    )
    pages = fields.Integer(
        help="number of pages."
    )
    approval_date = fields.Date(
        help="Modifier approval date."
    )
    standards_ref = fields.Char(
        string="Standards Referred to",
        help="Standards inherited from the standard template."
    )

    lst_price = fields.Float(string="Precio" )
    mod_type = fields.Selection([
        ('mod', 'Modificada'),
        ('partial', 'Parcial'),
        ('iden', 'Idéntica'),
        ('None_type', 'N/A')
    ], string='Tipo de modificación')
    edition = fields.Integer(string="Edición")

    # @api.model
    # def default_get(self, fields_list):
    #     """Sets the approval date when the wizard is called
    #     """
    #     res = super(ProductNewEdition, self).default_get(fields_list)
    #     res.update({
    #         'approval_date': fields.Date.today(),
    #     })
    #     return res

    @api.model
    def default_get(self, fields_list):
        """Set default values when the wizard is called."""
        template = self.env['product.template'].browse(
            self._context.get('active_id'))
        res = super(ProductNewEdition, self).default_get(fields_list)
        res.update({
            'pages': template.pages,
            'standards_ref': template.standards_ref,
            'approval_date': fields.Date.today(),
            'edition': template.edition+1,
        })
        return res

    def new_action_create_edition(self):
        """Creates a new edition of a standard."""
        product = self.env['product.template'].browse(
            self._context.get('active_id'))

        approval_year = fields.Date.from_string(
            self.approval_date).strftime('%Y')

        vals = {
            'state': self.state,
            'pages': self.pages,
            'edition': self.edition,
            'year': approval_year,
            'approval': self.approval_date,
            'standards_ref': self.standards_ref,
            'attribute_value_ids': [],
            'categ_id': product.categ_id.id,
            'list_price': self.lst_price,
            # 'default_code': product.default_code,
            'mod_type': self.mod_type
        }

        new_product = product.copy(default=vals)

        new_product.new_replaced_by = False
        new_product.edition = self.edition
        new_product.year = approval_year
        new_product.approval = self.approval_date
        product.state = 'R'
        product.new_replaced_by = new_product.id

        product.message_post(body=_(
            "A new edition was recently created for this product: "
            "<a href=#id=%s&view_type=form&model=product.template>%s</a>"
        ) % (new_product.id, new_product.name))
