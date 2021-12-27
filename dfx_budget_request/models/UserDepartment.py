import re
from odoo import models, fields, api, _


class UserDepartdbr(models.Model):  # dbr = dfx_budget_request
    _name = "user.depart"
    _description = 'Departamento de usuarios'

    depart_name = fields.Char(string="Departamento", required=False,)
    _rec_name = 'depart_name'
