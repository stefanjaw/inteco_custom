# -*- coding: utf-8 -*-
# pylint: disable=C0103
from odoo import api, models


class Import(models.TransientModel):
    _inherit = 'base_import.import'

    def do(self, fields, columns, options, dryrun=False):
        new_self = self.with_context(dryrun=dryrun)
        return super(Import, new_self).do(fields, columns, options, dryrun=dryrun)
