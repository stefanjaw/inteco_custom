# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ProductUseVariant(models.TransientModel):
    _name = "product.use.variant"
    _inherit = "product.common.wizard"

    def action_create_new_variant(self):
        """Creates a new variant using another variant as template."""

        modifiernumbers = {
            0: self.env.ref('inteco.attribute_modifiernumber_1').id,
            1: self.env.ref('inteco.attribute_modifiernumber_2').id,
            2: self.env.ref('inteco.attribute_modifiernumber_3').id,
        }

        modifier_id = self._context.get('modifier')

        product = self.env['product.product'].browse(
            self._context.get('active_id'))

        template = product.product_tmpl_id

        childs = product.product_variant_ids.filtered("attribute_value_ids")

        if len(childs) == len(modifiernumbers):
            raise ValidationError(
                _("The maximum number of allowed modifiers for this product "
                  "has been reached.")
            )

        if self.approval_date < template.approval:
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
                active_id=template.id).create({
                    'name': approval_year,
                    'attribute_id': self.env.ref(
                        'inteco.modifier_year_attribute').id
                }).id

        vals = {
            'state': self.state,
            'pages': self.pages,
            'standards_ref': self.standards_ref,
            'product_tmpl_id': template.id,
            'attribute_value_ids': [(6, 0, [
                modifier_id, number_id, year_id])] or [],
            'modifier_date': self.approval_date,
        }

        products_to_update = template.product_variant_ids.filtered(
            lambda x: x.state == 'C')

        new_product = self.env['product.product'].create(vals)

        if products_to_update:
            products_to_update.write({
                'state': 'R',
                'replaced_by': new_product.id,
            })

        product.message_post(body=_(
            "This product was used as template to create "
            "<a href=#id=%s&view_type=form&model=product.product>%s</a>"
        ) % (new_product.id, new_product.default_code))
