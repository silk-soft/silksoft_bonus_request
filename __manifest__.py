# -*- coding: utf-8 -*-

# noinspection PyStatementEffect
{
    'name': 'SilkSoft Bonus Request',
    'version': '15.0.1.0001',
    'category': 'Employee',
    'sequence': 101,
    'summary': 'Module to handle bonus requests for employees ',
    'description': """Module to handle bonus requests for employees""",
    'website': 'https://silksoft.org',
    'author': 'SilkSoft Inc',
    'license': 'AGPL-3',
    'depends': ['hr', 'hr_attendance', 'hr_payroll_community',
                'mail', 'account', "om_account_asset", "resource", "ss_modification_requests", "project", "sale"],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_employee.xml',
        'views/hr_contract.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
