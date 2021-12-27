import re
from odoo import models, fields


class Prod_Key_Words(models.Model):  # dbr = dfx_budget_request
    _name = "prod.key.words"
    _description = 'Palabras Clave'

    key_words = fields.Char(string="Nombre de la Palabra Clave", required=False, )
    _rec_name = 'key_words'