# -*- coding: utf-8 -*-
{
    'name': 'Stock Market Trading Simulator',
    'version': '1.0',
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
        
        # Views - Backend
        'views/menu_views.xml',
        'views/res_users_views.xml',
        'views/stock_session_views.xml',
        'views/stock_security_views.xml',
        'views/stock_order_views.xml',
        'views/stock_trade_views.xml',
        'views/stock_position_views.xml',
        'views/stock_deposit_views.xml',
        'views/stock_loan_views.xml',
        'views/stock_price_history_views.xml',
        'views/stock_config_views.xml',
        
        # Views - Portal
        'views/portal_templates.xml',
        
        # Reports
        'report/investor_report_templates.xml',
        
        # Main views file (if exists)
        'views/views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'stock/views/portal_templates.xml',
        ],
    },
    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}