from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import misc, UserError


class PropertyInstallment(models.TransientModel):
    _name = 'property.installment.wizards'
    _description = 'Installment'

    untaxed_total_amount = fields.Monetary()
    total_amount = fields.Monetary()
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    down_payment = fields.Monetary(required=True)
    down_payment_in_word = fields.Char("Down Payment In Words")
    remain_amount = fields.Monetary(compute='_compute_down_payment')
    installment_amount = fields.Monetary("Total Remaining Payable Amount With Interest")

    monthly_emi = fields.Monetary("EMI")
    message = fields.Char()
    config_installment_id = fields.Many2one('config.installment', string="Installment Scheme", required=True,
                                            domain='[("use_for", "=",use_for)]')
    use_for = fields.Selection([("sale", "Sale"), ("rent", "Rent")])
    amount_installment_id = fields.Many2one('amount.installment')
    last_payment = fields.Monetary(required=True)


    @api.onchange("config_installment_id", "down_payment","last_payment")
    def onchange_config_installment(self):
        self.down_payment_in_word = self.currency_id.amount_to_text(self.down_payment)
        if self.config_installment_id and self.config_installment_id.use_for == 'sale' and self.remain_amount:
            monthly_interest_rate=0
            if self.config_installment_id.extra_percentage>0:
                monthly_interest_rate = self.config_installment_id.extra_percentage / (12 * 100)
            last=0
            if self.last_payment>0:
                last=1

            time = self.config_installment_id.no_of_installment-last
            div=1
            if monthly_interest_rate>0:
                emi = self.remain_amount * monthly_interest_rate * ((1 + monthly_interest_rate) ** time) / (
                        (1 + monthly_interest_rate) ** time - 1)
            else:
                emi=self.remain_amount/time

            self.monthly_emi = round(emi)
            self.installment_amount = self.monthly_emi * time

    @api.depends('down_payment','last_payment')
    def _compute_down_payment(self):
        self.remain_amount=0
        if self.total_amount:
            self.remain_amount = self.total_amount - self.down_payment -self.last_payment

    @api.onchange('monthly_emi')
    def onchange_monthly_emi(self):
        if self.monthly_emi:
            installment = misc.format_amount(self.env, self.installment_amount, self.currency_id)
            m_emi = misc.format_amount(self.env, self.monthly_emi, self.currency_id)

            self.message = 'Your total installment is {} and number of installment is {}.\nMonthly EMI to pay is {}'.format(
                installment, self.config_installment_id.no_of_installment, m_emi)

    @api.constrains('total_amount')
    def _check_total_amount(self):
        print('ssssssssssssssssssss', self)
        if self.down_payment:
            print('self.down_payment', self.down_payment)
            if self.down_payment > self.total_amount:
                self.down_payment = 0
                raise UserError(_('Down payment should not be greater than Total Amount.'))
            if self.last_payment > self.total_amount:
                self.last_payment = 0
                raise UserError(_('Down payment should not be greater than Total Amount.'))

    def create_installment_action(self):

        # print("installment_amount",self.installment_amount)
        # if self.installment_amount:
        #     self.amount_installment_id.description = self.installment_amount
        # no_of_installment = fields.Integer()
        # total_emi_amount = fields.Monetary()
        # paid_installment_emi = fields.Monetary()
        # remaining_balance = fields.Monetary()

        contract_ids = self._context.get("active_ids")
        print("contract_ids", contract_ids)
        if contract_ids:

            contract_id = self.env["property.property.contract"].browse(contract_ids)
            if contract_id and contract_id.property_for == "sale":
                print("contract_id", contract_id)
                contract_id.no_of_installment = self.config_installment_id.no_of_installment
                contract_id.config_installment_id = self.config_installment_id.id
                # contract_id.total_emi_amount = self.installment_amount
                contract_id.paid_installment_emi = self.monthly_emi
                sequence = 1
                tax_amount = 0
                if contract_id.tax_ids:
                    tax_amount_dict = contract_id.tax_ids.compute_all(
                        self.down_payment,
                        quantity=1.0,
                        currency=contract_id.currency_id,
                        partner=contract_id.partner_id,
                        handle_price_include=False,
                    )
                    print(tax_amount_dict)
                    tax_amount = tax_amount_dict['total_included'] - tax_amount_dict['total_excluded']
                installment_list=[]
                if self.down_payment>0:
                    installment_list = [(0, 0, {
                        "description": "Down Payment",
                        "untaxed_amount": self.down_payment - tax_amount,
                        "amount_with_tax": self.down_payment,
                        "sequence": sequence,
                        "state": "unpaid"
                    })]

                print('self.monthly_emi', self.monthly_emi)
                print('')

                # if contract_id.state == 'confirmed':
                #     emi_date = datetime.today()
                #     print('emi_date = datetime.today', emi_date)
                #     due_date = emi_date + timedelta(self.config_installment_id.apply_fine_after)
                #     print('due_date ', due_date)
                # contract_id.total_emi_amount = 0

                last=0
                if self.last_payment>0:
                    last=1

                for rec in range(self.config_installment_id.no_of_installment-last):
                    # self.installment_amount = self.installment_amount - self.monthly_emi
                    # contract_id.remaining_balance = self.installment_amount

                    # remaining_balance = self.monthly_emi - self.paid_amount

                    # if self.monthly_emi == self.paid_amount:
                    sequence += 1
                    tax_amount = 0
                    if contract_id.tax_ids:
                        tax_amount_dict = contract_id.tax_ids.compute_all(
                            self.monthly_emi,
                            quantity=1.0,
                            currency=contract_id.currency_id,
                            partner=contract_id.partner_id,
                            handle_price_include=False,
                        )
                        print(tax_amount_dict)
                        tax_amount = tax_amount_dict['total_included'] - tax_amount_dict['total_excluded']
                    installment_list.append([0, 0, {
                        "description": "Monthly Installment",
                        "untaxed_amount": self.monthly_emi - tax_amount,
                        "amount_with_tax": self.monthly_emi,
                        "sequence": sequence,
                        "state": "unpaid"
                    }])
            if self.last_payment>0:
                tax_amount_dict = contract_id.tax_ids.compute_all(
                    self.last_payment,
                    quantity=1.0,
                    currency=contract_id.currency_id,
                    partner=contract_id.partner_id,
                    handle_price_include=False,
                )
                print(tax_amount_dict)
                tax_amount = tax_amount_dict['total_included'] - tax_amount_dict['total_excluded']
                installment_list.append([0, 0, {
                    "description": "Last Payment",
                    "untaxed_amount": self.last_payment - tax_amount,
                    "amount_with_tax": self.last_payment,
                    "sequence": sequence,
                    "state": "unpaid"
                }])


                if installment_list:
                    contract_id.amount_installment_ids = False
                contract_id.amount_installment_ids = installment_list
                if self.down_payment:
                    contract_id.down_payment_amount = self.down_payment
                if self.last_payment:
                    contract_id.last_payment=self.last_payment

            elif contract_id and contract_id.property_for == "rent" and contract_id.payment_paid == "rental_installment":
                print("contract_id", contract_id)
                contract_id.no_of_installment = contract_id.client_expected_rent_duration
                contract_id.config_installment_id = self.config_installment_id.id
                sequence = 1
                installment_list = []
                if contract_id.security_deposit_amount:
                    tax_amount = 0
                    if contract_id.tax_ids:
                        tax_amount_dict = contract_id.tax_ids.compute_all(
                            contract_id.security_deposit_amount,
                            quantity=1.0,
                            currency=contract_id.currency_id,
                            partner=contract_id.partner_id,
                            handle_price_include=False,
                        )
                        print(tax_amount_dict)
                        tax_amount = tax_amount_dict['total_included'] - tax_amount_dict['total_excluded']
                    installment_list = [(0, 0, {
                        "description": "Security Deposit Amount for %s, %s" % (
                            contract_id.property_id.name, contract_id.property_id.main_property_id.name),
                        "untaxed_amount": contract_id.security_deposit_amount,
                        "amount_with_tax": contract_id.security_deposit_amount + tax_amount,
                        "sequence": sequence,
                        "state": "unpaid",
                        "is_rental_security_amount_line": True,
                    })]
                line_desc = "Monthly Rent Amount " if contract_id.rent_uom == "month" else "Daily Rent Amount"
                tax_amount = 0
                if contract_id.tax_ids:
                    tax_amount_dict = contract_id.tax_ids.compute_all(
                        contract_id.rent_price,
                        quantity=1.0,
                        currency=contract_id.currency_id,
                        partner=contract_id.partner_id,
                        handle_price_include=False,
                    )
                    print(tax_amount_dict)
                    tax_amount = tax_amount_dict['total_included'] - tax_amount_dict['total_excluded']
                for rec in range(contract_id.client_expected_rent_duration):
                    sequence += 1
                    installment_list.append([0, 0, {
                        "description": line_desc + " %s, %s" % (
                            contract_id.property_id.name, contract_id.property_id.main_property_id.name),
                        "untaxed_amount": contract_id.rent_price,
                        "amount_with_tax": contract_id.rent_price + tax_amount,
                        "sequence": sequence,
                        "state": "unpaid"
                    }])

                if installment_list:
                    contract_id.amount_installment_ids = False
                contract_id.amount_installment_ids = installment_list
