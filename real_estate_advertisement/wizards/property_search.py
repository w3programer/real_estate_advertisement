from odoo import models, fields


class PropertySearch(models.TransientModel):
    _name = 'property.search'
    _description = 'Property search'

    def get_default_uom_categ(self):
        uom_categ_id = self.env["uom.category"].search([("for_property_area", "=", True)], limit=1)
        if uom_categ_id:
            return uom_categ_id.id
        else:
            return False

    def get_default_uom(self):
        uom_categ_id = self.env["uom.category"].search([("for_property_area", "=", True)], limit=1)
        if uom_categ_id:
            uom_ids = self.env["uom.uom"].search([("category_id", "=", uom_categ_id.id)])
            uom_id = uom_ids.filtered(lambda uom: uom.ratio == 1)
            if uom_id:
                return uom_id.id
            else:
                return False
        else:
            return False

    name = fields.Char(default="Property Quick Search")
    property_name = fields.Char(string='Property Name')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state')
    country_id = fields.Many2one('res.country')
    property_for = fields.Selection([('rent', 'Rent'), ('sale', 'Sale')], required=True)
    minimum_price = fields.Monetary()
    maximum_price = fields.Monetary()
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientation = fields.Char()
    living_area_min = fields.Integer(string='Living Area')
    living_area_max = fields.Integer()
    area_uom_category = fields.Many2one("uom.category", domain=[("for_property_area", "=", True)],
                                        default=lambda self: self.get_default_uom_categ())
    area_uom = fields.Many2one("uom.uom", domain='[("category_id", "=", area_uom_category)]',
                               default=lambda self: self.get_default_uom())
    offer = fields.Boolean(string='Offers')
    furnishing = fields.Selection(
        [("unfurnished", "Unfurnished"), ("semi_furnished", "Semi-Furnished"), ("fully_furnished", "Fully-Furnished")])
    property_type_id = fields.Many2one('property.type')
    availability = fields.Selection([("immediately", "Immediately"), ("from_date", "From Date")], string='Availability')
    date_availability = fields.Date(string='Date Availability')
    property_ids = fields.Many2many('property.property')

    def wizard_search_method(self):
        domain = [("state", "=", "available")]

        if self.country_id:
            domain.append(('main_property_id.country_id', 'like', self.country_id.id))

        if self.city:
            domain.append(('main_property_id.city', 'like', self.city))

        if self.state_id:
            domain.append(('main_property_id.state_id', 'like', self.state_id.id))

        if self.property_name:
            domain.append(('name', 'like', self.property_name))

        domain.append(('property_for', '=', self.property_for))
        if self.property_for == 'rent':
            if self.maximum_price:
                domain.append(('rent_price', '<=', self.maximum_price))

            if self.minimum_price:
                domain.append(('rent_price', '>=', self.minimum_price))
        else:
            if self.maximum_price:
                domain.append(('selling_price', '<=', self.maximum_price))

            if self.minimum_price:
                domain.append(('selling_price', '>=', self.minimum_price))

        if self.living_area_min and self.area_uom:
            uom_ids = self.env["uom.uom"].search([("category_id", "=", self.area_uom.category_id.id)])
            uom_id = uom_ids.filtered(lambda uom: uom.ratio == 1)
            converted_area = uom_id._compute_price(self.living_area_min, self.area_uom)
            domain.append(('living_area', '>=', converted_area))

        if self.living_area_max and self.area_uom:
            uom_ids = self.env["uom.uom"].search([("category_id", "=", self.area_uom.category_id.id)])
            uom_id = uom_ids.filtered(lambda uom: uom.ratio == 1)
            converted_area = uom_id._compute_price(self.living_area_max, self.area_uom)
            domain.append(('living_area', '<=', converted_area))

        # if self.garden_area:
        #     domain.append(('garden_area','=',self.garden_area))
        if self.garage:
            domain.append(('garage', '=', self.garage))

        if self.garden:
            domain.append(('garden', '=', self.garden))

        if self.offer:
            if self.property_for == 'sale':
                domain.append(('sale_offer_ids', '!=', False))
            else:
                domain.append(('rent_offer_ids', '!=', False))

        if self.property_type_id:
            domain.append(('property_type_id', '=', self.property_type_id.id))

        if self.furnishing:
            domain.append(('furnishing', '=', self.furnishing))

        if self.availability == "immediately":
            domain.append(('availability', '=', self.availability))
        elif self.availability == "from_date" and self.date_availability:
            domain.append(('date_availability', '>=', self.date_availability))

        search_record = self.env['property.property'].search(domain)

        self.property_ids = [(6, 0, search_record.ids)]

    def reset_search(self):
        return {
            'name': "Property Quick Search",
            'context': self.env.context,
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            # 'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'inline',
        }
