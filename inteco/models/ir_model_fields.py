# -*- conding: utf8 -*-
from odoo import api, models


# this class and method were copied from odoo
class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    def unlink(self):
        # Prevent the deletion of some `shared` fields... -_-
        social = ('social_instagram',)

        self = self.filtered(
            lambda rec: not (
                (rec.model == 'res.company' and rec.name in social)
                or
                (rec.model == 'res.config.settings' and rec.name == 'auth_signup_uninvited')
            )
        )
        return super(IrModelFields, self).unlink()
