# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import ValidationError


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def action_feedback(self, feedback=False, attachment_ids=None):
        """Before marking an opportunity activity as done it is verified if it
        meets certain prerequisites."""
        activity = self.activity_type_id.id

        # Activities to be validated before being marked as done
        activities = {
            'data_register':
                self.env.ref('inteco.mail_activity_data_register').id,
            'seller_assign':
                self.env.ref('inteco.mail_activity_seller_assignment').id,
            'adjust_sale':
                self.env.ref('inteco.mail_activity_adjustment_amount_sale').id,
        }

        if activity not in activities.values():
            return super(MailActivity, self).action_feedback()

        warnings = []
        lead = self.env['crm.lead'].browse(self.res_id)

        # Validation for seller assignment activity
        if activity == activities.get('seller_assign') and not lead.user_id:
            raise ValidationError(
                _("You must assign a Salesperson to mark this activity as "
                  "done.")
            )

        if lead.type == 'lead':
            # These fields cannot be filled within the opportunity so they
            # should be required only if it's a lead
            # Part of data register activity validation
            warnings.extend([
                (not lead.contact_name, _("Specify the Contact Name.")),
                (not lead.email_from, _("Specify the Email.")),
            ])

        if lead.type == 'opportunity':

            # A planned closing date should have been specified
            # Part of data register activity validation
            warnings.extend([
                (not lead.date_deadline, _("Specify the Expected Closing."))
            ])

            # Validation for adjustment amount of sale activity
            if activity == activities.get('adjust_sale') and\
                    not lead.expected_revenue:
                raise ValidationError(
                    _("You must specify the expected revenue to mark this "
                      "activity as done.")
                )

        # Validation for data register activity
        # Fields that should have been filled
        warnings.extend([
            (not lead.country_id, _("Specify the Country.")),
            (not lead.campaign_id, _("Specify the Campaign.")),
            (not lead.medium_id, _("Specify the Medium.")),
            (not lead.source_id, _("Specify the Source.")),
        ])

        messages = [msg for value, msg in warnings if value]

        if activity == activities.get('data_register') and messages:
            raise ValidationError(
                _("To mark this activity as done you must meet the following "
                  "requirements: \n- %s") % ('\n- '.join(messages)))

        return super(MailActivity, self).action_feedback()
