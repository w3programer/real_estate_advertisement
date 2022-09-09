# -*- coding: utf-8 -*-

from odoo import models, fields, api


class partner_custom(models.Model):
    _inherit = 'res.partner'
    land_1 = fields.Char("الزقاق")
    land_2 = fields.Char("الدار")
    land_3 = fields.Char("المحلة")