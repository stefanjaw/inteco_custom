import re
from odoo import models, fields, api, _


class UserAprovdbr(models.Model):  # dbr = dfx_budget_request
    _name = "process.type"
    _description = 'Tipos de Procesos'

    user_name = fields.Char(string="Nombre del Proceso", required=False, )
    _rec_name = 'user_name'
