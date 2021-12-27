# -*- coding: utf-8 -*-

from odoo import fields, models


class Stage(models.Model):
    _inherit = 'crm.stage'

    default_activities_ids = fields.Many2many(
        'mail.activity.type', string="Default Activities",
        help='Default activities by stages.')
    template_id = fields.Many2one(
        'mail.template', string='Automated Answer Email Template',
        domain="[('model', '=', 'crm.lead')]",
        help="Automated email sent to the lead's customer when the lead "
             "reaches this stage.")
