# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions, _


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    #@api.multi
    def action_notify(self):
        for rec in self:
            original_context = rec.env.context
            body_template = rec.env.ref('mail.message_activity_assigned')
            if rec.res_model == 'crm.lead':
                pass
            else:
                for activity in rec:
                    if activity.user_id.lang:
                        # Send the notification in the assigned user's language
                        self = rec.with_context(lang=activity.user_id.lang)
                        body_template = body_template.with_context(lang=activity.user_id.lang)
                        activity = activity.with_context(lang=activity.user_id.lang)
                    model_description = self.env['ir.model']._get(activity.res_model).display_name
                    body = body_template._render(
                        dict(
                            activity=activity,
                            model_description=model_description,
                            access_link=self.env['mail.thread']._notify_get_action_link('view', model=activity.res_model, res_id=activity.res_id),
                        ),
                        engine='ir.qweb',
                        minimal_qcontext=True
                    )
                    record = self.env[activity.res_model].browse(activity.res_id)
                    if activity.user_id:
                        record.message_notify(
                            partner_ids=activity.user_id.partner_id.ids,
                            body=body,
                            subject=_('%(activity_name)s: %(summary)s assigned to you',
                                      activity_name=activity.res_name,
                                      summary=activity.summary or activity.activity_type_id.name),
                            record_name=activity.res_name,
                            model_description=model_description,
                            email_layout_xmlid='mail.mail_notification_light',
                        )
                    body_template = body_template.with_context(original_context)
                    self = rec.with_context(original_context)
