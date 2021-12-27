Website Language Selector in Header
===================================

.. |badge2| image:: https://img.shields.io/badge/license-OPL--1-blue.png
    :target: https://www.odoo.com/documentation/user/12.0/legal/licenses/licenses.html#odoo-apps
    :alt: License: OPL-1

.. |badge3| image:: https://img.shields.io/badge/powered%20by-yodoo.systems-00a09d.png
    :target: https://yodoo.systems
    
.. |badge5| image:: https://img.shields.io/badge/maintainer-CR&D-purple.png
    :target: https://crnd.pro/
    


|badge2| |badge5|

Website Language Selector in Header is a module developed by the Center of Research & Development company. It moves website's language selector to the top panel. You can see the language selector if two or more languages are loaded on the website.

Launch your own ITSM system in 60 seconds:
''''''''''''''''''''''''''''''''''''''''''

Create your own `Bureaucrat ITSM <https://yodoo.systems/saas/template/bureaucrat-itsm-demo-data-95>`__ database

|badge3| 

Bug Tracker
===========

Bugs are tracked on `https://crnd.pro/requests <https://crnd.pro/requests>`_.
In case of trouble, please report there.


Maintainer
''''''''''
.. image:: https://crnd.pro/web/image/3699/300x140/crnd.png

Our web site: https://crnd.pro/

This module is maintained by the Center of Research & Development company.

We can provide you further Odoo Support, Odoo implementation, Odoo customization, Odoo 3rd Party development and integration software, consulting services. Our main goal is to provide the best quality product for you. 

For any questions `contact us <mailto:info@crnd.pro>`__.

inherit_id="website.template_header_default"


  <xpath expr="//div[@id='top_menu_collapse']/t[1]" position="inside">
        <t t-if="(request and request.is_frontend_multilang and len(languages) &gt; 1)">

            <t t-set="languages_dict" t-value="{'llave1':1,'llave2':2,}"/>
            <li class="nav-item divider"/>
            <li class="nav-item dropdown" t-ignore="true">
                <a href="#" class="nav-link dropdown-toggle" data-toggle="dropdown">
                    <b>
                        <span t-esc="languages_dict.get('llave1')"/>
                        <span class="caret"></span>
                    </b>
                </a>
                <ul class="js_language_selector dropdown-menu" role="menu">
                    <li t-foreach="languages_dict.items()" t-as="lg">
                        <a class="js_change_lang dropdown-item"
                           role="menuitem"


                           t-att-data-lang="lg[0]"
                           t-esc="lg[1]"/>
                    </li>
                </ul>
            </li>
        </t>
    </xpath>


<xpath expr="//ul[@id='top_menu']/li[last()]" position="after">
        <t t-if="(request and request.is_frontend_multilang and len(languages) &gt; 1)">
            <t t-set="languages_dict" t-value="dict((l_code, l_name.split('/').pop().strip().capitalize()) for l_code, l_name in languages)"/>
            <li class="nav-item divider"/>
            <li class="nav-item dropdown" t-ignore="true">
                <a href="#" class="nav-link dropdown-toggle" data-toggle="dropdown">
                    <b>
                        <span t-esc="languages_dict.get(request.env.lang, request.lang.split('_')[0].split('-')[0])"/>
                        <span class="caret"></span>
                    </b>
                </a>
                <ul class="js_language_selector dropdown-menu" role="menu">
                    <li t-foreach="languages_dict.items()" t-as="lg">
                        <a class="js_change_lang dropdown-item"
                           role="menuitem"
                           t-att-href="url_for(request.httprequest.path + '?' + keep_query(), lang=lg[0])"
                           t-att-data-default-lang="(editable or translatable) and 'true' if website and lg[0] == website.default_lang_code else None"
                           t-att-data-lang="lg[0]"
                           t-esc="lg[1]"/>
                    </li>
                </ul>
            </li>
        </t>
    </xpath>