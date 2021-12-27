# -*- coding: utf-8 -*-
##############################################################################
#
#	Odoo Open Source Management Solution
#	Copyright (c) 2021 DIS S.A. (http://www.delfixcr.com) All Rights Reserved.
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU Affero General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU Affero General Public License for more details.
#
#	You should have received a copy of the GNU Affero General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _


class EventOrg(models.Model):
    _name = "event.organizer"
    _description = 'Organizadores del eventos'
    _rec_name = 'org_name'

    org_name = fields.Char(string="Nombre", required=True)
    site_name = fields.Char(string="Sitio Web", required=True, help="No olvidar usar https:// o http://")
    site_logo = fields.Binary(string="Logo", required=True)
