# -*- coding: utf-8 -*-
{
    'name': "Property Sale & Rental Management",

    'summary': """Odoo Real Estate Property Rental and Sale Management App""",

    'description': """Property Sale & Rental Management app is complete solution all kind of property and housing 
    Management system. We can create main properties and properties and set various type of details for a property. 
    We can also create sale and rent offers for the properties and give our customers best price. We can create 
    manage contract for rent and selling of property-house. Based on contract invoice will be created for every month 
    according to the contract duration. This odoo apps allow partial payment for property selling, means we can 
    accept payments in installments. In the configuration we create installment schemes. Once invoice is created 
    invoice due date automatically set based on interval set on contract, and it applies fine after the payment due 
    date.""",

    'author': 'ErpMstar Solutions',
    'category': 'Industry',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['account', 'account_accountant'],
    'external_dependencies': {
        'python': ['qrcode','base64']
    },

    # always loaded
    'data': [
        'security/property_security.xml',
        'security/ir.model.access.csv',
        'views/main_property_views.xml',
        'views/property_views.xml',
        'views/contract_property_views.xml',
        'views/contract_property_views.xml',
        'views/amount_installation_views.xml',
        'views/installment_config_views.xml',
        'views/mail_activity_views.xml',
        'views/res_config_settings_views.xml',
        'views/property_offer_views.xml',
        'data/ir_sequence_data.xml',
        'data/mail_data.xml',
        'wizards/property_search_views.xml',
        'wizards/installment_views.xml',
        'wizards/payment_views.xml',
        'report/property_contract_report_templates.xml',
        'report/installment_receipt_template.xml',
        'report/property_description_brochure_template.xml',
        'report/report_property_actions.xml',
        'data/mail_template_data.xml',
        'views/project.xml',
        'views/invoice.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'real_estate_advertisement/static/src/scss/property_dashboard.scss'
        ]
    },
    # only loaded in demonstration mode
    'demo': [
    ],

    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 251,
    'currency': 'EUR',
}
