from odoo import models, fields, api, _


class CostCenter(models.Model):
    _name = "cost.center"
    _description = 'Centro de Costos'

    cost_name = fields.Char(string="Nombre")
    _rec_name = 'cost_name'