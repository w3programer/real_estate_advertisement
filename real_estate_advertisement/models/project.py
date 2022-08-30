from odoo import fields, models, api


class Project(models.Model):
    _name = 'real.project'
    _inherit = ['mail.thread']
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    country_id = fields.Many2one("res.country", "Country")
    state_id = fields.Many2one("res.country.state","State",domain="[('country_id', '=?', country_id)]")
    name = fields.Char()
    cost = fields.Float("Average cost")
    area = fields.Float("Area")
    analytic_acounting_id = fields.Many2one("account.analytic.account",string="Cost center")
    partner_id = fields.Many2one("res.partner","Owner")
    main_property_ids  = fields.One2many("main.property.property","project_id")


