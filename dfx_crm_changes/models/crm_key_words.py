from odoo import models, fields, api, _


class CRMKeywords(models.Model):
    _name = "crm.key.words"
    _description = 'Palabras clave para leads'

    key_word_name = fields.Char(string="Palabra Clave")
    _rec_name = 'key_word_name'