# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
DOMAIN = []

class IntecoEventPartner(models.Model):
    _inherit = "res.partner.category"

    is_interest_topic = fields.Boolean(string='Es Tema de interés')
