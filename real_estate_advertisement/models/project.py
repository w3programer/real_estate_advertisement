from odoo import fields, models, api


class Project(models.Model):
    _name = 'real.project'
    _inherit = ['mail.thread']
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    country_id = fields.Many2one("res.country", "Country", track_visibility='onchange')
    state_id = fields.Many2one("res.country.state","State",domain="[('country_id', '=?', country_id)]", track_visibility='onchange')
    name = fields.Char(track_visibility='onchange')
    cost = fields.Float("Average cost", track_visibility='onchange')
    area = fields.Float("Area", track_visibility='onchange')
    analytic_acounting_id = fields.Many2one("account.analytic.account",string="Cost center", track_visibility='onchange')
    partner_id = fields.Many2one("res.partner","Owner", track_visibility='onchange')
    main_property_ids  = fields.One2many("main.property.property","project_id")


