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

{
    'name': 'Eventos: Personalizaciones de INTECO',
    'version': '17.08.21.1',
    'author': 'DelfixCR',
    'license': 'OPL-1',
    'support': 'soporte@delfixcr.com',
    'website': 'https://www.delfixcr.com',
    'category': 'Event',
    'description':
        '''
        Eventos: Personalizaciones de INTECO
        ''',
    'depends': [
        'base',
        'event',
        'website_event_questions',
        'website_event',
    
    ],
    'data': [
        'views/assets.xml',
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/inteco_event_inherit.xml',
        'views/registration_attendee.xml',
        'views/new_fields_web.xml'
    ],
    'installable': True,
}
