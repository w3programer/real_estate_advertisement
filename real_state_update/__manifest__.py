# -*- coding: utf-8 -*-
{
    'name': "Real-estate Updates",

    'summary': """
        Bulx""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','real_estate_advertisement','account'],

    # always loaded
    'data': [
        'security/contact.xml',
        'security/ir.model.access.csv',
        # 'views/account_payment.xml',
        # 'views/account_payment_inherit.xml',
        'views/views.xml',
        # 'reports/send_money.xml',
        # 'reports/receive_money.xml',
        # 'reports/journal_entery_report.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}