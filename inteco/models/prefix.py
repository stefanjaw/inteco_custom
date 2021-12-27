# -*- coding: utf-8 -*-

from odoo import fields, models


class Prefix(models.Model):
    _name = 'inteco.prefix'
    _description = 'The prefixes used as part of the standard name'
    _sql_constraints = [
        ('prefix_name_unique',
         'UNIQUE(name)',
         "The prefix name must be unique"
         ),
    ]

    name = fields.Char(help="prefix description")
    type = fields.Selection([
        ('I', 'Internal'),
        ('E', 'External'),
    ], default='E', help="prefix category")
