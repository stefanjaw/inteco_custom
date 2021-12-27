# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    crm_import_notification_enabled = fields.Boolean(string="Send Notification on Import")
