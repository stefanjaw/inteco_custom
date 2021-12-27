# -*- coding: utf-8 -*-

from odoo import fields, models


class HelpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    enabled = fields.Boolean(
        help="If true, appears as a selectable value for the types list in\
        the complaint form"
    )
