# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class BlogPost(models.Model):
    _inherit = "blog.post"

    @api.onchange('post_date')
    def onchange_post_date(self):
        """Prevents the user from setting a post date earlier than today
        """
        res = {}
        if not self.post_date:
            return res
        today = fields.Date.from_string(fields.Date.today())
        post_date = fields.Date.from_string(self.post_date)
        if post_date < today:
            res['warning'] = {
                'title': _('Invalid Post Date'),
                'message': _(
                    "The post date may not be earlier than today.\n"
                    "Today is %s, and you are trying to set the post date "
                    "to %s."
                    ) % (today, post_date)
            }
            res['value'] = {
                'post_date': False,
            }
        return res
