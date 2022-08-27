import base64
import io
from random import randint

from odoo import fields, models, api
from odoo.exceptions import ValidationError

ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id')


class MainProperty(models.Model):
    _name = 'main.property.property'
    _inherit = ['mail.thread']
    _description = "Main Real Estate Property"

    name = fields.Char(string='Property Name', required=True)
    image = fields.Binary()
    property_type_ids = fields.Many2many('property.type')
    description = fields.Text(string='Property Description')
    street = fields.Char(string='Street1')
    street2 = fields.Char(string='Street1')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', domain="[('country_id', '=?', country_id)]")
    zip = fields.Char(string='Zip')
    country_id = fields.Many2one('res.country')
    property_ids = fields.One2many('property.property', 'main_property_id', string='property Details')
    contact_address = fields.Text(compute="_compute_contact_address", store=True)
    state = fields.Selection([("available", "Available"), ("not_available", "Not Available")],
                             compute="_compute_property_state", store=True)
    property_usp_ids = fields.One2many("property.usp", "main_property_id")
    document_ids = fields.One2many("property.document", "main_property_id")
    image_gallery_doc_ids = fields.One2many("property.document", "main_property_image_id")

    @api.depends("property_ids.state")
    def _compute_property_state(self):
        for rec in self:
            if rec.property_ids.filtered(lambda property_id: property_id.state == "available").ids:
                rec.state = "available"
            else:
                rec.state = "not_available"

    @api.depends("street", "street2", "city", "state_id", "zip", "country_id")
    def _compute_contact_address(self):
        for rec in self:
            rec.contact_address = rec.display_address()

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.model
    def _get_default_address_format(self):
        return "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"

    @api.model
    def _get_address_format(self):
        return self.country_id.address_format or self._get_default_address_format()

    def display_address(self):

        address_format = self._get_address_format()

        args = {
            'state_code': self.state_id.code or '',
            'state_name': self.state_id.name or '',
            'country_code': self.country_id.code or '',
            'country_name': self.country_id.name or '',

        }

        for field in ADDRESS_FIELDS:
            args[field] = getattr(self, field) or ''
        return address_format % args

    def name_get(self):
        res = []
        for rec in self:
            name = rec.name or ''
            if self._context.get('show_address'):
                if rec.display_address():
                    address = rec.display_address()
                    address = address.replace("\n\n", "\n")
                    name = name + "\n" + address
            res.append((rec.id, name))
        return res


class Property(models.Model):
    _name = 'property.property'
    _inherit = ['mail.thread']
    _description = "Property"

    def split_list(self, a_list, which_half):
        if len(a_list) % 2 == 0:
            half = len(a_list) // 2
            if which_half == "first":
                return a_list[:half]
            else:
                return a_list[half:]
        else:
            half = len(a_list) // 2
            if which_half == "first":
                return a_list[:half + 1]
            else:
                return a_list[half + 1:]

    def get_default_uom_categ(self):
        uom_categ_id = self.env["uom.category"].search([("for_property_area", "=", True)], limit=1)
        if uom_categ_id:
            return uom_categ_id.id
        else:
            raise ValidationError("UOM category not set for property area!")

    def get_default_uom(self):
        uom_categ_id = self.env["uom.category"].search([("for_property_area", "=", True)], limit=1)
        if uom_categ_id:
            uom_ids = self.env["uom.uom"].search([("category_id", "=", uom_categ_id.id)])
            uom_id = uom_ids.filtered(lambda uom: uom.ratio == 1)
            if uom_id:
                print("UOM", uom_id, uom_id.ratio)
                return uom_id.id
            else:
                raise ValidationError("Set a default area UOM with ratio 1!")
        else:
            raise ValidationError("UOM category not set for property area!")

    # def load_default_partner(self):
    #     user_ids = self.env["res.users"].search([])
    #     real_estate_user_partner = self.env["res.partner"]
    #     for user in user_ids:
    #         if user.has_group("real_estate_advertisement.group_real_estate_user"):
    #             real_estate_user_partner += user.partner_id
    #     return [(6, 0, real_estate_user_partner.ids)]

    name = fields.Char(string='Property Name', required=True)
    main_property_id = fields.Many2one('main.property.property')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    expected_price = fields.Monetary()
    selling_price = fields.Monetary()

    # Property description fields

    bedrooms = fields.Integer()
    facing_direction = fields.Char()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_type = fields.Selection([("personal", "Personal"), ("common", "Common")], required=True)
    garden_area = fields.Integer()
    garden_orientation = fields.Char()
    bathroom = fields.Integer()
    reception = fields.Integer()
    pet_allowed = fields.Boolean()
    furnishing = fields.Selection(
        [("unfurnished", "Unfurnished"), ("semi_furnished", "Semi-Furnished"), ("fully_furnished", "Fully-Furnished")],
        default="unfurnished")
    floor = fields.Char()
    transaction = fields.Selection([("new", "New Property"), ("resale", "Resale")], default="new", required=True)
    preferred_tenant = fields.Char("Tenants Preferred")
    availability = fields.Selection([("immediately", "Immediately"), ("from_date", "From Date")], string='Availability',
                                    default="immediately", required=True)
    date_availability = fields.Date(string='Date Availability')
    balconies = fields.Integer()
    living_area = fields.Float(string='Living Area')
    super_area = fields.Float("Super Area")
    area_uom_category_id = fields.Many2one("uom.category", domain=[("for_property_area", "=", True)],
                                           default=lambda self: self.get_default_uom_categ())
    area_uom_id = fields.Many2one("uom.uom", domain='[("category_id", "=", area_uom_category_id)]',
                                  default=lambda self: self.get_default_uom())

    image = fields.Binary()
    property_type_id = fields.Many2one('property.type')
    property_for = fields.Selection([('rent', 'Rent'), ('sale', 'Sale')], required=True)
    state = fields.Selection(
        [('new', 'New'), ('maintenance', 'Maintenance'), ('available', 'Available'), ('in_contract', 'In Contract'),
         ('sold', 'Sold'), ('on_rent', 'On Rent')], string='State', default="new")

    # Property Rent Fields
    rent_price = fields.Monetary(required=True)
    rent_uom = fields.Selection([("month", "Month")], default="month", required=True)
    minimum_rent_duration = fields.Integer(required=True)
    minimum_rent_duration_uom = fields.Selection([("month", "Month")], default="month", required=True)
    security_deposit_amount = fields.Monetary()
    rent_offer_ids = fields.One2many('property.rent.offer', 'property_id', string='property Details')

    sale_offer_ids = fields.One2many('property.sale.offer', 'property_id', string='property Details')
    contract_property_ids = fields.One2many('property.property.contract', 'property_id', string='property Details')
    property_contract_id = fields.Many2one('property.property.contract', string='Property Contract')
    installment_option = fields.Boolean()
    installment_scheme_ids = fields.Many2many("config.installment")
    config_installment_id = fields.Many2one('config.installment')
    user_id = fields.Many2one("res.users")
    responsible_person_id = fields.Many2one("res.partner")

    responsible_person_is = fields.Selection([("dealer", "Dealer"), ("owner", "Owner")])
    property_owner_id = fields.Many2one("res.partner")
    document_ids = fields.One2many("property.document", "property_id")
    image_gallery_doc_ids = fields.One2many("property.document", "property_image_id")

    @api.onchange('responsible_person_id')
    def _onchange_responsible_person_id(self):
        if self.responsible_person_id:
            user_id = self.env["res.users"].sudo().search([("partner_id", "=", self.responsible_person_id.id)], limit=1)
            if user_id and user_id.has_group("real_estate_advertisement.group_real_estate_user"):
                self.user_id = user_id.id
            else:
                raise ValidationError("Only Property Users are allowed!")

    @api.onchange("availability")
    def onchange_property_availability(self):
        if self.availability == "immediately":
            self.date_availability = False

    @api.onchange('main_property_id')
    def _onchange_main_property_id(self):
        if self.main_property_id:
            res = {
                "domain": {
                    "property_type_id": [("id", "child_of", self.main_property_id.property_type_ids.ids)]
                }
            }
            return res

    def show_form_view(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "property.property",
            "view_mode": "form",
            "res_id": self.id,
            "domain": [],
            "name": "property",
            "target": "current",
        }

    def create_contract(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "property.property.contract",
            "view_mode": "form",
            "name": "Contract ",
            "target": "current",
            "context": {"default_country_id": self.main_property_id.country_id.id, "default_property_id": self.id}
        }

    def action_new(self):
        self.state = 'new'

    def action_available(self):
        if self.contract_property_ids:
            active_contract_ids = self.contract_property_ids.filtered(
                lambda contract: contract.state in ["draft", "confirmed"])
            if active_contract_ids:
                raise ValidationError(
                    "There maybe some active contract for this property, Cancel that contract to make the property available!")
        self.state = 'available'

    def action_make_available(self):
        self.state = 'available'

    def action_maintenance(self):
        self.state = 'maintenance'

    def action_sold(self):
        self.state = 'sold'

    def action_on_rent(self):
        self.state = 'on_rent'

    def get_contract_property_value(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "property.property.contract",
            "view_mode": "tree,form",
            "domain": [('id', 'in', self.contract_property_ids.ids)],
            "name": "Property Contracts",
        }


class PropertyType(models.Model):
    _name = 'property.type'
    _parent_store = True

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(required=True, translate=True)
    parent_id = fields.Many2one('property.type', string='Parent Category', index=True, ondelete="cascade")
    parent_path = fields.Char(index=True)
    parents_and_self = fields.Many2many('property.type', compute='_compute_parents_and_self')
    child_id = fields.One2many('property.type', 'parent_id', string='Children Categories')
    color = fields.Integer(string='Color', default=_get_default_color)

    def name_get(self):
        res = []
        for category in self:
            res.append((category.id, " / ".join(category.parents_and_self.mapped('name'))))
        return res

    def _compute_parents_and_self(self):
        for category in self:
            if category.parent_path:
                category.parents_and_self = self.env['property.type'].browse(
                    [int(p) for p in category.parent_path.split('/')[:-1]])
            else:
                category.parents_and_self = category


class PropertyUSP(models.Model):
    _name = "property.usp"

    name = fields.Char()
    description = fields.Text()
    main_property_id = fields.Many2one("main.property.property")


class UomUom(models.Model):
    _inherit = "uom.category"

    for_property_area = fields.Boolean()


class PropertyDocument(models.Model):
    _name = "property.document"

    name = fields.Char()
    doc_type = fields.Selection([("image", "Image"), ("pdf", "PDF")], default="image")
    image_file_data = fields.Image()
    pdf_file_data = fields.Binary()
    doc_description = fields.Text("Description")
    main_property_id = fields.Many2one("main.property.property")
    main_property_image_id = fields.Many2one("main.property.property")
    property_id = fields.Many2one("property.property")
    property_image_id = fields.Many2one("property.property")


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, res_ids=None, data=None):
        Model = self.env[self.sudo().model]

        result = super(IrActionsReport, self)._render_qweb_pdf(res_ids, data)
        if res_ids and Model._name == "property.property":
            record_ids = Model.browse(res_ids)
            if len(record_ids) == 1:
                pdf_doc_ids_1 = record_ids.main_property_id.document_ids.filtered(lambda doc: doc.doc_type == 'pdf')
                pdf_doc_ids_2 = record_ids.document_ids.filtered(lambda doc: doc.doc_type == 'pdf')
                all_docs_ids = pdf_doc_ids_1 | pdf_doc_ids_2
                if all_docs_ids:
                    streams = [io.BytesIO(result[0])]
                    for pdf_doc in all_docs_ids:
                        streams.append(io.BytesIO(base64.decodebytes(pdf_doc.pdf_file_data)))
                    return self._merge_pdfs(streams), 'pdf'

        return result
