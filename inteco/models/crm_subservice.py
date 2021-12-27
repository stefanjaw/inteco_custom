# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SubService(models.Model):
    _name = 'crm.subservice'

    name = fields.Char(help="Name of the subservice", required=True)
    description = fields.Text()
    responsible_id = fields.Many2one('res.users',
                                     help="User responsible of the subservice")
    crm_team_id = fields.Many2one('crm.team', required=True)
    product_ids = fields.One2many(
        'product.template', 'subservice_id', string="Products",
        help="Products associated with the subservice."
    )
    parent_id = fields.Many2one(
        'crm.subservice', string="Parent"
    )
    display_name = fields.Char(
        compute='_compute_display_name', store=True,
    )
    website_published = fields.Boolean(
        default=True, help="If it's true, the subservice can be selected from "
                           "the contact form of the website"
    )

    @api.depends('name', 'parent_id.display_name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = (
                '%s - %s' % (record.parent_id.display_name, record.name)
                if record.parent_id else record.name
            )

    #TODO QUITAR @api.multi
    def action_view_products(self):
        """This method returns an action that displays the product kanban view
        with the products associated with a subservice."""
        for record in self:
            if not record.product_ids:
                raise ValidationError(
                    _("The subservice does not yet have products associated.")
                )
            action = self.env.ref(
                'product.product_normal_action_sell').read()[0]
            action['domain'] = [
                ('product_tmpl_id', 'in', record.product_ids.mapped('id'))]
        return action

    #TODO QUITAR @api.multi
    def website_publish_button(self):
        self.website_published = not self.website_published
