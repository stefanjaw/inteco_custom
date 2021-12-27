# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
from odoo.addons.inteco.models.product import STANDARD_STATES


class ProductUseVariant(models.TransientModel):
    _name = "new.product.use.variant"
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

    @api.model
    def default_get(self, fields_list):
        """Set default values when the wizard is called."""
        template = self.env['product.template'].browse(
            self._context.get('active_id'))
        res = super(ProductUseVariant, self).default_get(fields_list)
        res.update({
            'pages': template.pages,
            'standards_ref': template.standards_ref,
        })
        return res

    def new_action_create_new_variant(self):
        """Creates a new product using another product as template."""

        modifiernumbers = {
            0: self.env.ref('inteco.attribute_modifiernumber_1').id,
            1: self.env.ref('inteco.attribute_modifiernumber_2').id,
            2: self.env.ref('inteco.attribute_modifiernumber_3').id,
        }

        modifier_id = self._context.get('modifier')

        product = self.env['product.template'].browse(self._context.get('active_id', []))

        template = product.id

        childs = product.product_variant_ids.filtered("attribute_value_ids")

        if len(childs) == len(modifiernumbers):
            raise ValidationError(
                _("The maximum number of allowed modifiers for this product "
                  "has been reached.")
            )

        if self.approval_date < product.approval:
            raise ValidationError(
                _("The modifier cannot have an approval date lower than "
                  "the base standard.")
            )

        number_id = modifiernumbers[sum([
            modifier_id in child.attribute_value_ids.mapped(
                "id") for child in childs])]

        approval_year = fields.Date.from_string(
            self.approval_date).strftime('%Y')

        year_id = self.env['product.attribute.value'].search(
            [('name', '=', approval_year)]).id

        if not year_id:
            year_id = self.env['product.attribute.value'].with_context(
                active_id=template).create({
                    'name': approval_year,
                    'attribute_id': self.env.ref(
                        'inteco.modifier_year_attribute').id
                }).id

        if product.default_code.find("COR") >= 0:
            new_default_code = product.default_code.split("COR"[0])
            new_code = str(new_default_code[0]) + 'COR' + ' ' + str(product.edition_con) + ':' + str(approval_year)
        else:
            product.edition_con = 1
            new_code = str(product.default_code) + '/' + 'COR' + ' ' + str(product.edition_con) + ':' + str(approval_year)

        vals = {
            'state': self.state,
            'pages': self.pages,
            'standards_ref': self.standards_ref,
            # 'product_tmpl_id': template,
            'attribute_value_ids': [(6, 0, [modifier_id, number_id, year_id])] or [],
            'modifier_date': self.approval_date,
            'categ_id': product.categ_id.id,
            'uom_id': product.uom_id.id,
            'uom_po_id': product.uom_po_id.id,
            'is_published': product.is_published,
            'default_type': new_code,
            'edition_con': product.edition_con+1
        }

        products_to_update = product.filtered(
            lambda x: x.state == 'C')

        # new_product = self.env['product.template'].create(vals)
        new_product = product.copy(default=vals)

        product.state = 'R'
        product.new_replaced_by = new_product.id


        product.message_post(body=_(
            "This product was used as template to create "
            "<a href=#id=%s&view_type=form&model=product.template>%s</a>"
        ) % (new_product.id, new_product.name))
