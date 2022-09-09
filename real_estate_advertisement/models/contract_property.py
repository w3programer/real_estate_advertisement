from odoo import fields, models, api, _, SUPERUSER_ID
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from datetime import date

from odoo.exceptions import ValidationError, UserError

from io import BytesIO
import qrcode
import base64

class PropertyContract(models.Model):
    _name = 'property.property.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Property Contract"
    _order = "id desc"

    name = fields.Char(string="Ref#.", default="New")
    # Buyer Fields
    partner_id = fields.Many2one('res.partner', required=True, string="Client", readonly=True,
                                 states={'draft': [('readonly', False)], 'cancelled': [('readonly', False)]}, track_visibility='onchange')
    phone = fields.Char(related='partner_id.phone', track_visibility='onchange')
    email = fields.Char(related='partner_id.email', track_visibility='onchange')

    # Seller Fields
    responsible_person_id = fields.Many2one("res.partner", track_visibility='onchange')
    user_id = fields.Many2one("res.users", track_visibility='onchange')
    responsible_person_is = fields.Selection([("dealer", "Dealer"), ("owner", "Owner")],
                                             related="property_id.responsible_person_is", track_visibility='onchange')
    property_owner_id = fields.Many2one("res.partner", related="property_id.property_owner_id", track_visibility='onchange')

    # Property Details
    property_id = fields.Many2one("property.property", string="Property", domain=[('state', '=', 'available')], track_visibility='onchange')
    main_property_id = fields.Many2one('main.property.property', related="property_id.main_property_id",
                                       string="Address", store=True)
    property_for = fields.Selection([('rent', 'Rent'), ('sale', 'Sale')], related='property_id.property_for')
    sale_offer_id = fields.Many2one("property.sale.offer", string="Sale offer", readonly=True,
                                    states={'draft': [('readonly', False)], 'cancelled': [('readonly', False)]},
                                    tracking=True)
    all_valid_sale_offer_ids = fields.Many2many("property.sale.offer", track_visibility='onchange')
    offer_info_message = fields.Text()
    availability = fields.Selection([("immediately", "Immediately"), ("from_date", "From Date")], string='Availability',
                                    readonly=False, required=True,
                                    states={'draft': [('readonly', False)], 'cancelled': [('readonly', False)]})
    date_availability = fields.Date(string='Property Availability Date')
    contract_start_date = fields.Datetime(default=fields.Datetime.now())
    contract_complete_date = fields.Datetime(readonly=True,
                                             states={'draft': [('readonly', False)],
                                                     'cancelled': [('readonly', False)]})
    # expected_price = fields.Monetary(related="property_id.expected_price")
    property_selling_price = fields.Monetary(readonly=True, required=True,
                                             states={'draft': [('readonly', False)],
                                                     'cancelled': [('readonly', False)]}, tracking=True)
    # property_sale_offer_price = fields.Monetary(related="sale_offer_id.offer_price")  # FIXME remove related

    # Property Rent Fields
    rent_price = fields.Monetary(tracking=True, track_visibility='onchange')
    rent_uom = fields.Selection([("month", "Month")], track_visibility='onchange')
    minimum_rent_duration = fields.Integer()
    minimum_rent_duration_uom = fields.Selection([("month", "Month(s)")])
    security_deposit_amount = fields.Monetary(readonly=True,
                                              states={'draft': [('readonly', False)],
                                                      'cancelled': [('readonly', False)]})
    client_expected_rent_duration = fields.Integer("Rent Duration", readonly=True, tracking=True,
                                                   states={'draft': [('readonly', False)],
                                                           'cancelled': [('readonly', False)]})
    rent_duration_uom = fields.Selection([("month", "Month(s)")], default="month", readonly=True,
                                         states={'draft': [('readonly', False)],
                                                 'cancelled': [('readonly', False)]})
    property_rent_price = fields.Monetary(readonly=True, required=True, tracking=True,
                                          states={'draft': [('readonly', False)],
                                                  'cancelled': [('readonly', False)]})
    rent_offer_id = fields.Many2one("property.rent.offer", string="Rent Offer", tracking=True)
    all_valid_rent_offer_ids = fields.Many2many("property.rent.offer")

    property_offer_price = fields.Monetary(tracking=True)
    installment_option = fields.Boolean(related="property_id.installment_option", string="Has Installment Options")
    amount_installment_ids = fields.One2many('amount.installment', 'property_contract_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    no_of_installment = fields.Integer()
    total_emi_amount = fields.Monetary(compute='_compute_paid_installment', string="Total Contract Amount")
    paid_installment_emi = fields.Monetary(compute='_compute_paid_installment', string="Total Paid Amount")
    remaining_balance = fields.Monetary(compute='_compute_paid_installment', string="Total Due Amount")
    tax_ids = fields.Many2many('account.tax', string='Taxes', domain=[('type_tax_use', '=', 'sale')], readonly=True,
                               states={'draft': [('readonly', False)], 'cancelled': [('readonly', False)]})
    # default=lambda self: self.env.company.account_sale_tax_id,
    tax_amount = fields.Monetary(compute='_compute_paid_installment')
    contract_total_amount_with_tax = fields.Monetary(compute='_compute_paid_installment', store=True)
    config_installment_id = fields.Many2one("config.installment", string="Installment Scheme")
    state = fields.Selection(
        [('draft', 'Draft'), ('sent', 'Contract Sent'), ('confirmed', 'Confirmed'), ('done', 'Done'),
         ('cancelled', 'Cancelled')], tracking=True, default='draft')

    payment_paid = fields.Selection(
        [("all", "Complete"), ("installment", "By Installment"), ("rental_installment", "Rental Installment")],
        required=True, string="Payment to Pay", default='all', track_visibility='onchange', readonly=True,
        states={'draft': [('readonly', False)], 'cancelled': [('readonly', False)]})
    invoice_id = fields.Many2one("account.move", "Invoice for Complete Payment")
    attachment_ids = fields.Many2many("ir.attachment")
    confirmation_datetime = fields.Datetime( track_visibility='onchange')
    down_payment_amount = fields.Monetary()
    last_payment = fields.Monetary()
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    qr_code = fields.Binary('QRcode', compute="_generate_qr")


    def _generate_qr(self):
        "method to generate QR code"
        for rec in self:
            if qrcode and base64:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=5,
                    border=5,
                )
                amount = 0
                if rec.remaining_balance==0:
                    amount = rec.contract_total_amount_with_tax
                else:
                    amount = rec.remaining_balance
                qr.add_data(rec.company_id.name)
                # qr.add_data(", Payment Reference : ")
                # qr.add_data(rec.payment_reference)
                qr.add_data(", Customer : ")
                qr.add_data(rec.partner_id.name)
                qr.add_data(",Contract Date : ")
                qr.add_data(rec.contract_start_date)
                qr.add_data(",Due Amount : ")
                qr.add_data(amount)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({'qr_code': qr_image})

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False

        if force_confirmation_template or (self.state == 'confirmed'):
            template_id = self.env['ir.model.data']._xmlid_to_res_id(
                'real_estate_advertisement.mail_template_contract_confirmation',
                raise_if_not_found=False)
        if not template_id:
            template_id = self.env['ir.model.data']._xmlid_to_res_id(
                'real_estate_advertisement.email_template_draft_contract',
                raise_if_not_found=False)

        return template_id

    def action_contract_send(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'property.property.contract',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_con_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            # 'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _send_contract_confirmation_mail(self):
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        template_id = self._find_mail_template(force_confirmation_template=True)
        if template_id:
            for order in self:
                order.with_context(force_send=True).message_post_with_template(template_id, composition_mode='comment',
                                                                               email_layout_xmlid="mail.mail_notification_paynow")

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_con_as_sent'):
            self.filtered(lambda o: o.state == 'draft').with_context(tracking_disable=True).write({'state': 'sent'})
        return super(PropertyContract, self.with_context(
            mail_post_autofollow=self.env.context.get('mail_post_autofollow', True))).message_post(**kwargs)

    # @api.onchange("config_installment_id")
    # def onchange_config_installment(self):
    #     if self.payment_paid == "installment" and self.config_installment_id:
    #         self.no_of_installment = self.config_installment_id.no_of_installment
    #     else:
    #         self.no_of_installment = 0

    def _track_subtype(self, init_values):
        self.ensure_one()
        if 'state' in init_values and self.state == 'confirmed':
            return self.env.ref('real_estate_advertisement.mt_contract_confirmed')
        elif 'state' in init_values and self.state == 'done':
            template_id = self.env.ref('real_estate_advertisement.mail_template_contract_done',
                                       raise_if_not_found=False)
            if template_id:
                template_id.send_mail(res_id=self.id, force_send=True,
                                      notif_layout="mail.mail_notification_paynow")
            return self.env.ref('real_estate_advertisement.mt_contract_done')
        return super(PropertyContract, self)._track_subtype(init_values)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        for contract in self:
            if contract.state not in ('draft', 'cancelled'):
                raise UserError(
                    _('You can not delete a confirmed or a done contract. You must first cancel it.'))
            if contract.state == "draft":
                self.property_id.state = "available"

    @api.onchange("payment_paid")
    def check_payment_paid_options(self):
        if self.payment_paid == "rental_installment":
            if self.property_id.property_for != "rent":
                raise ValidationError("Rental Installment option is only available for rental properties!")
        elif self.payment_paid == "all" or self.payment_paid == "installment":
            if self.property_id.property_for == "rent":
                raise ValidationError(
                    "Complete or By Installment option is not available for rental properties, select Rental Installment!")

    @api.onchange("sale_offer_id", "rent_offer_id")
    def show_offer_price(self):
        if self.rent_offer_id:
            self.property_offer_price = self.rent_offer_id.offer_price
            # self.property_rent_price = self.rent_offer_id.offer_price
        elif self.sale_offer_id:
            self.property_offer_price = self.sale_offer_id.offer_price
            # self.property_selling_price = self.sale_offer_id.offer_price
        else:
            self.property_offer_price = 0

        if not self.sale_offer_id:
            self.property_selling_price = self.property_id.expected_price
        if not self.rent_offer_id:
            # self.property_rent_price = self.property_id.rent_price
            self._onchange_property_id()

    @api.onchange("client_expected_rent_duration")
    def update_rent_price(self):
        if self.client_expected_rent_duration < self.minimum_rent_duration:
            raise ValidationError("Can't set Rent Duration less than the Minimum Rent Duration!")
        else:
            self.property_rent_price = self.client_expected_rent_duration * self.rent_price

    def apply_offer(self):
        if self.rent_offer_id:
            # self.property_offer_price = self.rent_offer_id.offer_price
            # self.property_rent_price = self.rent_offer_id.offer_price

            self.rent_price = self.rent_offer_id.offer_price
            self.rent_uom = self.property_id.rent_uom
            if self.rent_offer_id.duration_unit == 'year':
                self.minimum_rent_duration = self.rent_offer_id.duration * 12
            self.minimum_rent_duration_uom = 'month'
            # self.security_deposit_amount = self.property_id.security_deposit_amount
            self.client_expected_rent_duration = self.minimum_rent_duration
            self.rent_duration_uom = self.minimum_rent_duration_uom
            if self.minimum_rent_duration_uom == self.rent_uom:
                self.property_rent_price = self.client_expected_rent_duration * self.rent_price

        elif self.sale_offer_id:
            # self.property_offer_price = self.sale_offer_id.offer_price
            self.property_selling_price = self.sale_offer_id.offer_price
        # else:
        #     self.property_offer_price = 0

        if not self.sale_offer_id:
            self.property_selling_price = self.property_id.expected_price
        if not self.rent_offer_id:
            self.property_rent_price = self.property_id.rent_price

    def create_invoice(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "emi.payment.wizards",
            "view_mode": "form",
            "name": "Create Invoice",
            "target": "new",
            "context": {
                "default_total_amount": self.contract_total_amount_with_tax,
                "default_paid_amount": self.contract_total_amount_with_tax,
                "invoice_line_desc": str(self.property_id.name) + ", " + str(self.main_property_id.name) + " Amount",
                "partner_id": self.partner_id.id,
                # "default_amount_installment_id": self.id,
                # "per_day_fine_percent": self.property_contract_id.config_installment_id.delay_fine,
                # "delay_in_days": date.today().day - self.due_date.day,
                # "date": date.today().day > self.due_date.day,
                # "default_fine_on_paid_amount": self.delay_fine_amount,
                # "invoice_date_due": self.due_date}
            }
        }

    def view_invoice(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [('id', '=', self.invoice_id.id)],
            "name": "Contract Payment Invoice",
        }

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('property.property.contract') or 'New'
        rec = super(PropertyContract, self).create(vals)
        rec.property_id.state = "in_contract"
        rec.message_subscribe(partner_ids=rec.partner_id.ids)

        return rec

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange('responsible_person_id')
    def _onchange_responsible_person_id(self):
        if self.responsible_person_id:
            user_id = self.env["res.users"].sudo().search([("partner_id", "=", self.responsible_person_id.id)], limit=1)
            if user_id and user_id.has_group("real_estate_advertisement.group_real_estate_user"):
                self.user_id = user_id.id
            else:
                raise ValidationError("Only Property Users are allowed!")

    @api.onchange('property_id', 'partner_id')
    def _onchange_property_id(self):
        if self.property_id:
            self.responsible_person_id = self.property_id.responsible_person_id.id
            user_id = self.env["res.users"].sudo().search([("partner_id", "=", self.responsible_person_id.id)], limit=1)
            if user_id and user_id.has_group("real_estate_advertisement.group_real_estate_user"):
                self.user_id = user_id.id
            else:
                raise ValidationError("Only Property Users are allowed!")

        if self.property_id and self.property_id.property_for == "sale":
            self.availability = self.property_id.availability
            if self.property_id.availability == 'from_date':
                self.date_availability = self.property_id.date_availability
            else:
                self.date_availability = False
            if self.partner_id:
                offer_ids = self.property_id.sale_offer_ids.filtered(lambda offer: (
                                                                                           offer.partner_id == self.partner_id or not offer.partner_id) and offer.state == "active")
                if offer_ids:
                    self.all_valid_sale_offer_ids = False
                    self.all_valid_sale_offer_ids = [(6, 0, offer_ids.ids)]
                    self.offer_info_message = "There are offers available for you for this property. " \
                                              "You can select the best offer and get the benefits!"
                else:
                    self.offer_info_message = False
                    self.all_valid_sale_offer_ids = False
            else:
                self.offer_info_message = False
                self.all_valid_sale_offer_ids = False

            # res = {
            #     "domain": {
            #         "sale_offer_id": [("id", "in", self.property_id.sale_offer_ids.ids)]
            #     }
            # }
            # return res
        elif self.property_id and self.property_id.property_for == "rent":
            self.rent_price = self.property_id.rent_price
            self.rent_uom = self.property_id.rent_uom
            self.minimum_rent_duration = self.property_id.minimum_rent_duration
            self.minimum_rent_duration_uom = self.property_id.minimum_rent_duration_uom
            self.security_deposit_amount = self.property_id.security_deposit_amount
            self.client_expected_rent_duration = self.minimum_rent_duration
            self.rent_duration_uom = self.minimum_rent_duration_uom
            if self.minimum_rent_duration_uom == self.rent_uom:
                self.property_rent_price = self.client_expected_rent_duration * self.rent_price
            # FIXME : Also cover the different uom e.g. rent price is set by day and minimum rent duration in months
            self.payment_paid = "rental_installment"

            if self.partner_id:
                # FIXME: Update to add the check the offer by date, only show offers for that date
                offer_ids = self.property_id.rent_offer_ids.filtered(lambda offer: (
                                                                                           offer.partner_id == self.partner_id or not offer.partner_id) and offer.state == "active")
                if offer_ids:
                    self.all_valid_rent_offer_ids = [(6, 0, offer_ids.ids)]
                    self.offer_info_message = "There are offers available for you for this property. " \
                                              "You can select the best offer and get the benefits!"
                else:
                    self.offer_info_message = False
                    self.all_valid_rent_offer_ids = False
            else:
                self.offer_info_message = False
                self.all_valid_rent_offer_ids = False
        else:
            self.date_availability = False
            self.offer_info_message = False
            self.all_valid_sale_offer_ids = False
            self.all_valid_rent_offer_ids = False
            # result = {
            #     "domain": {
            #         'sale_offer_id': [('id', 'in', self.property_id.rent_offer_ids.ids)]
            #     }
            # }
            #
            # print('res', result)
            # return result

    def _compute_paid_installment(self):
        for contract in self:
            total_emi = 0
            total_paid = 0
            total_balance = 0
            if contract.payment_paid in ["installment", "rental_installment"]:
                for rec in contract.amount_installment_ids:
                    total_emi += rec.amount_total
                    total_paid += rec.paid_amount
                    total_balance += rec.balance_amount
                    print('rec.balance_amount', rec.balance_amount)
            elif contract.payment_paid == "all":
                total_emi = contract.property_selling_price
                total_paid = (
                        contract.invoice_id.amount_total - contract.invoice_id.amount_residual) if contract.invoice_id else 0
                tax_amount_dict = contract.tax_ids.compute_all(
                    total_emi,
                    quantity=1.0,
                    currency=contract.currency_id,
                    partner=contract.partner_id,
                    handle_price_include=False,
                )
                print("...................", contract.invoice_id, contract.invoice_id.amount_residual)
                tax_amount = tax_amount_dict['total_included'] - tax_amount_dict['total_excluded']
                total_balance = contract.invoice_id.amount_residual if contract.invoice_id else tax_amount + total_emi
                print("total_balance", total_balance)

            contract.total_emi_amount = total_emi
            contract.paid_installment_emi = total_paid
            contract.remaining_balance = total_balance
            tax_amount_dict = contract.tax_ids.compute_all(
                total_emi,
                quantity=1.0,
                currency=contract.currency_id,
                partner=contract.partner_id,
                handle_price_include=False,
            )
            print(tax_amount_dict)
            tax_amount = tax_amount_dict['total_included'] - tax_amount_dict['total_excluded']
            contract.tax_amount = tax_amount
            contract.contract_total_amount_with_tax = total_emi + tax_amount

    def action_draft(self):
        if self.property_id.state == "available":
            self.state = 'draft'
            self.property_id.state = "in_contract"
        else:
            if self.property_id.property_for == "rent":
                raise ValidationError(
                    "The selected property is already in other contract or On Rent! Unable to proceed with this contract.")
            else:
                raise ValidationError(
                    "The selected property is already in other contract or sold! Unable to proceed with this contract.")

    def action_confirmed(self):
        if self.payment_paid == "installment":
            if not self.amount_installment_ids:
                raise ValidationError("Add the installment lines before confirm!")
            emi_date = datetime.today()
            if self.config_installment_id.duration_type == 'days':
                due_date = emi_date + relativedelta(days=1)
            elif self.config_installment_id.duration_type == 'months':
                due_date = emi_date + relativedelta(months=1)
            else:
                due_date = emi_date + relativedelta(months=1)
            # due_date = emi_date + timedelta(self.config_installment_id.apply_fine_after)
            for amount_installment in self.amount_installment_ids:
                amount_installment.start_date = emi_date
                amount_installment.due_date = due_date

                if self.config_installment_id.duration_type=='days':
                     emi_date = emi_date + relativedelta(days=self.config_installment_id.duration)
                if self.config_installment_id.duration_type=='months':
                     emi_date = emi_date + relativedelta(months=self.config_installment_id.duration)
                due_date = emi_date + timedelta(self.config_installment_id.apply_fine_after)
        elif self.payment_paid == "rental_installment":
            if not self.amount_installment_ids:
                raise ValidationError("Add the rental installment lines before confirm!")
            rental_security_amount_line = self.amount_installment_ids.filtered(
                lambda line: line.is_rental_security_amount_line)

            rent_pay_date = datetime.today()
            due_date = rent_pay_date + timedelta(self.config_installment_id.apply_fine_after)

            if rental_security_amount_line:
                rental_line = self.amount_installment_ids - rental_security_amount_line
                rental_security_amount_line.start_date = rent_pay_date
                rental_security_amount_line.due_date = due_date
            else:
                rental_line = self.amount_installment_ids
            for amount_installment in rental_line:
                amount_installment.start_date = rent_pay_date
                amount_installment.due_date = due_date
                if self.rent_uom == 'day':
                    rent_pay_date = rent_pay_date + relativedelta(days=1)
                if self.rent_uom == "month":
                    rent_pay_date = rent_pay_date + relativedelta(months=1)
                due_date = rent_pay_date + timedelta(self.config_installment_id.apply_fine_after)

        self.state = 'confirmed'
        self.confirmation_datetime = fields.Datetime.today()
        if self.property_id.property_for == "rent":
            self.property_id.state = "on_rent"
        else:
            self.property_id.state = "sold"
        self._send_contract_confirmation_mail()

    def action_done(self):
        if self.remaining_balance:
            raise ValidationError("Unable to complete the contract!\nPayment not completed.")
        else:
            self.contract_complete_date = fields.Datetime.now()
            self.state = "done"

    def action_cancelled(self):
        self.state = "cancelled"
        self.property_id.state = "available"

    # @api.onchange("sale_offer_id")
    # def onchange_offer_id(self):
    #     if self.sale_offer_id:
    #         self.property_selling_price = self.sale_offer_id.offer_price
    #     else:
    #         self.property_selling_price = self.property_id.expected_price

    def create_installment(self):
        total_amount = 0
        config_installment_id = False
        wizard_name = "Create"
        tax_amount = 0
        amount = 0
        if self.payment_paid == "rental_installment":
            amount = self.property_rent_price + self.security_deposit_amount
            if self.tax_ids:
                tax_amount_dict = self.tax_ids.compute_all(
                    amount,
                    quantity=1.0,
                    currency=self.currency_id,
                    partner=self.partner_id,
                    handle_price_include=False,
                )
                print(tax_amount_dict)
                tax_amount = tax_amount_dict['total_included'] - tax_amount_dict['total_excluded']
            total_amount = amount + tax_amount
            config_installment_id = self.property_id.installment_scheme_ids and self.property_id.installment_scheme_ids[
                0].id
            wizard_name = "Creating Rental Installments"
        elif self.payment_paid == "installment":
            amount = self.property_selling_price
            if self.tax_ids:
                tax_amount_dict = self.tax_ids.compute_all(
                    amount,
                    quantity=1.0,
                    currency=self.currency_id,
                    partner=self.partner_id,
                    handle_price_include=False,
                )
                print(tax_amount_dict)
                tax_amount = tax_amount_dict['total_included'] - tax_amount_dict['total_excluded']
            total_amount = amount + tax_amount
            wizard_name = "Creating Installments"
        return {
            "type": "ir.actions.act_window",
            "res_model": "property.installment.wizards",
            "view_mode": "form",
            "name": wizard_name,
            "target": "new",
            "context": {
                "default_total_amount": total_amount,
                "default_config_installment_id": config_installment_id,
                "default_untaxed_total_amount": amount,
                "default_use_for": self.property_for,

            }
        }

    def fetch_contracts_to_remind(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        send_contract_payment_reminder = bool(
            ICPSudo.get_param('real_estate_advertisement.send_contract_payment_reminder'))
        remind_before = int(ICPSudo.get_param('real_estate_advertisement.remind_before')) or 5
        remind_on_due_date = ICPSudo.get_param('real_estate_advertisement.remind_on_due_date')

        remind_every_day_after_due_date = ICPSudo.get_param('real_estate_advertisement.remind_every_day_after_due_date')

        today = datetime.today().date()
        if send_contract_payment_reminder:
            contract_ids = self.search([("state", "=", "confirmed")])
            remind_installment_ids = self.env["amount.installment"]
            for contract_id in contract_ids:

                if contract_id.amount_installment_ids:
                    for installment_id in contract_id.amount_installment_ids.sorted(key=lambda k: k['sequence']):
                        remind_date = installment_id.start_date + timedelta(days=remind_before)
                        if installment_id.state != 'paid' and (
                                remind_date == today or (remind_on_due_date and installment_id.due_date == today) or (
                                remind_every_day_after_due_date and installment_id.due_date < today)):
                            remind_installment_ids += installment_id
                            break

            if remind_installment_ids:
                print("remind_installment_ids", remind_installment_ids)
                template_id = self.env.ref('real_estate_advertisement.mail_template_contract_installment_reminder',
                                           raise_if_not_found=False)
                if template_id:
                    for installment in remind_installment_ids:
                        template_id.send_mail(res_id=installment.id, force_send=True,
                                              notif_layout="mail.mail_notification_paynow")
