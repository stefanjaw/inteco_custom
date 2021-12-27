# -*- coding: utf-8 -*-

import collections
from mock import patch
from odoo import http
from odoo.tests.common import HttpCase


class TestWebsiteCrm(HttpCase):

    def test_01_complaint_form_ticket(self):
        """This test validates that when a new ticket is generated through the
        website complaint form, the ticket type id is automatically assigned,
        and for those cases when the ticket is a complaint the description
        field is joined with the complaint text field."""
        complaint_type = self.env.ref('inteco.type_complaint')
        complaint_team = self.env.ref('inteco.helpdesk_complaint')

        with patch.object(http, 'request') as request:
            request.env = self.env
            request.session = self.session
            request.params = collections.OrderedDict([
                ('partner_name', 'jhon doe'),
                ('partner_email', 'jhon@domain.com'),
                ('name', 'subject'),
                ('description', 'description text'),
                ('team_id', complaint_team.id),
                ('ticket_type_id', complaint_type.id),
                ('complaint_text', 'pertinent actions'),
            ])

            values = self.env['helpdesk.ticket'].website_form_input_filter(
                request, dict(request.params))
            ticket = self.env['helpdesk.ticket'].create(values)
            self.assertEqual(
                ticket.ticket_type_id.id, complaint_type.id,
                "Wrong value for ticket type field."
            )
            self.assertEqual(
                ticket.description, '\n'.join([
                    request.params.get('description'),
                    request.params.get('complaint_text')]),
                "The description must also contain the complaint text."
            )
