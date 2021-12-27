# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Committee(models.Model):
    _name = 'inteco.committee'
    _description = 'The organisms within INTECO in charge of standardization\
        work'
    _sql_constraints = [
        ('committee_complete_name_unique',
         'UNIQUE(complete_name)',
         "The committee code must be unique"),
    ]

    name = fields.Char(
        required=True,
        help="committee description."
    )
    type = fields.Selection([
        ('CNN', 'National Standards Commission'),
        ('CTN', 'Technical Committee'),
        ('CTP', 'Technical Committee Private'),
        ('SC', 'Subcommittee'),
        ('GT', 'Workgroup'),
    ], required=True, help="levels of the hierarchy.")
    identifier = fields.Char(
        help="numerical or alphabetical identifier."
    )
    parent_id = fields.Many2one(
        'inteco.committee', string="Parent"
    )
    sector_id = fields.Many2one(
        'inteco.sector', string="Sector", required=True)
    international = fields.Boolean(
        help="Is it a representation of an international committee?."
    )
    international_committe = fields.Char(
        help="name of the international committee."
    )
    international_participation = fields.Selection([
        ('P', 'Participant'),
        ('O', 'Observer'),
    ], help="level of participation.")
    complete_name = fields.Char(
        compute='_compute_complete_name', store=True,
    )

    @api.depends('type', 'identifier', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for record in self:
            record.complete_name = (
                '%s %s %s' % (record.parent_id.complete_name, record.type,
                              record.identifier or '') if record.parent_id else
                '%s %s' % (record.type, record.identifier or '')).strip()

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
        return super(Committee, self).name_search(name=name, args=args,
                                                  operator=operator,
                                                  limit=limit)
