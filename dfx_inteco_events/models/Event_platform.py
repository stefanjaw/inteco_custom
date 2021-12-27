from odoo import models, fields, api, _


class EventPlatform(models.Model):
    _name = "event.platform"
    _description = 'Plataformas de eventos'

    platform_name = fields.Char(string="Nombre")
    _rec_name = 'platform_name'
