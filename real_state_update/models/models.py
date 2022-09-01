from odoo import models, fields, api, tools, exceptions, _
from odoo.exceptions import ValidationError, UserError
import datetime


class PropertyPropertyContractInherit(models.Model):
    _inherit = 'property.property.contract'

    state = fields.Selection(selection_add=[("revise", "تدقيق")])
    dyas_notif = fields.Integer('Days Before Notification')
    tonow_date = fields.Date(track_visibility='onchange', default=fields.Date.today())
    end_date = fields.Date(track_visibility='onchange')
    user_not = fields.Many2one('res.users', string='User to notify')

    def action_revise(self):
        self.state = 'revise'

    def action_not(self):
        if not self.user_not:
            raise ValidationError('Please Select User to notify first')
        self.tonow_date = fields.Date.today()
        if self.tonow_date:
            print(self.tonow_date,'hdocjods')
            planned = (datetime.datetime.strptime(str(self.tonow_date), '%Y-%m-%d') + datetime.timedelta(
                days=self.dyas_notif)).strftime('%Y-%m-%d')
            self.end_date = planned
            for rec in self.amount_installment_ids:
                if rec.due_date == self.end_date:
                    notification_ids = []
                    notification_ids.append((0, 0, {
                        'res_partner_id': self.user_not.partner_id.id,
                        'notification_type': 'inbox',
                        # 'href': ' %i' % self.env.ref('rabat_hr_custody.view_hr_custody_form').id,
                    }))
                    self.env['mail.message'].create({
                        'message_type': 'notification',
                        'subject': ('انتبه لقد تم اشعارك بمعاد سداد قسط قادم يوم: %s') % (rec.due_date),
                        'body': ('للعميل: %s') % (str(self.partner_id.name)),
                        'model': self._name,
                        'author_id': self.env.user.partner_id.id,
                        'partner_ids': [self.user_not.partner_id.id],
                        'notification_ids': notification_ids,
                        'subtype_id': self.env.ref('mail.mt_comment').id,
                        'res_id': self.id,
                        # 'subtype_id': self.env.ref('rabat_hr_custody.view_hr_custody_form').id,

                    })
                    print('hallla done')
