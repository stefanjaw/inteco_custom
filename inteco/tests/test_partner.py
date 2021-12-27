# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestPartner(TransactionCase):
    """Test cases for the partner model"""

    def setUp(self):
        super(TestPartner, self).setUp()
        self.partner_model = self.env['res.partner']

    def test_01_fill_automatically_individual_partner_name(self):
        """This test validates that the partner name is automatically filled
        when the contact_name, contact_last_name or second_last_name fields are
        modified and the partner is not a company
        """
        partner = self.partner_model.create({
            'name': 'Test partner',
            'is_company': True,
        })

        partner.update({
            'contact_name': 'john',
            'contact_last_name': 'doe',
        })
        partner._onchange_full_name()

        self.assertEqual(
            partner.name, 'Test partner',
            "The partner name should remain unchanged.")

        partner.update({
            'is_company': False,
        })
        partner._onchange_full_name()

        self.assertEqual(
            partner.name, 'John Doe',
            "The partner name should be a combination of contact_name and "
            "contact_last_name fields.")

        partner.second_last_name = 'lee'
        partner._onchange_full_name()
        self.assertEqual(
            partner.name, 'John Doe Lee',
            "The partner name should be a combination of all names")

    def test_02_exporting_permissions(self):
        """Validates that only members of the group 'Export Data' may export
            partner data
        """
        user = self.env['res.users'].create({
            'name': 'Test user',
            'login': 'test_user',
            'email': 'test@inteco.org',
            'company_id': self.env.ref('base.main_company').id,
            'groups_id': [(6, 0, [self.ref('base.group_user')])]
        })
        partners = self.partner_model.search([], limit=5).sudo(user=user)
        exported_fields = ('id', 'name')
        # firstly, we try to export without belonging to the group, should fail
        error_msg = ('Only users from the group "Exporting Permissions" may '
                     'export data')
        with self.assertRaisesRegexp(UserError, error_msg):
            partners.export_data(exported_fields)
        # Then, we try again belonging to the group, this time should not fail
        self.env.ref('inteco.group_export_data').users |= user
        exported_data = partners.export_data(exported_fields)
        self.assertTrue(exported_data, "Data were not exported")
        self.assertEqual(
            len(exported_data['datas']), 5,
            "Data were not exported for all partners")

    def test_03_split_full_name(self):
        """ Validates that the method split_full_name works correctly.
            It covers five cases, from one to five words
        """
        split_full_name = self.partner_model.split_full_name
        self.assertTupleEqual(
            split_full_name("Name"),
            ("Name", False, False))
        self.assertTupleEqual(
            split_full_name("Name Lastname"),
            ("Name", "Lastname", False))
        self.assertTupleEqual(
            split_full_name("Name Lastname1 Lastname2"),
            ("Name", "Lastname1", "Lastname2"))
        self.assertTupleEqual(
            split_full_name("Name1 Name2 Lastname1 Lastname2"),
            ("Name1 Name2", "Lastname1", "Lastname2"))
        self.assertTupleEqual(
            split_full_name("Name1 Name2 Name3 Lastname1 Lastname2"),
            ("Name1 Name2 Name3", "Lastname1", "Lastname2"))

    def test_04_view_partner_from_lead_chatter(self):
        """ Validates that the proper form view is used when a partner is
            created from a lead's chatter
        """
        custom_view = self.env.ref('inteco.view_partner_simple_form_lead')

        # In a regular case, the custom view should not be returnedsed
        view = self.partner_model._fields_view_get()
        self.assertNotEqual(
            view.get('view_id'), custom_view.id,
            "Custom view should be used only when creating partner from lead")

        # Try the same, setting the context just the same way as the lead's
        # chatter would do
        ctx = {
            'src_model': 'crm.lead',
            'ref': 'compound_context',
        }
        view = self.partner_model.with_context(ctx)._fields_view_get()
        self.assertEqual(
            view.get('view_id'), custom_view.id,
            "Custom view should be used when creating partner from lead")

    def test_05_create_partner_without_names(self):
        """ Validates that, when a person is created and neither its fields
            first name, last name nor second last name are provided, they are
            filled parsing them from the full name, and only if it's a person
        """
        par = self.partner_model.create({
            'name': 'John Doe Lee',
            'is_company': True,
        })
        self.assertTupleEqual(
            (par.contact_name, par.contact_last_name, par.second_last_name),
            (False, False, False),
            "None of the person's names should be set")
        par = self.partner_model.create({
            'name': 'John Doe Lee',
        })
        self.assertTupleEqual(
            (par.contact_name, par.contact_last_name, par.second_last_name),
            ('John', 'Doe', 'Lee'),
            "Names were not parsed correctly")

    def test_06_create_user_existing_partner(self):
        """ Validates that, when an user is created for an already existing
            partner, the partner is assigned automatically
        """
        partner = self.partner_model.create({
            'name': 'John Doe',
            'email': 'john.doe@example.com',
        })
        user = self.env['res.users'].create({
            'name': 'Should not matter',
            'email': 'John.Doe@example.com',
            'login': 'jdoe',
        })
        self.assertEqual(
            user.partner_id, partner,
            "Partner was not assigned when the user was created")

    def test_07_invalid_name(self):
        """ Validates that an exception is raised when a partner name contains
            numbers, and that it's raised only if the partner is not a company
        """
        partner_person = self.partner_model.create({
            'name': 'John Doe',
            'is_company': False,
        })
        partner_company = self.partner_model.create({
            'name': 'Test partner',
            'is_company': True,
        })

        # Sets a name containing numbers to the company, it should not fail
        partner_company.name = "John Do3"

        # Does the same with the person, it should fail
        error_msg = "The name may not contain numbers. Please, try again."
        with self.assertRaisesRegexp(ValidationError, error_msg):
            partner_person.name = "John Do3"
