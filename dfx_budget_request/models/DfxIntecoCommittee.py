import re
from odoo import models, fields, api, _


class DfxIntecoComm(models.Model):  # dbr = dfx_budget_request
    _inherit = "inteco.committee"

    type = fields.Selection([
        ('CNN', 'National Standards Commission'),
        ('CTN', 'Technical Committee'),
        ('CTP', 'Technical Committee Private'),
        ('SC', 'Subcommittee'),
        ('GT', 'Workgroup'),
        ('EN', 'Endoso'),
    ], required=True, help="levels of the hierarchy.")
