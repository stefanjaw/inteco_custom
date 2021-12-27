from odoo import models, fields, api, _


class EventComertial(models.Model):
    _name = "event.comertial"
    _description = 'Comercial para eventos'

    comertial_name = fields.Many2one(comodel_name='res.users', string="Comercial")
    _rec_name = 'comertial_name'
