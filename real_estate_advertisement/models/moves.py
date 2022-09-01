from odoo import fields, models, api
from io import BytesIO
import qrcode
import base64


class ModelName(models.Model):
    _inherit = "account.move"

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

