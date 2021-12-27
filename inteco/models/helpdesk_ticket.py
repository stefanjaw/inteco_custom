# -*- coding: utf-8 -*-

from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    complaint_text = fields.Text(
        help="Used as a complementary for description field when the ticket\
        type is Complaint",
    )

    def website_form_input_filter(self, request, values):
        """Allows associate to the ticket a specific type and, for complaint
        cases, add additional information to the description field."""
        complaint_id = self.env.ref('inteco.type_complaint').id
        form_type_id = int(request.params.get('ticket_type_id', False))
        form_complaint_text = request.params.get('complaint_text')
        form_description = request.params.get('description')

        values.update({
            'ticket_type_id': form_type_id,
        })
        if form_type_id == complaint_id and form_complaint_text:
            values.update({
                'description': '\n'.join([
                    form_description, form_complaint_text]),
            })
        return values
