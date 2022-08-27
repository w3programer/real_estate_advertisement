# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    send_contract_payment_reminder = fields.Boolean()
    remind_before = fields.Integer()
    remind_on_due_date = fields.Boolean()
    remind_every_day_after_due_date = fields.Boolean()

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('real_estate_advertisement.send_contract_payment_reminder',
                                                  self.send_contract_payment_reminder)
        self.env['ir.config_parameter'].set_param('real_estate_advertisement.remind_before', self.remind_before)
        self.env['ir.config_parameter'].set_param('real_estate_advertisement.remind_on_due_date',
                                                  self.remind_on_due_date)
        self.env['ir.config_parameter'].set_param('real_estate_advertisement.remind_every_day_after_due_date',
                                                  self.remind_every_day_after_due_date)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        send_contract_payment_reminder = ICPSudo.get_param('real_estate_advertisement.send_contract_payment_reminder')
        remind_before = ICPSudo.get_param('real_estate_advertisement.remind_before') or 5
        remind_on_due_date = ICPSudo.get_param('real_estate_advertisement.remind_on_due_date')
        remind_every_day_after_due_date = ICPSudo.get_param('real_estate_advertisement.remind_every_day_after_due_date')

        res.update(
            send_contract_payment_reminder=bool(send_contract_payment_reminder),
            remind_before=int(remind_before),
            remind_on_due_date=bool(remind_on_due_date),
            remind_every_day_after_due_date=bool(remind_every_day_after_due_date),
        )
        return res
