# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestCrm(TransactionCase):
    """Test cases for crm models"""

    def setUp(self):
        super(TestCrm, self).setUp()
        self.lead_model = self.env['crm.lead']

    def create_lead(self, values=None):
        values = values or {}
        lead_values = {
            'type': "lead",
            'name': "Test lead new",
            'contact_name': 'John Doe',
            'email_from': 'john.doe@domain.com',
            'partner_name': 'Vauxoo S.A.',
        }
        lead_values.update(values)
        lead = self.lead_model.create(lead_values)
        return lead

    def test_01_incomplete_lead_to_opportunity(self):
        """This test validates that an incomplete lead cannot be converted to
        an opportunity."""
        new_lead = self.create_lead({
            'contact_name': False,
            'email_from': False,
        })
        error_msg = 'To convert to an opportunity you must'
        with self.assertRaisesRegexp(ValidationError, error_msg):
            new_lead.lead_to_opportunity()

    def test_02_change_sales_channel(self):
        """This test validates that when the sales channel of an opportunity
        is changed, automatically the stage is set to the first stage of the
        selected channel."""
        general_team = self.env.ref('inteco.team_general_department')
        general_stage = self.env.ref('inteco.stage_general_new')
        new_lead = self.create_lead()
        new_lead.lead_to_opportunity()
        new_lead.activity_ids.unlink()
        new_lead.write({
            'team_id': general_team.id,
        })
        self.assertEqual(
            new_lead.stage_id.id, general_stage.id,
            "The opportunity was assigned to the wrong stage.")

    def test_03_compute_contact_name(self):
        """This test verifies that the _compute_contact_name works correctly"""
        lead = self.create_lead({
            'first_name': 'richard',
            'last_name': 'lewis',
        })
        lead._onchange_full_name()
        self.assertEqual(
            lead.contact_name, 'Richard Lewis',
            "Contact's name was not computed correctly")
        lead.second_last_name = 'lee'
        lead._onchange_full_name()
        self.assertEqual(
            lead.contact_name, 'Richard Lewis Lee',
            "Contact's name was not computed correctly")

    def test_04_activity_deadline_without_weekends(self):
        """Validates that, when an activity is created from an lead, the
            deadline is calculated without taking into account weekend days
        """
        new_lead = self.create_lead()
        activity = self.env.ref('inteco.mail_activity_adjustment_amount_sale')
        activity.days = 7
        new_lead.stage_id.default_activities_ids = activity
        # `today` method needs to be patched, so the results may be predictable
        patcher = patch(
            'odoo.addons.inteco.models.crm_lead.Date', wraps=fields.Date)
        mock_date = patcher.start()
        mock_date.today.return_value = '2010-01-01'
        new_lead.new_automatic_activity(
            new_lead.stage_id.default_activities_ids)
        patcher.stop()
        automatic_activity = self.env['mail.activity'].search([
            ('activity_type_id', '=', activity.id),
        ])
        self.assertEqual(
            len(automatic_activity), 1,
            "There should be created exactly one automatic activity")
        # 2010-01-01 is friday, so 7 working days ahead would cover 2 weekends
        # 7 + 2 + 2 = 11 days ahead, i.e. 2010-01-12
        self.assertEqual(
            automatic_activity.date_deadline, '2010-01-12',
            "Activity's deadline was not calculated correctly")

    def test_05_crm_lost(self):
        """that Validates, when a lead is lost, the company name which the lead
            was lost may be set in the reason, and that the company name is set
            automatically in the lead
        """
        new_lead = self.create_lead()
        ctx = {'active_ids': new_lead.ids}
        lead_lost = self.env['crm.lead.lost'].with_context(ctx).create({
            'lost_company_name': 'Smartmatic',
        })
        lead_lost.action_lost_reason_apply()
        self.assertEqual(new_lead.lost_company_name, 'Smartmatic')

    def test_06_lead_stages(self):
        """This validates all lead stages work correctly and all fields are
            set properly in all of them:
            - Create a lead
            - Convert it to opportunity
            - Set it as won
        """
        lead = self.create_lead()

        # Convert the lead to opportunity
        action = lead.lead_to_opportunity()
        expected_action = self.env.ref(
            'crm.action_crm_lead2opportunity_partner').read()[0]
        self.assertDictEqual(
            action, expected_action,
            "The action to set lead to opportunity was not gotten")
        wizard_model = self.env[action['res_model']]
        ctx = {'active_ids': lead.ids}
        convert_wizard = wizard_model.with_context(ctx).create({
            'name': 'convert',
        })
        convert_wizard.action_apply()
        self.assertEqual(
            lead.type, 'opportunity',
            "The lead was not converted to opportunity")

        # Tests contact's fields
        contact = lead.partner_id
        self.assertTrue(contact, "The partner for the contact was not created")
        self.assertEqual(
            contact.name, "John Doe", "Contact's name was not set correctly")
        self.assertEqual(
            contact.email, "john.doe@domain.com",
            "Contact's email was not set correctly")

        # Tests company's fields
        company = contact.parent_id
        self.assertTrue(
            contact, "The partner for the contact's company was not created")
        self.assertEqual(
            company.name, "Vauxoo S.A.",
            "company's name was not set correctly")
        self.assertFalse(company.email, "Company's email should be blank")

        # Finally, sets the lead as won
        lead.action_set_won()
        self.assertEqual(
            lead.stage_id.name, "Won",
            "Lead stage is not Won after been set to Won")
        self.assertEqual(
            lead.probability, 100,
            "Lead's probability is not 100 after been set to Won")

    def test_07_import_lead(self):
        """Validates that, when leads are created importing them from a file:
            - The responsible of the channel is assigned to the new lead
            - the user who is importing leads is removed from the followers
            - Message tracking is not disabled
        """
        user = self.env.ref('base.user_demo')
        team = self.env.ref('inteco.team_standards_department')
        team.user_id = user
        user.company_id.crm_import_notification_enabled = True
        ctx = {
            'import_file': 'crm.lead.csv',
            'tracking_disable': True,
            'dryrun': False,
        }
        self.lead_model = self.lead_model.with_context(ctx)
        lead = self.create_lead({
            'team_id': team.id,
        })
        self.assertEqual(
            lead.user_id, user, "The user should've been taken from the team")
        self.assertFalse(
            lead.message_is_follower,
            "User who creates the lead should've been removed from followers")
        self.assertNotIn(
            'tracking_disable', lead.env.context,
            "Message tracking shouldn't be disabled")

        # Try now with notification disabled
        user.company_id.crm_import_notification_enabled = False
        new_lead = self.create_lead({
            'team_id': team.id,
        })
        self.assertIn(
            'tracking_disable', new_lead.env.context,
            "Message tracking should be disabled")

    def test_08_partner_from_chatter(self):
        """ Validates that, when a partner is created from a lead's chatter,
            its default values are set correctly
        """
        # Since a partner is created automatically when creating a lead to send
        # them a confirmation email, we need to create it without email and
        # assign it after it's created
        lead = self.create_lead({
            'email_from': False,
        })
        lead.email_from = 'john.doe@domain.com'

        # Call method to resolve recipients, just the way as chatter would do
        partner_info = lead.message_partner_info_from_emails([lead.email_from])
        self.assertEqual(len(partner_info), 1, "Got an unexpected result")

        # Retrieve and validate default values and source model
        context = partner_info[0].get('context')
        self.assertTrue(
            context,
            "a context should've been appended.\nGot: " + str(partner_info))
        self.assertEqual(
            context.get('src_model'), 'crm.lead',
            "Got an unexpected source model")
        self.assertEqual(
            context.get('default_name'), 'John Doe',
            'Got an unexpected contact name')
        parent_id = context.get('default_parent_id')
        self.assertTrue(parent_id, "A company was not created")
        parent = self.env['res.partner'].browse(parent_id)
        self.assertEqual(
            parent.name, "Vauxoo S.A.", 'Got an unexpected company name')

    def test_09_lead_from_email(self):
        """ Validates that a lead is created when an email is received through
            a proper recipient, and that its default values are set correctly,
            including those defined as config parameters
        """
        # Define the team leader for the channel that will be used in the
        # creation of the new lead
        team = self.env['crm.team'].search([
            ('alias_name', '=', 'normas@inteco.org')])
        team.write({
            'user_id': self.env.ref('base.user_demo').id
        })

        # Create campaign, medium and source
        campaign = self.env['utm.campaign'].create({
            'name': 'Campaign Test',
        })
        medium = self.env['utm.medium'].create({
            'name': 'Medium Test',
        })
        source = self.env['utm.source'].create({
            'name': 'Source',
        })

        # Set config parameters to point to the records just created
        config = self.env['res.config.settings'].create({
            'lead_email_campaign_id': campaign.id,
            'lead_email_medium_id': medium.id,
            'lead_email_source_id': source.id,
            'alias_domain': 'inteco.org',
        })
        config.execute()

        # Sends an email so a lead is created
        email_msg = MIMEText("Email body")
        email_msg['From'] = '"John Doe" <john.doe@example.com>'
        email_msg['To'] = 'normas@inteco.org'
        email_msg['Subject'] = 'Subject Test'
        self.env['mail.thread'].message_process(False, email_msg.as_string())

        # Verifies a lead was created with all expected values
        lead = self.lead_model.search([
            ('name', '=', 'Subject Test'),
            ('type', '=', 'lead'),
            ('email_from', '=', 'john.doe@example.com'),
            ('campaign_id', '=', campaign.id),
            ('medium_id', '=', medium.id),
            ('source_id', '=', source.id),
            ('contact_name', '=', 'John Doe'),
            ('first_name', '=', 'John'),
            ('last_name', '=', 'Doe'),
            ('second_last_name', '=', False)
        ])

        # Assign leader by default to the lead
        action = self.env.ref('inteco.crm_assign_leader_by_default')
        action_on_create = action.with_context({
            'active_model': 'crm.lead',
            '__action_done': {},
            'active_id': lead.id,
            'active_ids': [lead.id],
        })
        action_on_create._process(lead)

        self.assertEqual(
            lead.user_id.id, team.user_id.id,
            "The leader assign to the lead is wrong."
        )

        self.assertTrue(
            lead, "A lead should've been created after the email was received")

    def test_10_change_to_unrelated_stage(self):
        """This test validates that a lead cannot be changed to a stage that
        is not related with it defined team"""
        lead = self.create_lead()

        message = 'This stage is not related with *.'
        with self.assertRaisesRegexp(ValidationError, message):
            lead.write({
                'stage_id': self.env.ref('inteco.stage_general_new').id,
            })

    def test_11_invalid_contact_name(self):
        """ Validates that an exception is raised when a contact name contains
            numbers
        """
        lead = self.create_lead()
        error_msg = "Contact's name may not contain numbers. Please, try again"
        with self.assertRaisesRegexp(ValidationError, error_msg):
            lead.contact_name = "John Do3"
