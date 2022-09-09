from odoo import fields, models, api,_


class ModelName(models.TransientModel):
    _name = 'real.report.wizard'

    date_from = fields.Date()
    date_to = fields.Date()

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Partner_ids')

    def view_contract(self):
        domain=[('confirmation_datetime','>=',self.date_from)\
                                                                      ,('confirmation_datetime','<=',self.date_to)]

        # contract_ids = self.env['property.property.contract'].search()
        if self.partner_ids:
            domain.append(('partner_id','in',self.partner_ids.ids))
        return {
            'name': _('Contracts'),
            'view_mode': 'tree,form',
            'view_type': 'form',

            'res_model': 'property.property.contract',
            'domain': domain,
            'type': 'ir.actions.act_window',
            'target': 'current'
        }
    def view_installment(self):
        print("=================",type(self.date_to))
        domain=[('due_date','>=',self.date_from) ,('due_date','<=',self.date_to)]
        domain.append(('balance_amount','>',0))
        # contract_ids = self.env['property.property.contract'].search()
        if self.partner_ids:
            domain.append(('partner_id','in',self.partner_ids.ids))
        return {
            'name': _('Installment'),
            'view_mode': 'tree,form',
            'view_type': 'form',

            'res_model': 'amount.installment',
            'domain': domain,
            'type': 'ir.actions.act_window',
            'target': 'current'
        }
