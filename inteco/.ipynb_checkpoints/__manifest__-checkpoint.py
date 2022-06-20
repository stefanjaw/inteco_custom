# -*- coding: utf-8 -*-
# Copyright 2017 Vauxoo
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Inteco",
    'summary': '''Instance creator''',
    "version": "06.07.21.2",
    "author": "Vauxoo",
    "application": True,
    "category": "Inteco",
    "website": "http://vauxoo.com",
    "license": "LGPL-3",
    "depends": [
        # Sales
        'sale_crm',
        'phone_validation', #'crm_phone_validation',
        'sale',
        'sale_management',
        'utm',
        
        # Localizations
        'l10n_cr',
        
        # Project
        'project',
        'project_forecast',
        'hr_timesheet',
        
        # Support
        'helpdesk',
        
        # Website
        'website_sale',
        'web_widget_datepicker_options',
        'website_crm',
        'web_editor',
        'website_blog',
        'website_event_questions',
        'website_twitter',
        'website_sale_digital',
        'website_livechat',
        'website_form',
        'website_helpdesk_form',
        'website_helpdesk_livechat',
        
        # Tools
        'company_country',
        'base_automation',
        'auth_oauth',
        'marketing_automation',
        'mass_mailing',
        'survey',
        'hr_expense',
        
        'web_widget_email_validator',
    ],
    'qweb': [
        'static/src/xml/help.xml',
        'static/src/xml/base.xml',
    ],

    "data": [
        #     # Security
        "security/res_groups.xml",
        "security/ir.model.access.csv",

        #     # Data
        #"data/res_company_data.xml",
        "data/sector.xml",
        #"data/res_partner_data.xml", #Dupplicated Line
        "data/event_data.xml",
        "data/product_category_data.xml",
        "data/prefix.xml",
        "data/organism.xml",
        "data/files.xml",
        "data/certificates.xml",
        "data/product_attribute_data.xml",
        "data/base_automation.xml",
        # "data/organism.xml",
        # "data/sales_team.xml",
        "data/res_partner_data.xml",
        "data/product_data.xml",
        "data/mail_activity.xml",
        "data/mail_template.xml",
        "data/crm_stage.xml",
        "views/crm_subservice.xml",



        "report/sale_order_templates.xml",

        
        #
        #     # Website Pages
        "views/assets.xml",
        "views/pages/menu.xml",
        "views/pages/homepage.xml",
        "views/pages/header.xml",
        "views/pages/footer.xml",
        "views/pages/cart.xml",
        "views/pages/certifications.xml",
        "views/pages/standards_development.xml",
        "views/pages/standards_process.xml",
        # "views/pages/standards_public.xml",
        "views/pages/tech_committees.xml",
        "views/pages/certifications_system.xml",
        "views/pages/certifications_greenhouse.xml",
        "views/pages/certifications_process.xml",
        "views/pages/certifications_products.xml",
        "views/pages/certifications_people.xml",
        # "views/pages/certifications_list.xml",
        "views/pages/about.xml",
        "views/pages/trainings.xml",
        "views/pages/food_sector.xml",
        "views/pages/faq.xml",
        "views/pages/contactus.xml",
        "views/pages/complaints.xml",
        "views/pages/membership.xml",
        "views/pages/payment_suppliers.xml",
        "views/pages/signup.xml",
        "views/pages/products_list_view.xml",
        "views/pages/address.xml",
        "views/event_views.xml",
        "views/pages/terms_conditions.xml",
        #
        #     # Views
        "views/ir_attachment_view.xml",
        "views/sale_views.xml",
        "views/sector_view.xml",
        "views/organism_view.xml",
        "views/committee_view.xml",
        "views/ics_view.xml",
        "views/prefix_view.xml",
        "views/menus.xml",
        "wizard/product_confirm_view.xml",
        "wizard/product_use_variant_view.xml",
        "wizard/product_new_edition_view.xml",
        "wizard/crm_lead_lost_views.xml",
        "views/product_view.xml",
        "views/res_partner_view.xml",
        "views/helpdesk_ticket_type_views.xml",
        "views/res_config_settings.xml",
        "views/portal_templates.xml",
        "views/sale_quote_views.xml",
        "views/auth_signup.xml",
        "views/on_page_auth.xml",
        # "views/payment_link_terms.xml",
        'views/templates.xml',
        'views/webclient_templates.xml',
        #'views/website_helpdesk_form_views.xml', #NO SE ENCUENTRA LA VISTA inherit_id="website_helpdesk_form.team_form_2"
        'views/website_quote_templates.xml',
        'views/website_sale.xml',
        'data/website_menu_data.xml',
        'data/website_blog_data.xml',
        'data/website_crm_data.xml',
        'data/website_helpdesk.xml',
        'views/account_move.xml',
    ]
}
