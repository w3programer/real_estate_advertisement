import datetime

from odoo import fields, models, api, _
from datetime import date

from odoo.exceptions import ValidationError
from odoo.tools import float_compare

from dateutil.relativedelta import relativedelta
class AmountInstallment(models.Model):
    _name = 'amount.installment'
    _inherit = ['mail.thread']
    _description = "Property Installment Amount"

    name = fields.Char( track_visibility='onchange')
    sequence = fields.Integer( track_visibility='onchange')
    start_date = fields.Date(string="Start Date", track_visibility='onchange')
    due_date = fields.Date(string="Due Date")
    installment_payment_datetime = fields.Datetime()

    property_contract_id = fields.Many2one("property.property.contract", ondelete='cascade')
    partner_id = fields.Many2one(related='property_contract_id.partner_id')
    currency_id = fields.Many2one("res.currency", related="property_contract_id.currency_id")
    description = fields.Text(string="Description")
    invoice_ids = fields.One2many("account.move", 'amount_installment_id')
    invoice_date = fields.Date()
    total_paid = fields.Float(required=True)

    # invoiced_amount = fields.Float(compute="_compute_amount")

    # installment_total_with_fine = fields.Float()
    is_rental_security_amount_line = fields.Boolean()
    def sale_whatsapp(self):
        record_phone = self.partner_id.mobile
        if not record_phone:
            view = self.env.ref('odoo_whatsapp_integration.warn_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = "Please add a mobile number!"
            return {
                'name': 'Mobile Number Field Empty',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'display.error.message',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context
            }
        if not record_phone[0] == "+":
            view = self.env.ref('odoo_whatsapp_integration.warn_message_wizard')
            view_id = view and view.id or False
            context = dict(self._context or {})
            context['message'] = "No Country Code! Please add a valid mobile number along with country code!"
            return {
                'name': 'Invalid Mobile Number',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'display.error.message',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': context
            }
        else:
            return {'type': 'ir.actions.act_window',
                    'name': _('Whatsapp Message'),
                    'res_model': 'whatsapp.wizard',
                    'target': 'new',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'context': {
                        'default_template_id': self.env.ref('real_estate_advertisement.whatsapp_sales_template_installment').id},
                    }

    # Amount Fields

    untaxed_amount = fields.Float(string="Untaxed Amount")
    amount_with_tax = fields.Float(string="Main Amount")  # Tax Includes
    delay_fine_amount = fields.Float(compute="_compute_amount", string="Delay Fine")
    fully_invoiced = fields.Boolean(compute="_compute_amount", )
    paid_amount = fields.Float(string="Paid Amount", compute="_compute_amount")
    balance_amount = fields.Float(string="Remaining Amount", compute="_compute_amount")
    amount_total = fields.Float(compute="_compute_amount")  # amount_with_tax + delay_fine_amount

    state = fields.Selection([('unpaid', 'Unpaid'), ('delay', 'Delay'), ('partial', 'Partial Paid'), ('paid', 'Paid')],
                             string='Status', default="unpaid", compute="_compute_amount", tracking=True, store=True)

    def _track_subtype(self, init_values):
        self.ensure_one()
        print("Subtype")
        if 'state' in init_values and self.state == 'paid':
            template_id = self.env.ref('real_estate_advertisement.mail_template_contract_installment_paid_ack',
                                       raise_if_not_found=False)
            if template_id:
                template_id.send_mail(res_id=self.id, force_send=True,
                                      notif_layout="mail.mail_notification_paynow")
        return super(AmountInstallment, self)._track_subtype(init_values)

    def name_get(self):
        res = []
        for record in self:
            res.append((
                record.id,
                record.name or _('Installment #%s', record.sequence)
            ))
        return res

    @api.depends('invoice_ids.payment_state','invoice_ids')
    def _compute_amount(self):
        for rec in self:
            rec.delay_fine_amount = 0
            rec.fully_invoiced = False
            rec.paid_amount = 0
            rec.balance_amount = 0
            rec.amount_total = 0
            if not rec.due_date and not rec.start_date:
                rec.delay_fine_amount = 0
                rec.fully_invoiced = False
                rec.paid_amount = 0
                rec.balance_amount = 0
                rec.amount_total = 0
                rec.state = "unpaid"
            today_date = datetime.datetime.today().date()
            # Calculate fine if due date passed and invoice is not created
            if not rec.invoice_date and rec.due_date and today_date > rec.due_date:
                days = (today_date - rec.due_date).days
                print(">>>>>>>>>>>>>>>>>>>",days,rec.due_date)
                per_day_fine_percent = rec.property_contract_id.config_installment_id.delay_fine
                if per_day_fine_percent>0:
                    if rec.property_contract_id.config_installment_id.type == 'prec':

                        per_day_fine_amount = rec.amount_with_tax * per_day_fine_percent / 100
                    elif rec.property_contract_id.config_installment_id.type == 'amount':

                        per_day_fine_amount = per_day_fine_percent

                else:
                    per_day_fine_amount = rec.amount_with_tax
                total_fine = per_day_fine_amount * days
                rec.delay_fine_amount = total_fine
                rec.amount_total = total_fine + rec.amount_with_tax
                rec.state = "delay"
                rec.fully_invoiced = False
                rec.paid_amount = 0
                rec.balance_amount = total_fine + rec.amount_with_tax

            if rec.invoice_date and rec.due_date and rec.invoice_date > rec.due_date:
                days = (rec.invoice_date - rec.due_date).days
                per_day_fine_percent = rec.property_contract_id.config_installment_id.delay_fine
                if rec.property_contract_id.config_installment_id.type == 'prec':

                    per_day_fine_amount = rec.amount_with_tax * per_day_fine_percent / 100
                elif rec.property_contract_id.config_installment_id.type == 'amount':

                    per_day_fine_amount = per_day_fine_percent
                total_fine = per_day_fine_amount * days
                rec.delay_fine_amount = total_fine
                rec.amount_total = total_fine + rec.amount_with_tax
                invoice_due_total = invoice_total = 0
                for inv in rec.invoice_ids:
                    print("====================", inv.name, inv.move_type, inv.amount_residual)
                    if inv.move_type != 'entry':
                        invoice_due_total += inv.amount_residual
                        invoice_total += inv.amount_total


                # invoice_due_total = sum(rec.invoice_ids.mapped("amount_residual"))

                # invoice_total = sum(rec.invoice_ids.mapped("amount_total"))  # i.e. installment_total
                is_equal = float_compare(total_fine + rec.amount_with_tax, invoice_total,
                                         precision_digits=rec.property_contract_id.currency_id.decimal_places)

                if invoice_due_total:
                    is_equal_ = float_compare(total_fine + rec.amount_with_tax, invoice_due_total,
                                              precision_digits=rec.property_contract_id.currency_id.decimal_places)
                    if is_equal_ == 0:
                        rec.state = "unpaid"
                        rec.paid_amount = 0
                        rec.balance_amount = invoice_due_total
                        rec.fully_invoiced = True
                    else:
                        rec.state = "partial"
                        rec.paid_amount = invoice_total - invoice_due_total
                        rec.balance_amount = invoice_due_total
                elif is_equal == 0:
                    rec.state = "paid"
                    rec.paid_amount = total_fine + rec.amount_with_tax
                    rec.balance_amount = 0
                    rec.installment_payment_datetime = datetime.datetime.today()
                else:
                    rec.state = "partial"

                if is_equal == 0:
                    rec.fully_invoiced = True
                else:
                    rec.fully_invoiced = False

            if rec.invoice_date and rec.start_date and rec.due_date :
                # if rec.invoice_date and rec.start_date and rec.due_date and (
                #     rec.start_date <= rec.invoice_date <= rec.due_date):
                rec.delay_fine_amount = 0
                rec.amount_total = 0 + rec.amount_with_tax
                # rec.state = "unpaid"
                # rec.paid_amount = 0
                # rec.balance_amount = rec.amount_with_tax
                # rec.fully_invoiced = False
                # invoice_due_total = sum(rec.invoice_ids.mapped("amount_residual"))
                invoice_due_total=invoice_total=0
                for inv in rec.invoice_ids:
                    print("====================", inv.name, inv.move_type, inv.amount_residual)
                    if inv.move_type != 'entry':
                        invoice_due_total += inv.amount_residual
                        invoice_total += inv.amount_total
                # invoice_total = sum(rec.invoice_ids.mapped("amount_total"))  # i.e. installment_total

                is_equal = float_compare(rec.amount_with_tax, invoice_total,
                                         precision_digits=rec.property_contract_id.currency_id.decimal_places)

                if invoice_due_total:

                    is_equal_ = float_compare(rec.amount_with_tax, invoice_due_total,
                                              precision_digits=rec.property_contract_id.currency_id.decimal_places)
                    if is_equal_ == 0:
                        rec.state = "unpaid"
                        rec.paid_amount = 0
                        rec.balance_amount = invoice_due_total
                        rec.fully_invoiced = True
                    else:
                        rec.state = "partial"
                        rec.paid_amount = invoice_total - invoice_due_total
                        rec.balance_amount = invoice_due_total
                elif is_equal == 0:
                    rec.state = "paid"
                    rec.paid_amount = rec.amount_with_tax
                    rec.balance_amount = 0
                    rec.installment_payment_datetime = datetime.datetime.today()
                else:
                    rec.state = "partial"

                if is_equal == 0:
                    rec.fully_invoiced = True
                else:
                    rec.fully_invoiced = False
            #
            # if not rec.invoice_date and rec.start_date and rec.due_date and (
            #         rec.start_date <= today_date <= rec.due_date):

            if not rec.invoice_date and rec.due_date and today_date <= rec.due_date:
                print(">>>>>>>>>")
                rec.delay_fine_amount = 0
                rec.amount_total = 0 + rec.amount_with_tax
                rec.state = "unpaid"
                rec.paid_amount = 0
                rec.balance_amount = rec.amount_with_tax
                rec.fully_invoiced = False

    # @api.depends('invoice_ids.payment_state')
    # def _compute_amount_a(self):
    #     for rec in self:
    #
    #         print("rec.fully_invoiced", rec.fully_invoiced)
    #         invoice_total = 0
    #         if rec.invoice_ids:
    #             installment_total = rec.amount + rec.delay_fine_amount  # main amount + fine
    #             invoice_total = sum(rec.invoice_ids.mapped("amount_total"))  # i.e. installment_total
    #             # print('invoice_total', invoice_total)
    #             # un_invoiced_amount = installment_total - invoice_total + rec.delay_fine_amount
    #             invoice_due_total = sum(rec.invoice_ids.mapped("amount_residual"))
    #             # print('invoice_due_total', invoice_due_total)
    #             total_paid = invoice_total - invoice_due_total
    #             # print('total_paid', total_paid)
    #             rec.paid_amount = total_paid
    #             rec.invoiced_amount = invoice_total
    #             balance_amount = rec.balance_amount = invoice_due_total
    #
    #             if installment_total > balance_amount > 0:
    #                 if invoice_total == invoice_due_total:
    #                     rec.state = "unpaid"
    #                 else:
    #                     rec.state = "partial"
    #             elif balance_amount == 0 and invoice_due_total == 0:
    #                 rec.state = "paid"
    #             elif balance_amount == 0:
    #                 if invoice_total == invoice_due_total:
    #                     rec.state = "unpaid"
    #                 else:
    #                     rec.state = "partial"
    #
    #             elif installment_total == balance_amount:
    #                 rec.state = "unpaid"
    #             print("installment_total >>> ", installment_total)
    #             print("invoice_total >>> ", invoice_total)
    #             is_equal = float_compare(installment_total, invoice_total,
    #                                      precision_digits=rec.property_contract_id.currency_id.decimal_places)
    #             if is_equal == 0:
    #                 rec.fully_invoiced = True
    #                 rec.state = "paid"
    #             else:
    #                 rec.fully_invoiced = False
    #                 rec.state = "unpaid"
    #
    #         else:
    #             rec.paid_amount = 0
    #             rec.invoiced_amount = 0
    #             balance_amount = rec.balance_amount = rec.amount + rec.delay_fine_amount
    #             rec.state = "unpaid"
    #
    #         today_date = date.today()
    #         due_date = rec.due_date
    #         print("Due Date", due_date)
    #         if due_date and today_date > due_date and not rec.fully_invoiced:
    #
    #             days = (today_date - due_date).days
    #             print(">>>>>>>>>>", due_date, (today_date - due_date).days, balance_amount)
    #             per_day_fine_percent = rec.property_contract_id.config_installment_id.delay_fine
    #             per_day_fine_amount = balance_amount * per_day_fine_percent / 100
    #             total_fine = per_day_fine_amount * days
    #             rec.delay_fine_amount = total_fine
    #             rec.installment_total_with_fine = total_fine + rec.amount
    #             # self.balance_amount = self.balance_amount + (days *)
    #             # print('self.balance_amount', self.balance_amount)
    #             if invoice_total and balance_amount == 0:
    #                 rec.delay_fine_amount = invoice_total - rec.amount
    #                 rec.installment_total_with_fine = rec.delay_fine_amount + rec.amount
    #         else:
    #             rec.delay_fine_amount = 0
    #             rec.installment_total_with_fine = rec.amount
    def diff_month(d1, d2):
        return (d1.years - d2.years) * 12 + d1.months - d2.months
    def create_invoice(self):
        if self.property_contract_id.state!='confirmed':
            raise ValidationError("Please Confirm your contract ")
        current_installment_number = self.sequence
        previous_installment_line_ids = self.property_contract_id.amount_installment_ids.filtered(
            lambda installment_line: installment_line.sequence < current_installment_number)
        # if previous_installment_line_ids.filtered(lambda installment_line: installment_line.state != 'paid'):
        #     raise ValidationError(
        #         "Before creating the invoice for this installment, complete the payment of previous installments!")

        today = datetime.datetime.today().date()
        # if today < self.start_date:
        #     raise ValidationError("Can't accept payment for the installment before the start date!")
        # print(">>>>>>>>>>>>>",(date.today() - self.due_date).days,(date.today() - self.due_date))
        day_dely=0
        if self.property_contract_id.config_installment_id.from_delay =='day':
            day_dely=(date.today() - self.due_date).days
        elif self.property_contract_id.config_installment_id.from_delay =='week':
            day_dely = (date.today() - self.due_date).days
            day_dely=day_dely/7
        if self.property_contract_id.config_installment_id.from_delay =='month':
            day_dely=relativedelta(date.today(), self.due_date).months



        return {
            "type": "ir.actions.act_window",
            "res_model": "emi.payment.wizards",
            "view_mode": "form",
            "name": "Create Invoice For Installment",
            "target": "new",
            "context": {"default_total_amount": self.amount_total,
                        "default_paid_amount": self.untaxed_amount,
                        "default_tax_amount": self.amount_with_tax - self.untaxed_amount,
                        "default_amount_installment_id": self.id,
                        "per_day_fine_percent": self.property_contract_id.config_installment_id.delay_fine,
                        "delay_in_days": day_dely if day_dely>0 else 0,
                        # "delay_in_days": abs(day_dely) ,
                        "date": date.today().day > self.due_date.day,
                        "default_fine_on_paid_amount": self.delay_fine_amount,
                        "invoice_date_due": self.due_date}
        }

    def show_invoice(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "name": "Invoice ",
            "domain": [('id', 'in', self.invoice_ids.ids),('move_type','!=','entry')],
            "target": "current"
        }

    def print_installment_receipt(self):
        client_action = {
            'type': 'ir.actions.act_url',
            'name': "Installment Receipt",
            'target': 'new',
            'url': "/report/pdf/real_estate_advertisement.report_installment_receipt/%s" % self.id,
        }
        return client_action


class AccountMove(models.Model):
    _inherit = 'account.move'

    amount_installment_id = fields.Many2one('amount.installment')
