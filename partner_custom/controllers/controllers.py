# -*- coding: utf-8 -*-
# from odoo import http


# class PartnerCustom(http.Controller):
#     @http.route('/partner_custom/partner_custom', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/partner_custom/partner_custom/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('partner_custom.listing', {
#             'root': '/partner_custom/partner_custom',
#             'objects': http.request.env['partner_custom.partner_custom'].search([]),
#         })

#     @http.route('/partner_custom/partner_custom/objects/<model("partner_custom.partner_custom"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('partner_custom.object', {
#             'object': obj
#         })
