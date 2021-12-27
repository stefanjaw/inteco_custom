# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Sector(models.Model):
    _name = 'inteco.sector'
    _description = 'The industry sectors to which a standard may belong to'
    _sql_constraints = [
        ('sector_code_unique',
         'UNIQUE(code)',
         "The sector code must be unique"),
    ]

    name = fields.Char(
        help="industry area to which the standard belongs."
    )
    code = fields.Char(
        help="a one character code to identify the sector."
    )

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            args = [('code', operator, name)]
            return self.search(args, limit=limit).name_get()
        return super(Sector, self).name_search(name=name, args=args,
                                               operator=operator,
                                               limit=limit)
