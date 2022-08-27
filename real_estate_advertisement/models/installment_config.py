from odoo import fields, models, api


class ConfigInstallment(models.Model):
    _name = 'config.installment'
    _description = "Installment Configuration"

    name = fields.Char("Scheme Name", required=True)
    no_of_installment = fields.Integer("Total Number Of Installments")
    apply_fine_after = fields.Integer(required=True)
    extra_percentage = fields.Float("Extra % On Total Payable")
    delay_fine = fields.Float("Delay Fine % On Total Payable", required=True)
    from_delay = fields.Selection([('day', 'Day'), ('week', 'Week'), ('month', 'Month')], default="day", required=True)
    is_active = fields.Boolean("Active")
    use_for = fields.Selection([("sale", "Sale"), ("rent", "Rent")], default="sale", required=True)

    @api.onchange("use_for")
    def onchange_use_for(self):
        if self.use_for == "rent":
            self.no_of_installment = 0
            self.extra_percentage = 0

    def name_get(self):

        res = []
        for rec in self:
            name = rec.name or ''
            if rec.no_of_installment:
                name = name + " [" + str(rec.no_of_installment) + " Installments]"
            # if self._context.get('show_address'):
            #     if rec.display_address():
            #         address = rec.display_address()
            #         address = address.replace("\n\n", "\n")
            #         name = name + "\n" + address
            res.append((rec.id, name))
        return res
