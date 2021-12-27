
from ast import literal_eval

from odoo import api, fields, models, _
from odoo.tools.misc import ustr

from odoo.addons.auth_signup.models.res_partner import SignupError, now


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        """ When an user is created without partner, and a partner with the
            same email already exists, assigns the partner automatically. This
            Allows to avoid errors when creating a new user from the website
            which already has a registered partner, and the system tries to
            create a new partner with the same email.

            This is not done by Odoo because, by default, there could be more
            than one partner with the same email, so such a case would not
            happen.
        """
        if 'partner_id' not in vals and vals.get('email'):
            partner = self.env['res.partner'].search([
                ('is_company', '=', False),
                ('email', '=ilike', vals.get('email')),
                ], limit=1)
            if partner:
                vals['partner_id'] = partner.id
        return super(ResUsers, self).create(vals)


    def _create_user_from_template(self, values):
        template_user_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('base.template_portal_user_id', 'False'))
        template_user = self.browse(template_user_id)
        if not template_user.exists():
            raise ValueError(_('Signup: invalid template user'))
    
        if not values.get('login'):
            raise ValueError(_('Signup: no login given for new user'))
        if not values.get('partner_id') and not values.get('name'):
            raise ValueError(_('Signup: no name or partner given for new user'))
    
        # create a copy of the template user (attached to a specific partner_id if given)
        values['active'] = True
        try:
            with self.env.cr.savepoint():
                user = template_user.with_context(no_reset_password=True).copy(values)
                user.partner_id.company_type = values.get('company_type', 'person')
                return user
        except Exception as e:
            # copy may failed if asked login is not available.
            raise SignupError(ustr(e))