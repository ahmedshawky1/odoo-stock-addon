# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockConfig(models.Model):
    _name = 'stock.config'
    _description = 'Stock Market Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'company_id'
    
    company_id = fields.Many2one(
        'res.company', string='Company',
        required=True, default=lambda self: self.env.company
    )
    
    # Trading Configuration
    currency_symbol = fields.Char(
        string='Currency Symbol',
        default='$',
        help="Currency symbol to display in the interface"
    )
    
    settlement_days = fields.Integer(
        string='Settlement Days (T+)',
        default=2,
        help="Number of days for trade settlement (T+2 means 2 business days after trade)"
    )
    
    price_decimal_places = fields.Integer(
        string='Price Decimal Places',
        default=2,
        help="Number of decimal places for prices"
    )
    
    # Margin Configuration
    margin_call_threshold = fields.Float(
        string='Margin Call Threshold (%)',
        default=70.0,
        help="Percentage of collateral value that triggers margin call"
    )
    
    margin_call_grace_period = fields.Integer(
        string='Margin Call Grace Period (hours)',
        default=24,
        help="Hours given to respond to margin call before liquidation"
    )
    
    # Loan Configuration
    default_penalty_rate = fields.Float(
        string='Daily Default Penalty Rate (%)',
        default=0.1,
        help="Daily penalty rate for overdue loans"
    )
    
    loan_default_days = fields.Integer(
        string='Loan Default Days',
        default=30,
        help="Days overdue before loan is marked as defaulted"
    )
    
    # Interest Rates
    savings_interest_rate = fields.Float(
        string='Savings Interest Rate (%)',
        default=1.5,
        help="Annual interest rate for savings deposits"
    )
    
    fixed_deposit_base_rate = fields.Float(
        string='Fixed Deposit Base Rate (%)',
        default=3.0,
        help="Base annual interest rate for fixed deposits"
    )
    
    # Trading Limits
    min_order_value = fields.Float(
        string='Minimum Order Value',
        default=100.0,
        help="Minimum value for any order"
    )
    
    daily_trading_limit = fields.Float(
        string='Daily Trading Limit',
        default=1000000.0,
        help="Maximum daily trading value per user"
    )
    
    position_limit_percent = fields.Float(
        string='Position Limit (%)',
        default=10.0,
        help="Maximum percentage of security that one user can hold"
    )
    
    # Price Movement
    price_update_threshold = fields.Float(
        string='Price Update Volume Threshold',
        default=1000.0,
        help="Minimum trade volume required to update security price"
    )
    
    max_price_change_percent = fields.Float(
        string='Max Price Change (%)',
        default=10.0,
        help="Maximum allowed price change in a single session"
    )
    
    # Additional Configuration Fields
    max_order_value = fields.Float(
        string='Maximum Order Value',
        default=1000000.0,
        help="Maximum value for any single order"
    )
    
    max_leverage_ratio = fields.Float(
        string='Maximum Leverage Ratio',
        default=3.0,
        help="Maximum leverage allowed for margin trading"
    )
    
    trading_halt_threshold = fields.Float(
        string='Trading Halt Threshold (%)',
        default=15.0,
        help="Price movement percentage that triggers trading halt"
    )
    
    position_limit_per_security = fields.Integer(
        string='Position Limit Per Security',
        default=10000,
        help="Maximum number of shares per security per user"
    )
    
    # Commission Configuration
    default_broker_commission = fields.Float(
        string='Default Broker Commission (%)',
        default=0.5,
        help="Default commission rate for brokers"
    )
    
    # System Behavior
    auto_execute_margin_calls = fields.Boolean(
        string='Auto Execute Margin Calls',
        default=True,
        help="Automatically liquidate positions on margin calls"
    )
    
    enable_after_hours_trading = fields.Boolean(
        string='Enable After Hours Trading',
        default=False,
        help="Allow trading outside session hours"
    )
    
    require_broker_approval = fields.Boolean(
        string='Require Broker Approval',
        default=False,
        help="Require broker approval for large orders"
    )
    
    large_order_threshold = fields.Float(
        string='Large Order Threshold',
        default=100000.0,
        help="Order value that requires broker approval"
    )
    
    # Risk Management
    circuit_breaker_enabled = fields.Boolean(
        string='Enable Circuit Breakers',
        default=True,
        help="Enable automatic trading halts on price movements"
    )
    
    volatility_threshold = fields.Float(
        string='Volatility Threshold (%)',
        default=20.0,
        help="Volatility percentage that triggers risk alerts"
    )
    
    # Notifications
    send_margin_call_notifications = fields.Boolean(
        string='Send Margin Call Notifications',
        default=True,
        help="Send email notifications for margin calls"
    )
    
    send_trade_confirmations = fields.Boolean(
        string='Send Trade Confirmations',
        default=True,
        help="Send email confirmations for trades"
    )
    
    _sql_constraints = [
        ('company_uniq', 'unique (company_id)', 'Only one configuration per company allowed!'),
        ('settlement_days_positive', 'CHECK (settlement_days > 0)', 'Settlement days must be positive!'),
        ('margin_call_threshold_valid', 'CHECK (margin_call_threshold > 0 AND margin_call_threshold < 100)', 
         'Margin call threshold must be between 0 and 100!'),
    ]
    
    @api.model
    def get_config(self):
        """Get configuration for current company"""
        config = self.search([('company_id', '=', self.env.company.id)], limit=1)
        if not config:
            # Create default configuration if none exists
            config = self.create({
                'company_id': self.env.company.id
            })
        return config
    
    @api.constrains('default_penalty_rate', 'loan_default_days', 'min_order_value')
    def _check_values(self):
        for config in self:
            if config.default_penalty_rate < 0:
                raise ValidationError("Default penalty rate cannot be negative.")
            if config.loan_default_days <= 0:
                raise ValidationError("Loan default days must be positive.")
            if config.min_order_value < 0:
                raise ValidationError("Minimum order value cannot be negative.") 