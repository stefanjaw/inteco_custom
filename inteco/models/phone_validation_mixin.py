# -*- coding: utf-8 -*-

from odoo import models
from odoo.addons.phone_validation.tools import phone_validation


class PhoneValidationMixin(models.AbstractModel):

    _inherit = 'phone.validation.mixin'

    def phone_format(self, number, country=None, company=None, raise_exception=False):
        """
        Se agrega el parametro raise_exception que viene de la migracion y esta adaptado a la version 14
        """
        country = country or self._phone_get_country()
        if not country:
            return number
        return phone_validation.phone_format(
            number,
            country.code if country else None,
            country.phone_code if country else None,
            force_format='INTERNATIONAL',
            raise_exception=raise_exception
        )
