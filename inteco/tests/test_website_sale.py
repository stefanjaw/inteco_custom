# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from ..controllers.main import WebsiteSaleInherit


class TestWebSiteSaleInherit(TransactionCase):

    def test_01_filter_products_by_search_text(self):
        """This test validates the behavior of the method used to filter
        a group of products."""
        product = self.env['product.template'].create({
            'name': 'My New Product',
            'sector_id': self.env.ref('inteco.sector_demo_01').id,
            'committee_id': self.env.ref('inteco.committee_demo_01').id,
            'prefix_id': self.env.ref('inteco.prefix_demo_01').id,
            'correspondence_ids': [(6, 0, [
                self.env.ref('inteco.standard_demo_02').id])],
            'short_code': '22005',
            'process': 'C',
            'application_field': 'My Application Field',
            'website_published': True,
        })

        products = self.env['product.template'].search([])
        website_sale = WebsiteSaleInherit()

        # match by default_code
        self.assertTrue(
            website_sale.filter_products(
                products, product.default_code, 'default_code'),
            "There should be a match by code."
        )

        # match by name
        self.assertTrue(
            website_sale.filter_products(
                products, product.name, 'name'),
            "There should be a match by name."
        )

        # match by sector
        self.assertTrue(
            website_sale.filter_products(
                products, product.sector_id.name, 'sector_id.name'),
            "There should be a match by sector name."
        )

        # match by correspondence
        self.assertTrue(
            website_sale.filter_products(
                products, product.correspondence_ids[0].name,
                'correspondence_ids.name'),
            "There should be a match by sector correspondence."
        )

        # match by committee
        self.assertTrue(
            website_sale.filter_products(
                products, product.committee_id.name, 'committee_id.name'),
            "There should be a match by committee name."
        )

        # match by application field
        self.assertTrue(
            website_sale.filter_products(
                products, product.application_field, 'application_field'),
            "There should be a match by application field."
        )
