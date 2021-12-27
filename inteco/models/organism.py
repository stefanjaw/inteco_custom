# -*- coding: utf-8 -*-

from odoo import fields, models


class Organism(models.Model):
    _name = 'inteco.organism'
    _description = 'The external organizations responsible for creating new\
        standards'
    _sql_constraints = [
        ('organism_name_unique',
         'UNIQUE(name)',
         "The organism name must be unique"),
    ]

    name = fields.Char(
        help="acronym of the organism."
    )
    correspondence_ids = fields.One2many(
        'inteco.organism.standard', 'organism_id', string="Correspondence")
    website = fields.Char(
        help="Website of Organism."
    )


class OrganismStandard(models.Model):
    _name = 'inteco.organism.standard'
    _description = 'The standards associated to an specific organism'
    _sql_constraints = [
        ('standard_name_unique',
         'UNIQUE(name)',
         "The code for a correspondence must be unique"),
    ]

    name = fields.Char(
        help="document number"
    )
    organism_id = fields.Many2one(
        'inteco.organism', string="Organism")
    website = fields.Char(
        help="Website of Standard."
    )
