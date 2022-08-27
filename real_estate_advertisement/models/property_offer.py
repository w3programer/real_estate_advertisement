from odoo import fields, models, api


class PropertySaleOffer(models.Model):
    _name = 'property.sale.offer'
    _order = "id desc"

    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    property_id = fields.Many2one('property.property', ondelete='cascade')
    main_property_id = fields.Many2one("main.property.property", related="property_id.main_property_id", store=True,
                                       readonly=False)
    start_date = fields.Date()
    end_date = fields.Date()
    offer_price = fields.Monetary()
    description = fields.Text()
    state = fields.Selection([('inactive', 'Inactive'), ('active', 'Active'), ('expired', 'Expired')],
                             compute="_compute_offer_status")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    def _compute_offer_status(self):
        for offer in self:
            if offer.start_date and offer.end_date:
                today = fields.Date.today()
                if offer.start_date <= today <= offer.end_date:
                    offer.state = "active"
                elif offer.start_date > today:
                    offer.state = "inactive"
                elif today > offer.end_date:
                    offer.state = "expired"
            else:
                offer.state = "inactive"


class PropertyRentOffer(models.Model):
    _name = 'property.rent.offer'
    _order = "id desc"

    name = fields.Char()
    partner_id = fields.Many2one('res.partner')
    main_property_id = fields.Many2one("main.property.property", related="property_id.main_property_id", store=True,
                                       readonly=False)
    property_id = fields.Many2one('property.property', ondelete='cascade')
    duration = fields.Integer()
    duration_unit = fields.Selection([('month', 'Month'), ('year', 'Year')])
    start_date = fields.Date()
    end_date = fields.Date()
    offer_price = fields.Monetary()
    description = fields.Text()
    state = fields.Selection([('inactive', 'Inactive'), ('active', 'Active'), ('expired', 'Expired')],
                             compute="_compute_offer_status")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    def _compute_offer_status(self):
        for offer in self:
            if offer.start_date and offer.end_date:
                today = fields.Date.today()
                if offer.start_date <= today <= offer.end_date:
                    offer.state = "active"
                elif offer.start_date > today:
                    offer.state = "inactive"
                elif today > offer.end_date:
                    offer.state = "expired"
            else:
                offer.state = "inactive"
