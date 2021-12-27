# -*- coding: utf-8 -*-

from odoo import api, fields, models

from ..models.product import STANDARD_STATES


class ProductCommonWizard(models.TransientModel):
    """Defines fields and methods which are common among product wizards"""
    _name = "product.common.wizard"

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
        template = self.env['product.product'].browse(
            self._context.get('active_id'))
        res = super(ProductCommonWizard, self).default_get(fields_list)
        res.update({
            'pages': template.pages,
            'standards_ref': template.standards_ref,
        })
        return res
