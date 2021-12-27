# -*- coding: utf-8 -*-

import json
from odoo import _
from odoo.exceptions import AccessError
from odoo.http import route, request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal as CP
from odoo.addons.sale.controllers.portal import CustomerPortal as SCP
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

import werkzeug

from odoo import http
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)

class CustomerPortal(CP):

    def __init__(self, **args):
        """Overwritten in order to include two new fields in the details form
        validation, and also to add an optional one."""
        self.MANDATORY_BILLING_FIELDS.extend(
            ['contact_name', 'contact_last_name'])
        self.OPTIONAL_BILLING_FIELDS.extend(
            ['second_last_name'])
        super(CustomerPortal, self).__init__(**args)

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        """When the user updates any of the following fields: name, first last
        name or second last name in his portal profile, we must ensure that the
        partner name is always a combination of these fields just as it is done
        in the back-end with the partner form view."""
        if post:
            contact_name = ' '.join([n for n in [
                post.get('contact_name'), post.get('contact_last_name'),
                post.get('second_last_name')
            ] if n])
            contact_name = contact_name.title()
            post.update({'name': contact_name})
        return super(CustomerPortal, self).account(redirect=None, **post)


class SaleCustomerPortal(SCP):

    @route()
    def portal_quote_accept(self, res_id, access_token=None, partner_name=None,
                            signature=None):
        """This method was overwritten to ignore the signature images added to
        the chatter once the order has been accepted."""
        if not self._portal_quote_user_can_accept(res_id):
            return {'error': _('Operation not allowed')}

        try:
            order_sudo = self._order_check_access(
                res_id, access_token=access_token)
        except AccessError:
            return {'error': _('Invalid order')}
        if order_sudo.state != 'sent':
            return {'error': _(
                'Order is not in a state requiring customer validation.')}

        order_sudo.action_confirm()

        _message_post_helper(
            res_model='sale.order',
            res_id=order_sudo.id,
            message=_('Order accepted by %s') % (partner_name,),
            **({'token': access_token} if access_token else {}))
        return {
            'success': _('Your Order has been confirmed.'),
            'redirect_url': '/my/orders/%s?%s' % (
                order_sudo.id,
                access_token and
                'access_token=%s' % order_sudo.access_token or ''),
        }


class IntecoController(AuthSignupHome):
    
    
    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()
        if qcontext.get('contact_name', False):
            name = qcontext.get('contact_name', '') \
                   + ' ' + qcontext.get('contact_last_name', '') + ' ' \
                   + qcontext.get('second_last_name', '')
            qcontext['name'] = name

        if qcontext.get('type_is_company', False):
            if qcontext.get('type_is_company', False) == 'on':
                qcontext['company_type'] = 'company'
            else:
                qcontext['company_type'] = 'person'
        
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                if qcontext.get('token'):
                    User = request.env['res.users']
                    user_sudo = User.sudo().search(
                        User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                    )
                    template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
                    if user_sudo and template:
                        template.sudo().send_mail(user_sudo.id, force_send=True)
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")
        
        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password', 'company_type') }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '')
        if lang in supported_lang_codes:
            values['lang'] = lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()

    @route(
        "/inteco/signup", type="http", auth="public",
        website="website", csrf=False)
    def _inteco_singup(self, redirect=None, **kw):
        if not kw.get('name'):
            partner_name = " ".join([
                kw.get('contact_name'),
                kw.get('contact_last_name'),
                kw.get('second_last_name')
            ])
            request.params['name'] = partner_name
            kw['name'] = partner_name
        res = self.web_auth_signup(**kw)
        ctx = res.qcontext
        error_msg = ctx.get('error', False)
        if not error_msg:
            user = request.env['res.users'].sudo().browse(
                request.session.uid)
            user.partner_id.write(kw)
            if user.partner_id.company_name:
                user.partner_id.create_company()
        return json.dumps({
            'error_msg': error_msg,
            'success': not error_msg
        })

    @route(
        '/inteco/render-province', type="http", auth="public")
    def render_province_select(self, **kw):
        country = request.env['res.country'].sudo().browse(
            int(kw.get('country_id')))
        country_states = request.env['res.country.state'].search(
            [('country_id', '=', country.id)])
        values = {'country_states': country_states}
        return request.render('inteco.state_per_country', values)
