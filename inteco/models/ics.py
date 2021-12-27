# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Ics(models.Model):
    _name = 'inteco.ics'
    _description = 'The International Classification for Standards'
    _sql_constraints = [
        ('ics_complete_name_unique',
         'UNIQUE(complete_name)',
         "The ICS code must be unique"
         ),
    ]

    name = fields.Char(
        help="ics description.",
        translate=True
    )
    code = fields.Char(
        help="ics code."
    )
    parent_id = fields.Many2one(
        'inteco.ics', string="Parent"
    )
    complete_name = fields.Char(
        compute='_compute_complete_name', store=True,
    )

    @api.depends('code', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for record in self:
            record.complete_name = (
                '%s.%s' % (record.parent_id.complete_name, record.code)
                if record.parent_id else record.code)

    # @api.multi
    # @api.depends('complete_name', 'name')
    # def name_get(self):
    #     result = []
    #     for record in self:
    #         name = "%s - %s" % (record.complete_name, record.name)
    #         result.append((record.id, name))
    #     return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if name and operator in ('=', 'ilike', '=ilike', 'like', '=like'):
            args = [('complete_name', operator, name)]
            return self.search(args, limit=limit).name_get()
        return super(Ics, self).name_search(name=name, args=args,
                                            operator=operator,
                                            limit=limit)
