# -*- coding: utf-8 -*-
{
    'name': "Customize Login Page - Skan Portal",

    'summary': "Customize Login Page with Egyptian Real Estate Platform Design",

    'description': """
    This module provides a customized login page matching the Egyptian Real Estate Platform (skan portal) design.
    Features include modern UI with Egyptian government color scheme, responsive Bootstrap 5 layout, 
    Font Awesome icons, and Cairo/Roboto fonts for authentic branding consistency.
    
    Key Features:
    - Skan portal design integration with matching navbar and footer
    - Egyptian government color scheme (Red #C62E29)
    - Clean, professional login interface
    - Custom portal user redirect path configuration
    - Portal users can be redirected to custom paths after login instead of default /my
    - Branded reset password functionality with consistent design
    - Responsive forgot password and change password pages
    """,

    'author': "NxonBytes",
    "support": "webdeveloper.inf@gmail.com",
    'category': 'Tools',
    'version': '18.0.1.3.0',
    'license': 'LGPL-3',
    'price': 0,
    'currency': 'USD',
    'installable': True,
    'auto_install': False,
    'application': False,

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_setup', 'web', 'auth_signup', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/login_image.xml',
        'views/assets.xml',
        'views/middle_login_template.xml',
        'views/reset_password_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "images": ["static/description/banner.png"],
}

