# -*- coding: utf-8 -*-

import base64

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import safe_eval


class TestProduct(TransactionCase):

    def setUp(self):
        super().setUp()
        self.new_edition = self.env['product.new.edition'].create({
            'pages': '1',
            'approval_date': fields.Date.from_string('2010-05-01'),
            'standards_ref': 'ISO C39',
        })
        self.template = self.env['product.template'].create({
            'name': 'New product template',
            'sector_id': self.env.ref('inteco.sector_demo_01').id,
            'committee_id': self.env.ref('inteco.committee_demo_01').id,
            'prefix_id': self.env.ref('inteco.prefix_demo_01').id,
            'short_code': '22005',
            'process': 'C',
            'approval': fields.Date.from_string('2009-12-18'),
            'website_published': True,
        })
        self.confirm = self.env['product.confirm'].create({
            'confirmation_date': fields.Date.from_string('2018-06-03'),
        })

    def create_portal_file(self, product, values=None):
        """ Creates a portal file attachment whose content is a dummy PDF
        """
        if values is None:
            values = {}
        filename = "attachment" + str(product.attachment_count + 1)
        datas = base64.b64encode(b'%PDF-1.4')
        attachment_values = {
            'name': filename,
            'datas': datas,
            'datas_fname': filename,
        }
        attachment_values.update(values)
        ctx = safe_eval(product.action_open_attachments().get('context'))
        attachment = product.env['ir.attachment'].with_context(
            ctx).create(attachment_values)
        product.refresh()
        return attachment

    def test_01_product_history(self):
        """This test verifies the correctness of the method that generates the
        history for a specific product."""
        self.new_edition.with_context({
            'active_id': self.template.product_variant_id.id
        }).action_create_edition()

        self.assertEqual(
            len(self.template.product_history()), 2,
            "The product history has not been generated correctly.")

        self.assertEqual(
            self.template.product_history(filterby='current'),
            self.template.product_variant_id.replaced_by,
            "The product is not the current.")

        self.template.product_variant_id.update({
            'replaced_by': self.template.product_variant_id.id})

        self.assertEqual(
            len(self.template.product_history()), 1,
            "The product history has not been generated correctly.")

    def test_02_confirm_product(self):
        """This test validates the confirmation process of a product."""
        self.confirm.with_context({
            'active_id': self.template.product_variant_id.id
        }).action_confirm_product()

        self.assertEqual(
            self.template.product_variant_id.confirmation_date,
            self.confirm.confirmation_date,
            "The confirmation date is wrong."
        )

    def test_03_portal_file_publish_on_website(self):
        """ Validates that a product may be published on website only if it has
            an associated portal file
        """
        product1 = self.template.product_variant_id
        product2 = product1.copy()
        self.create_portal_file(product1)

        # Publish product with one portal file, it should not fail
        action = product1.website_publish_button()
        self.assertTrue(
            action,
            "An action was not gotten after publishing product on website")

        # Publish product without portal files, it should fail
        error_msg = "you must first attach a portal file"
        with self.assertRaisesRegexp(ValidationError, error_msg):
            product2.website_publish_button()

    def test_04_one_portal_file_per_product(self):
        """ Validates that a product may contain at most one portal file,
            unless you're the user "admin" (not a member of administrators)
        """
        user = self.env.ref('base.user_demo')
        user.groups_id |= self.env.ref('base.group_system')
        product1 = self.template.product_variant_id
        product2 = product1.copy().sudo(user=user)

        # Create two portal files as admin, it should not fail
        self.create_portal_file(product1)
        self.create_portal_file(product1)

        # Create two portal files as a regular user, it should fail
        error_msg = "You can attach only one portal file per product"
        self.create_portal_file(product2)
        with self.assertRaisesRegexp(ValidationError, error_msg):
            self.create_portal_file(product2)

    def test_05_approval_date_change(self):
        """Validate the restrictions in the change of the approval date of
        a standard."""
        product = self.template.product_variant_id

        # confirm the standard
        confirmation = self.env['product.confirm'].create({
            'confirmation_date': fields.Date.from_string('2011-12-18'),
        })
        confirmation.with_context({
            'active_id': product.id
        }).action_confirm_product()

        # create a new variant of the standard
        new_variant = self.env['product.use.variant'].create({
            'pages': '1',
            'approval_date': fields.Date.from_string('2012-12-18'),
            'standards_ref': 'ISO C39',
        })
        new_variant.with_context({
            'active_id': product.id,
            'modifier': self.env.ref('inteco.attribute_modifier_cor').id,
        }).action_create_new_variant()

        product.update({
            'approval': fields.Date.from_string('2018-12-18')
        })

        message = ".*greater than the modifier date*."
        with self.assertRaisesRegexp(ValidationError, message):
            product._onchange_approval()

        product.update({
            'approval': fields.Date.from_string('2011-12-28')
        })

        message = ".*greater than the current confirmation*."
        with self.assertRaisesRegexp(ValidationError, message):
            product._onchange_approval()
