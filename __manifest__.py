# -*- coding: utf-8 -*-
{
    'name': 'Stock Market Trading Simulator',
    'version': '1.0.3',
    'category': 'Trading',
    'summary': 'Complete stock market trading simulation with order matching, settlement, and reporting',
    'description': """
Stock Market Trading Simulator
==============================

This module provides a complete stock market trading simulation including:

Features:
---------
* Trading Sessions Management
* Security Management (Stocks, Bonds, Mutual Funds)
* Order Management with Price-Time Priority Matching
* Real-time Trade Execution and Settlement
* Portfolio Tracking with P&L Calculations
* Banking Features (Deposits and Loans)
* Commission Management for Brokers
* Role-based Access Control
* Portal Access for Investors, Brokers, and Bankers
* Comprehensive Reporting
* Price History and Market Data
* Circuit Breakers and Risk Management

User Roles:
-----------
* Investors: Place orders, view portfolio, manage deposits/loans
* Brokers: View client orders, earn commissions
* Bankers: Manage deposits and loans
* Administrators: Manage sessions, securities, and users

Technical Features:
------------------
* Automated matching engine
* Real-time position updates
* Concurrent order processing
* Audit trail for all transactions
* Performance optimized for large volumes
    """,
    'author': 'Stock Market Simulator Team',
    'website': 'https://www.example.com',
    'depends': ['base', 'portal', 'web'],
    'data': [
        # Security
        'security/stock_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/ir_sequence_data.xml',
        'data/stock_data.xml',
        'data/cron.xml',
        'data/fix_emails_data.xml',
        'data/fix_partner_emails_data.xml',
        
        # Views - Backend  
        'views/res_users_views.xml',
        'views/stock_trade_views.xml',
        'views/stock_order_views.xml',
        'views/stock_security_views.xml',
        'views/stock_session_views.xml',
        'views/stock_position_views.xml',
        'views/stock_deposit_views.xml',
        'views/stock_loan_views.xml',
        'views/stock_price_history_views.xml',
        'views/stock_new_models_views.xml',
        'views/stock_transaction_log_views.xml',
        'views/menu_views.xml',
        'views/stock_config_views.xml',
        
        # Views - Portal
        'views/portal_templates.xml',
        
        # Wizards
        'wizard/session_end_ipo_wizard_views.xml',
        
        # Reports
        'report/investor_report_templates.xml',
        
        # Main views file (if exists)
        'views/views.xml',
    ],
    'demo': [
        'demo/demo.xml',
        'demo/new_models_demo.xml',
    ],
    # QWeb templates are provided via 'data' (views). Do not include full view XML in asset bundles,
    # it can cause the web client ModuleLoader to attempt to fetch large XML files and fail.
    'assets': {
        # Portal Assets - CSS and JavaScript for enhanced UI
        'web.assets_frontend': [
            'stock_market_simulation/static/src/scss/stock_portal.scss',
            'stock_market_simulation/static/src/js/stock_portal.js',
        ],
        # Small JS fallback loaded early to recover the login form if the Owl component doesn't mount
        'web.assets_frontend_minimal': [
            'stock_market_simulation/static/src/js/login_fallback.js',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}