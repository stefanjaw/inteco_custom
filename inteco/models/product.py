# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# Important! Pay special attention to the changes in this list.
# It's used in the standards catalog as a part of the state filter option and
# also to sort the results of the searches according to the exact position of
# each element, therefore, any change here could affect the expected behavior
# of this features.
STANDARD_STATES = [
    ('C', 'Current'),
    ('P', 'Public consultation'),
    ('V', 'In development'),
    ('D', 'Removed'),
    ('R', 'Replaced'),
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    process = fields.Selection([
        ('F', 'Fast Track'),
        ('C', 'Complete')
    ], help="Process type", default="C")
    short_code = fields.Char(
        help="short code of the standard."
    )
    sector_id = fields.Many2one(
        'inteco.sector', string="Sector"
    )
    committee_id = fields.Many2one(
        'inteco.committee', string="Committee"
    )
    prefix_id = fields.Many2one(
        'inteco.prefix', string="Prefix"
    )
    ics_ids = fields.Many2many(
        'inteco.ics', string="ICS"
    )
    organism_ids = fields.Many2many(
        'inteco.organism', string="Organisms",
        compute='_compute_organism', store=True
    )
    correspondence_ids = fields.Many2many(
        'inteco.organism.standard', string="Correspondences"
    )
    purchase_ok = fields.Boolean(
        default=False
    )
    edition = fields.Integer(
        store=True,
        help="edition number of the standard."
    )
    year = fields.Char(
        compute='_compute_year', store=True,
        help="year of the standard."
    )
    part_one = fields.Integer(
        string="Part I",
        help="first part of a standard."
    )
    part_two = fields.Integer(
        string="Part II",
        help="second part of a standard."
    )
    part_three = fields.Integer(
        string="Part III",
        help="third part of a standard."
    )
    type = fields.Selection(
        default="service"
    )
    approval = fields.Date(
        help="approval date."
    )
    product_variant_id = fields.Many2one(store=True)
    application_field = fields.Text(
        help="Descriptive text about the scope of the standard."
    )
    subservice_id = fields.Many2one(
        'crm.subservice', string='Subservice',
        help="Subservice associated with the template"
    )

    @api.depends('product_variant_ids')
    def _compute_product_variant_id(self):
        """To show correctly the state of the product in the catalog when the
        state filter is used was necessary to assign to product_variant_id the
        last product variant instead of the first."""
        for product in self:
            if product.product_variant_ids:
                product.product_variant_id = product.product_variant_ids[-1].id

    #TODO QUITAR @api.multi
    @api.depends('approval')
    def _compute_year(self):
        """Updates the year depending of the approval date."""
        for product in self:
            if product.approval:
                val = fields.Date.from_string(product.approval).strftime('%Y')
                product.year = val.replace(',', "")

    #TODO QUITAR @api.multi
    @api.depends('default_code')
    def _compute_edition(self):
        """Compute the edition number depending on the number of templates
        and their year."""
        for product in self:
            domain = [
                ('prefix_id', '=', product.prefix_id.id),
                ('short_code', '=', product.short_code),
            ]
            if product.part_one:
                domain += [
                    ('part_one', '=', product.part_one),
                ]
            if product.part_two:
                domain += [
                    ('part_two', '=', product.part_two),
                ]
            if product.part_three:
                domain += [
                    ('part_three', '=', product.part_three),
                ]
            if product.prefix_id.type == 'I' and product.sector_id:
                domain += [
                    ('sector_id', '=', product.sector_id.id),
                ]
            templates = self.env['product.template'].search(
                domain).mapped('default_code')

            if product.default_code in templates:
                product.edition = templates.index(product.default_code) + 1

    @api.depends('correspondence_ids')
    def _compute_organism(self):
        """Search for the organism associated to each correspondence."""
        for record in self:
            organisms = record.mapped('correspondence_ids.organism_id.id')
            record.organism_ids = [(6, 0, organisms)]

    #TODO QUITAR @api.multi
    def _get_default_code(self):
        """Creates an internal reference for the product template by joining
        some specific fields."""
        if not self:
            return False
        self.ensure_one()
        standard_categ = self.env.ref('inteco.product_category_1_1',
                                      raise_if_not_found=False)
        if not standard_categ or self.categ_id != standard_categ:
            return False
        internal_ref = []
        if self.prefix_id.type == 'I' and self.sector_id:
            internal_ref.append(self.sector_id.code)
        if self.short_code:
            internal_ref.append(self.short_code)
        parts = list(filter(None, [
            self.part_one, self.part_two, self.part_three]))
        if parts:
            internal_ref.extend(['-' + str(part) for part in parts])
        if self.year:
            internal_ref.extend([':' + str(self.year)])
        internal_ref = [''.join(internal_ref)]
        if self.prefix_id:
            internal_ref.insert(0, self.prefix_id.name)
        return ' '.join(internal_ref)

    @api.depends('product_variant_ids', 'product_variant_ids.default_code')
    def _compute_default_code(self):
        for product in self:
            product.default_code = product._get_default_code()

    #TODO QUITAR @api.multi
    def _set_default_code(self):
        """Updates the internal reference of the variants if the internal
        reference of the template is changed."""
        for variant in self.mapped('product_variant_ids'):
            variant.default_code = variant._get_default_code()

    @api.model
    def default_get(self, fields_list):
        """Assigns the All / Saleable / Standards category as default value
        when creating a new product."""
        res = super(ProductTemplate, self).default_get(fields_list)
        res.update({
            'categ_id': self.env.ref('inteco.product_category_1_1').id
        })
        return res

    #TODO QUITAR @api.multi
    def product_variant_fields(self):
        """Return the fields related to the product variants."""
        values = []
        for variant in self.product_variant_ids:
            state = dict(self.env['product.product']._fields['state'].
                         _description_selection(self.env)).get(variant.state)
            values.append({
                "state": state,
                "pages": variant.pages,
                "approval": variant.approval,
                "previous_code": variant.previous_code,
                "replaced_by": variant.replaced_by,
                "standards_ref": variant.standards_ref,
            })
        return values

    #TODO QUITAR @api.multi
    def product_history(self, filterby=False):
        """Generates the history of the product. The method return by default
        the entire history. The filterby parameter can be used to return the
        current standard or the new editions."""
        base = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.id)], limit=1)
        history = self.env['product.product']
        while base and base not in history:
            history += base
            base = base.replaced_by
        if filterby == 'current':
            history = history.filtered(lambda r: not r.replaced_by)
        if filterby == 'editions':
            history = history.filtered(lambda r: not r.attribute_value_ids)
        return history


class ProductProduct(models.Model):
    _inherit = 'product.product'

    attribute_value_ids = fields.Many2many(
        'product.attribute.value', string='Attribute Values', ondelete='restrict')
    previous_code = fields.Char(
        help="previous internal reference code."
    )
    pages = fields.Integer(
        help="number of pages."
    )
    state = fields.Selection(
        selection=STANDARD_STATES, help="current state.", default="C")
    replaced_by = fields.Many2one(
        'product.product',
        help="reference to the standard that replaces it."
    )
    standards_ref = fields.Char(
        string="Standards Referred to",
        help="Standards that served as a reference for development "
        "(separated by comma)."
    )
    default_code = fields.Char(
        compute='_compute_default_code', store=True,
        tracking=True,
    )
    modifier_date = fields.Date(
        help="Date related to the modifier Em or Cor."
    )
    latest_date = fields.Date(
        string="Date", compute='_compute_latest_date',
        store=True, readonly=True,
        help="The latest date from the modifier date and the confirmation date"
    )

    priority = fields.Selection(
        [('0', 'None'),
         ('1', 'Low'),
         ('2', 'Medium'),
         ('3', 'High')],
        default='0',
        help="Priority of the standard in searches"
    )

    confirmation_date = fields.Date(
        help="Date of the last review and confirmation."
    )

    #TODO QUITAR @api.multi
    def _get_default_code(self):
        """Creates an internal reference for the product template by joining
        some specific fields."""
        if not self:
            return False
        self.ensure_one()
        standard_categ = self.env.ref(
            'inteco.product_category_1_1', raise_if_not_found=False)
        if not standard_categ or self.categ_id != standard_categ:
            return False
        attr_modifier = self.env.ref(
            'inteco.modifier_attribute', raise_if_not_found=False)
        attr_modifier_num = self.env.ref(
            'inteco.modifier_number_attribute', raise_if_not_found=False)
        attr_modifier_year = self.env.ref(
            'inteco.modifier_year_attribute', raise_if_not_found=False)
        val_modifier = (
            self.attribute_value_ids.filtered(
                lambda x: x.attribute_id == attr_modifier)
            if attr_modifier else False)
        val_modifier_num = (
            self.attribute_value_ids.filtered(
                lambda x: x.attribute_id == attr_modifier_num)
            if attr_modifier_num else False)
        val_modifier_year = (
            self.attribute_value_ids.filtered(
                lambda x: x.attribute_id == attr_modifier_year)
            if attr_modifier_year else False)
        attrib = ''
        if all([val_modifier, val_modifier_num, val_modifier_year]):
            attrib = '/%s %s:%s' % (
                val_modifier.name, val_modifier_num.name,
                val_modifier_year.name)
        default_code = self.product_tmpl_id._get_default_code()
        return (default_code + attrib) if default_code else False

    #TODO QUITAR @api.multi
    @api.depends('attribute_value_ids', 'prefix_id', 'prefix_id.type',
                 'sector_id', 'short_code', 'approval', 'part_one', 'part_two',
                 'part_three','year')
    def _compute_default_code(self):
        """Creates an internal reference for the product variant by joining
        some specific fields."""
        for product in self:
            product.default_code = product._get_default_code()

    # #TODO QUITAR @api.multi
    # @api.depends('confirmation_date', 'modifier_date', 'approval')
    # def _compute_latest_date(self):
    #     for product in self:
    #         product.latest_date = max(product.confirmation_date or '', product.modifier_date or '', product.approval or '')
    #         pass
    
    @api.depends('confirmation_date', 'modifier_date', 'approval')
    def _compute_latest_date(self):
        for product in self:
            if product.approval:
                product.latest_date = str(product.approval)
            else:
                if product.confirmation_date:
                    product.latest_date = str(product.confirmation_date)
                else:
                    if product.modifier_date:
                        product.latest_date = str(product.modifier_date)
                    else:
                        pass
                    
    #TODO QUITAR @api.multi
    def website_publish_button(self):
        """ Ensures the product has a portal file before publishing it on
            website
        """
        if not self.website_published and not self.attachment_count:
            raise ValidationError(_(
                "To publish this product on website, you must first attach "
                "a portal file."))
        return super(ProductProduct, self).website_publish_button()

    #TODO QUITAR @api.multi
    def write(self, vals):
        if 'modifier_date' in vals:
            # When the year of the modification date changes, it is mandatory
            # to change the corresponding attribute; otherwise, the internal
            # reference of the product will remain outdated.
            year_one = fields.Date.from_string(
                vals['modifier_date']).strftime('%Y')
            year_two = fields.Date.from_string(
                self.modifier_date).strftime('%Y')

            if year_one == year_two:
                return super(ProductProduct, self).write(vals)

            new_year = self.env[
                'product.attribute.value'].search([('name', '=', year_one)])

            if not new_year:
                new_year = self.env['product.attribute.value'].create({
                    'name': year_one,
                    'attribute_id': self.env.ref(
                        'inteco.modifier_year_attribute').id
                })

            old_year = self.env[
                'product.attribute.value'].search([('name', '=', year_two)])

            # replace the current ID for the 'modifier year' attribute with
            # the new ID of the selected value.
            attribute_ids = [
                new_year.id if id == old_year.id else id
                for id in self.attribute_value_ids.mapped('id')
            ]

            vals.update({
                'attribute_value_ids': [(6, 0, attribute_ids)]
            })
        return super(ProductProduct, self).write(vals)

    @api.onchange('approval')
    def _onchange_approval(self):
        products = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id)])

        compare_dates = [
            True for date in products.mapped('modifier_date')
            if date and self.approval > date
        ]
        if any(compare_dates):
            raise ValidationError(
                _("The approval date cannot be greater than the modifier "
                  "date of any of his associated standards.")
            )

        if self.confirmation_date and self.approval > self.confirmation_date:
            raise ValidationError(
                _("The approval date cannot be greater than the current "
                  "confirmation date.")
            )

    @api.onchange('confirmation_date')
    def _onchange_confirmation_date(self):
        if self.confirmation_date < self.approval:
            raise ValidationError(
                _("The confirmation date cannot be lower than the approval "
                  "date.")
            )

    @api.onchange('modifier_date')
    def _onchange_modifier_date(self):
        if self.modifier_date < self.approval:
            raise ValidationError(
                _("The modifier cannot have an approval date lower than "
                  "the base standard.")
            )
