from odoo import fields, models, api,_
from io import BytesIO
import qrcode
import base64

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    amount_installment_id = fields.Many2one('amount.installment')

    def _create_payments(self):
        res=super(AccountPaymentRegister, self)._create_payments()
        print("===============",res)

        for rec in res:
            rec.amount_installment_id = self.amount_installment_id.id if self.amount_installment_id else ''

        return res
class Payment(models.Model):
    _inherit = 'account.payment'
    amount_installment_id = fields.Many2one('amount.installment')


    @api.model
    def create(self,vals):
        res=super(Payment, self).create(vals)
        if res.amount_installment_id:
            res.amount_installment_id.total_paid = res.amount
        return res




class ModelName(models.Model):
    _inherit = "account.move"



    qr_code = fields.Binary('QRcode', compute="_generate_qr")

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''

        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
                'default_amount_installment_id':self.amount_installment_id.id if self.amount_installment_id else '',
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

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
                amount=0
                if rec.state=='draft':
                    amount=rec.amount_total
                else:
                    amount=rec.amount_residual
                qr.add_data(rec.company_id.name)
                qr.add_data(", Payment Reference : ")
                qr.add_data(rec.payment_reference)
                qr.add_data(", Customer : ")
                qr.add_data(rec.partner_id.name)
                qr.add_data(",Invoice Date : ")
                qr.add_data(rec.invoice_date)
                qr.add_data(",Due Amount : ")
                qr.add_data(amount)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({'qr_code': qr_image})

