# -*- coding: utf-8 -*-
# Copyright 2016 Vauxoo
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import base64
import io
from werkzeug.utils import redirect

from odoo import fields, http, tools, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import AccessError
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.website_sale_digital.controllers.main import WebsiteSaleDigital
from odoo.addons.website_sale.controllers.main import WebsiteSale, TableCompute # TODO, PPG, PPR
from ..models.product import STANDARD_STATES
from werkzeug.exceptions import Forbidden, NotFound

_logger = logging.getLogger(__name__)

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
except (ImportError, IOError) as err:
    _logger.debug(err)


class WebsiteSaleInherit(WebsiteSale):

    def _checkout_form_save(self, mode, checkout, all_values):
        if all_values.get('contact_last_name'):
            name = all_values.get('contact_name', '') + ' ' + \
                   all_values.get('contact_last_name') + ' ' + \
                   all_values.get('second_last_name')
            checkout['name'] = name
        return super(WebsiteSaleInherit, self)._checkout_form_save(mode, checkout, all_values)
    
    @http.route('/shop/products/autocomplete', type='json', auth='public', website=True)
    def products_autocomplete(self, term, options={}, **kwargs):
        """
        Returns list of products according to the term and product options
    
        Params:
            term (str): search term written by the user
            options (dict)
                - 'limit' (int), default to 5: number of products to consider
                - 'display_description' (bool), default to True
                - 'display_price' (bool), default to True
                - 'order' (str)
                - 'max_nb_chars' (int): max number of characters for the
                                        description if returned
    
        Returns:
            dict (or False if no result)
                - 'products' (list): products (only their needed field values)
                        note: the prices will be strings properly formatted and
                        already containing the currency
                - 'products_count' (int): the number of products in the database
                        that matched the search query
        """
        ProductTemplate = request.env['product.template']
        
        display_description = options.get('display_description', True)
        display_price = options.get('display_price', True)
        order = self._get_search_order(options)
        max_nb_chars = options.get('max_nb_chars', 999)
        
        category = options.get('category')
        attrib_values = options.get('attrib_values')
        
        domain = self._get_search_domain(term, category, attrib_values, display_description)
        products = ProductTemplate.search(
            domain,
            limit=min(20, options.get('limit', 5)),
            order=order
        )
        
        fields = ['id', 'name', 'website_url', 'default_code']
        if display_description:
            fields.append('description_sale')
        
        res = {
            'products': products.read(fields),
            'products_count': ProductTemplate.search_count(domain),
        }
        
        if display_description:
            for res_product in res['products']:
                desc = res_product['description_sale']
                if desc and len(desc) > max_nb_chars:
                    res_product['description_sale'] = "%s..." % desc[:(max_nb_chars - 3)]
        
        
        if display_price:
            FieldMonetary = request.env['ir.qweb.field.monetary']
            monetary_options = {
                'display_currency': request.website.get_current_pricelist().currency_id,
            }
            for res_product, product in zip(res['products'], products):
                combination_info = product._get_combination_info(only_template=True)
                res_product.update(combination_info)
                res_product['list_price'] = FieldMonetary.value_to_html(res_product['list_price'], monetary_options)
                res_product['price'] = FieldMonetary.value_to_html(res_product['price'], monetary_options)
                res_product['default_code'] = res_product['default_code']
                default_code = res_product.get('default_code', False)
                if default_code:
                    default_code = '['+str(default_code)+']'
                    res_product['name'] = default_code + " " +res_product['name']
        
        return res


    def sort_products(self, unsorted_products):
        """Receives a group of products and sort them according to the position
        of the elements inside the category_id and STANDARD_STATES lists."""
        sorted_products = request.env['product.template']
        category_ids = [
            request.env.ref('inteco.public_category_management').id,
            request.env.ref('inteco.public_category_product').id,
            request.env.ref('inteco.public_category_testing').id,
            request.env.ref('inteco.public_category_guide').id,
            request.env.ref('inteco.public_category_normative').id,
            request.env.ref('inteco.public_category_vocabulary').id
        ]
        if len(unsorted_products) == 1:
            return unsorted_products
        # Sort process by state -> category -> date
        for state in STANDARD_STATES:
            products_by_state = unsorted_products.filtered(
                lambda r: r.state == state[0])
            for category_id in category_ids:
                # A category must be divided into category with and without
                # approval date to avoid a possible 'unorderable types' error
                # when a record doesn't have defined an approval date.
                category_with = products_by_state.filtered(
                    lambda r:
                    r.approval and category_id in r.public_categ_ids.ids)
                category_without = products_by_state.filtered(
                    lambda r:
                    not r.approval and category_id in r.public_categ_ids.ids)
                sorted_products += category_with.sorted(
                    'approval', reverse=True) + category_without
        return sorted_products

    def custom_filters_values(self, rqst):
        """Verifies which of the custom filters were selected when a search is
        performed in the products catalog, then this information is used to
        keep the elements associated with its values using the t-att-selected
        attribute in the template."""
        values = {}
        sector = rqst.httprequest.args.get('sector', False)
        committee = rqst.httprequest.args.get('committee', False)
        organism = rqst.httprequest.args.get('organism', False)
        # keywords = rqst.httprequest.args.get('key_words', False)
        # Fills the list dynamically by asking for each state defined in the
        # STANDARD_STATE list. In this way, we ensure that if a new state is
        # defined it is considered as a possible filter.
        states = [
            rqst.httprequest.args.get(
                'state_%s' % (state[0]), False) for state in STANDARD_STATES]
        if sector:
            values['sector_set'] = sector
        if committee:
            values['committee_set'] = committee
        if organism:
            values['organism_set'] = organism
        if 'category' in rqst.httprequest.base_url:
            # Gets the id of the chosen category.
            # The id is included in the base URL as follows: category-name-id.
            # E.g.: http://host/shop/category/standards-normative-document-2
            values['category_set'] = rqst.httprequest.base_url[-1]
        # if keywords:
        #     values['keywords_set'] = keywords
        selected_states = list(filter(None, states))
        if selected_states:
            values['states_set'] = selected_states
        return values

    def filter_products(self, products, text, field, exclude=None):
        """ Given a products recordset, returns a new recordset that contain all
            the coincidences of the form 'text in field', excluding those
            passed in ``exclude``
        """
        domain = [
            ('id', 'in', products.ids),
            (field, 'ilike', text),
        ]
        if exclude:
            domain.append(('id', 'not in', exclude.ids))
        return products.search(domain)

    def _get_compute_currency(self, pricelist, product=None):
        company = product and product._get_current_company(pricelist=pricelist, website=request.website) or pricelist.company_id or request.website.company_id
        from_currency = (product or request.env['res.company']._get_main_company()).currency_id
        to_currency = pricelist.currency_id
        return lambda price: from_currency._convert(price, to_currency, company, fields.Date.today())
    
    
    def _get_compute_currency_and_context(self, product=None):
        pricelist_context, pricelist = self._get_pricelist_context()
        compute_currency = self._get_compute_currency(pricelist, product)
        return compute_currency, pricelist_context, pricelist
    
    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        """By user request, when a search is performing in the products catalog
        the returned data must be sorted by default as follows:

            1. Current state
                1.1 Management system category
                    1.1.1 approval date 01-01-2018
                    1.1.2 approval date 02-01-2018
                1.2 Testing method category
                    1.2.1 approval date 12-01-2017
                    1.2.2 approval date 01-01-2018
                ...
                1.6 category name
            2. Public consultation state
                1.1 Management system
                    1.1.1 approval date 01-01-2018
                    1.1.2 approval date 02-01-2018
                1.2 Testing method category
                    1.2.1 approval date 12-01-2017
                    1.2.2 approval date 01-01-2018
                ...
                1.6 category name
            ...
            3. Replaced state
                ...

        Summarizing, first sort the results by state, then sort each stage by
        category, and finally, sort each state/category by approval date.

        This was copied from:
        https://github.com/odoo/odoo/blob/0050019390daa759ac5882ded79a6ee50ab4749e/
        addons/website_sale/controllers/main.py#L211

        In the original definition of this method, the result of the search is
        returned in groups with a generic order, due to this limitation it is
        more convenient to overwrite the method instead of inheriting it.
        """
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[
            int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}

        domain = self._get_search_domain(search, category, attrib_values)

        keep = QueryURL(
            '/shop', category=category and int(category), search=search,
            attrib=attrib_list, order=post.get('order'))

        compute_currency, __, pricelist = (
            self._get_compute_currency_and_context())

        request.context = dict(
            request.context, pricelist=pricelist.id,
            partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if category:
            category = request.env['product.public.category'].browse(
                int(category))
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            post['attrib'] = attrib_list

        categs = request.env['product.public.category'].search([
            ('parent_id', '=', False),
        ])
        product_model = request.env['product.template']

        parent_category_ids = []
        if category:
            parent_category_ids = [category.id]
            current_category = category
            while current_category.parent_id:
                parent_category_ids.append(current_category.parent_id.id)
                current_category = current_category.parent_id

        product_count = product_model.search_count(domain)
        pager = request.website.pager(
            url=url, total=product_count, page=page, step=ppg, scope=7,
            url_args=post)

        # Empty recordset that will contain a subset of products.
        products = request.env['product.template']

        # Empty recordset that will contain the sorted products.
        sorted_products = request.env['product.template']

        # Originally this operation was performing using the search method
        # with a limit and offset, getting a small group of records.
        # Now we get all the records to sorter then according to the premises
        # mentioned above.
        search_results = product_model.search(
            domain, order=self._get_search_order(post))

        # All fields for which we'll need to filter the search results.
        field_names = []
        if search:
            field_names.extend([
                'default_code', 'name', 'sector_id.name',
                'correspondence_ids.name', 'committee_id.name',
                'application_field',
            ])

        # Extracts groups from the search results depending on the defined
        # field names and order them.
        for field_name in field_names:
            match = self.filter_products(
                search_results, search, field_name, sorted_products)
            sorted_products |= self.sort_products(match)
        sorted_products |= search_results

        if search and sorted_products:
            # All current standards must be shown in the first places.
            current = sorted_products.filtered(
                lambda r: r.product_variant_id.state == 'C')
            # Finally we must order the current standards ones by priority
            current = current.sorted(
                key=lambda r: r.product_variant_id.priority, reverse=True)
            sorted_products = current | sorted_products

        # Slice of the sorted products depending on the pager offset and
        # the products per page.
        # E.g. located on the third page we get:
        #   ordered_products[40 : 40 + 20]
        products = sorted_products[pager['offset']:pager['offset'] + ppg]

        product_attribute_model = request.env['product.attribute']
        if products:
            # get all products without limit
            selected_products = product_model.search(domain, limit=False)
            attributes = product_attribute_model.search([
                ('attribute_line_ids.product_tmpl_id', 'in',
                 selected_products.ids)
            ])
        else:
            attributes = product_attribute_model.browse(attributes_ids)

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg),
            'rows': PPR,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'parent_category_ids': parent_category_ids,
        }

        additional_values = self.custom_filters_values(request)
        if additional_values:
            values.update(additional_values)

        if category:
            values['main_object'] = category
        return request.render("website_sale.products", values)

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        response = super(WebsiteSaleInherit, self).product(
            product, category=category, search=search, **kwargs)
        variant = product.id
        if kwargs.get('variant'):
            try:
                product_id = int(kwargs.get('variant'))
                variant = http.request.env['product.template'].sudo().browse(
                    product_id)
            except (ValueError, AccessError):
                _logger.exception("Couldn't load variant use template instead")
        response.qcontext.update({'variant': variant})
        return response

    def _get_search_domain(self, search, category, attrib_values, aux=None):
        domain = super(WebsiteSaleInherit, self)._get_search_domain(
            search, category, attrib_values)
        sector = request.httprequest.args.get('sector')
        committee = request.httprequest.args.get('committee')
        organism = request.httprequest.args.get('organism')
        # Fills the list dynamically by asking for each state defined in the
        # STANDARD_STATE list. In this way, we ensure that if a new state is
        # defined it is considered as a possible filter.
        states = [
            request.httprequest.args.get(
                'state_%s' % (state[0]), False) for state in STANDARD_STATES]
        if sector:
            domain += [('sector_id', '=', int(sector))]
        if committee:
            domain += [('committee_id', '=', int(committee))]
        if organism:
            domain += [('organism_ids', '=', int(organism))]
        selected_states = list(filter(None, states))
        if selected_states:
            domain += [('product_variant_id.state', 'in', selected_states)]
        if not search:
            return domain

        new_domain = []
        for condition in domain:
            if (not isinstance(condition, tuple) or condition[0] not in
                    ['name', 'product_variant_ids.default_code']):
                new_domain += [condition]
            elif condition[0] == 'name':
                new_domain += ['|', '|', '|', '|', '|', condition]
            elif condition[0] == 'product_variant_ids.default_code':
                new_domain += [
                    condition,
                    ('correspondence_ids.name', 'ilike', search),
                    ('product_variant_ids.previous_code', 'ilike', search),
                    ('sector_id.name', 'ilike', search),
                    ('committee_id.name', 'ilike', search),
                    ('application_field', 'ilike', search),
                ]

        return new_domain

    # Se desabilita por que no lo necesita el cliente
    # def _get_mandatory_billing_fields(self):
    #     flds = super(WebsiteSaleInherit, self)._get_mandatory_billing_fields()
    #     flds.extend(('vat',))
    #     return flds
    #
    # def _get_mandatory_shipping_fields(self):
    #     flds = super(WebsiteSaleInherit, self)._get_mandatory_shipping_fields()
    #     flds.extend(('vat',))
    #     return flds

    @http.route()
    def address(self, *args, **kw):
        response = super().address(*args, **kw)
        states = request.env['res.country.state'].sudo().search([])
        response.qcontext.update(states=states)
        return response


class WebsiteContactUs(http.Controller):

    @http.route(['/contactus'], type='http', auth="public", website=True)
    def contact_us(self, **kw):
        team_alias = request.httprequest.args.get('alias', False)
        team = http.request.env['crm.team'].sudo().search([
            ('alias_name', '=', team_alias)], limit=1) if team_alias else False
        values = {'team_id': team.id if team else False,
                  'type_request': team_alias}
        return request.render("inteco.inteco_contactus", values)

    @http.route(['/contactus/subservices'], type='json', auth="public",
                website=True)
    def get_subservices(self, team_id):
        subservices = request.env['crm.subservice'].search([
            ('crm_team_id', '=', team_id), ('website_published', '=', True)
        ])
        return dict(
            subserv=[(s.id, s.name) for s in subservices]
        )


class WebsiteComplaint(http.Controller):

    @http.route(['/helpdesk/complaint-form'], type='json', auth="public",
                website=True)
    def complaint_form_field(self, form_type_id):
        """Allows to show or hide additional fields in the complaint form
        depending on the selected ticket type."""
        # FIXME: this should be configurable in the helpdesk settings section
        complaint_id = request.env.ref('inteco.type_complaint').id
        # Currently, only one additional field is need shown in the form if
        # the ticket type is a complaint.
        return complaint_id == form_type_id


class SaleQuote(CustomerPortal):

    @http.route("/my/quotes/<int:order_id>", type='http',
                auth='user', website=True)
    def view_user(self, *args, **kwargs):
        """ The content added to this method was taken
        from the portal_order_page method ->
        odoo/addons/website_sale_digital/controllers/main.py
        because we need to add the downloads option in the quote
        of customer in its My Account menu in the website.
        Initially the download option is available to Sale Order
        in the portal menu, BUT, when the website_quote module is installed
        the portal menu is replaced. More info in the
        portal_my_quotations_inherit_quote template available in ->
        addons/website_quote/views/website_quote_templates.xml
        """
        response = super(SaleQuote, self).view_user(*args, **kwargs)

        order = response.qcontext['quotation']

        invoiced_lines = request.env['account.move.line'].sudo().search(
            [('invoice_id', 'in', order.invoice_ids.ids),
             ('invoice_id.state', '=', 'paid')])

        products = invoiced_lines.mapped('product_id') | \
            order.order_line.filtered(
                lambda r: not r.price_subtotal).mapped('product_id')

        purchased_products_attachments = {}

        for product in products:
            # Search for product attachments
            attachment = request.env['ir.attachment']
            product_id = product.id
            template = product.product_tmpl_id
            att = attachment.search_read(
                domain=['|', '&', ('res_model', '=', product._name),
                        ('res_id', '=', product_id), '&',
                        ('res_model', '=', template._name),
                        ('res_id', '=', template.id),
                        ('product_downloadable', '=', True)],
                fields=['name', 'write_date'],
                order='write_date desc',
            )

            # Ignore products with no attachments
            if not att:
                continue

            purchased_products_attachments[product_id] = att
        response.qcontext.update({
            'digital_attachments': purchased_products_attachments,
        })

        return response


class WebsiteSaleDigitalWithQuotation(WebsiteSaleDigital):

    @http.route([
        '/my/download',
    ], type='http', auth='public')
    def download_attachment(self, attachment_id, sale_id=None):
        """ This method was taken from website_sale_digital module ->
        odoo/addons/website_sale_digital/controllers/main.py
        The method was overwritten because we need change the coditional
        when the attach is a document. (if attachmente['data'])
        When the attach is a document should be a watermark in all the
        pages of the document.
        """
        # Check if this is a valid attachment id
        attachment = request.env['ir.attachment'].sudo().search_read(
            [('id', '=', int(attachment_id))],
            ["name", "datas", "datas_fname", "mimetype", "res_model", "res_id", "type", "url"]
        )
        if not attachment:
            return redirect(self.orders_page)
        attachment = attachment[0]

        # Check if the user has bought the associated product
        res_model = attachment['res_model']
        res_id = attachment['res_id']
        purchased_products = request.env['account.move.line']\
            .get_digital_purchases()

        orders_page = False
        page = {
            'product.product': lambda res_id, purchased:
                res_id not in purchased,
            # Also check for attachments in the product templates
            'product.template': lambda res_id, purchased:
                not request.env['product.product'].search_count(
                    [('id', 'in', purchased),
                     ('product_tmpl_id', '=', res_id)])
                }
        orders_page = page.get(res_model, lambda *a: False)(
            res_id, purchased_products)

        if res_model not in ['product.product', 'product.template'] or \
                orders_page:
            return redirect(self.orders_page)

        # The client has bought the product,
        # otherwise it would have been blocked by now
        if attachment["type"] == "url":
            if attachment["url"]:
                return redirect(attachment["url"])
            else:
                return request.not_found()
        if attachment["datas"]:
            # base64 to pdf content (bytes object)
            data = base64.standard_b64decode(attachment["datas"])
            # We have a report in Odoo and get the pdf content too, this gets
            # a bytes object
            report_watermark = request.env.ref(
                'inteco.action_report_watermark')
            pdf = report_watermark.sudo().render_qweb_pdf(int(sale_id))[0]

            # BytesIO is a file-like API for reading and writing bytes objects.
            # bytes object is pass to in-memory bytes buffer
            data = io.BytesIO(data)
            data_pdf = io.BytesIO(pdf)

            # file object is transform to PdfFileReader
            pdf = PdfFileReader(data_pdf)
            data = PdfFileReader(data)

            output = PdfFileWriter()
            page = data.getPage(0)
            if page:
                output.addPage(page)

            num = 1
            while num < data.getNumPages():
                # The watermark is overlaped in all pages
                # (except the first page) in the product digital document
                page = data.getPage(num)
                # The page_pdf have overlapped the page before
                # here the watermark page_pdf is created clean again
                pdf = PdfFileReader(data_pdf)
                page_pdf = pdf.getPage(0)
                page_pdf.mergePage(page)
                output.addPage(page_pdf)
                num += 1

            # a bytes buffer is created to write the new product pdf
            # with the watermark
            final_pdf = io.BytesIO()
            # The PdfFileWriter is written in buffer to be export
            # (dowloaded)
            output.write(final_pdf)

            # the file object(final_pdf) will be dowloaded
            return http.send_file(final_pdf,
                                  filename=attachment['name'],
                                  as_attachment=True)
        return request.not_found()
