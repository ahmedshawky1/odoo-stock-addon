# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockSecurity(models.Model):
    _name = 'stock.security'
    _description = 'Tradeable Security'
    _order = 'symbol'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Basic Information
    symbol = fields.Char(
        string='Symbol',
        required=True,
        index=True,
        tracking=True,
        help='Trading symbol (e.g., AAPL, GOOGL)'
    )
    
    name = fields.Char(
        string='Security Name',
        required=True,
        tracking=True,
        help='Full name of the security'
    )
    
    security_type = fields.Selection([
        ('stock', 'Stock'),
        ('bond', 'Bond'),
        ('mf', 'Mutual Fund')
    ], string='Type', default='stock', required=True, tracking=True)
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Inactive securities cannot be traded'
    )
    
    # Pricing Information
    current_price = fields.Float(
        string='Current Price',
        digits=(16, 4),
        required=True,
        tracking=True,
        help='Current market price'
    )
    
    session_start_price = fields.Float(
        string='Session Start Price',
        digits=(16, 4),
        help='Price at the start of current session'
    )
    
    previous_close = fields.Float(
        string='Previous Close',
        digits=(16, 4),
        help='Closing price from previous session'
    )
    
    ipo_price = fields.Float(
        string='IPO Price',
        digits=(16, 4),
        help='Initial public offering price'
    )
    
    # Trading Rules
    tick_size = fields.Float(
        string='Tick Size',
        default=0.01,
        digits=(16, 4),
        help='Minimum price increment'
    )
    
    lot_size = fields.Integer(
        string='Lot Size',
        default=1,
        help='Minimum trading quantity'
    )
    
    max_order_size = fields.Integer(
        string='Max Order Size',
        help='Maximum quantity per order (0 = unlimited)'
    )
    
    # Relationships
    order_ids = fields.One2many(
        'stock.order',
        'security_id',
        string='Orders'
    )
    
    trade_ids = fields.One2many(
        'stock.trade',
        'security_id',
        string='Trades'
    )
    
    position_ids = fields.One2many(
        'stock.position',
        'security_id',
        string='Positions'
    )
    
    price_history_ids = fields.One2many(
        'stock.price.history',
        'security_id',
        string='Price History'
    )
    
    # Computed Fields
    change_amount = fields.Float(
        string='Change',
        compute='_compute_price_change',
        digits=(16, 4),
        help='Price change from session start'
    )
    
    change_percentage = fields.Float(
        string='Change %',
        compute='_compute_price_change',
        digits=(16, 2),
        help='Percentage change from session start'
    )
    
    volume_today = fields.Integer(
        string='Volume Today',
        compute='_compute_today_stats',
        help='Total shares traded today'
    )
    
    value_today = fields.Float(
        string='Value Today',
        compute='_compute_today_stats',
        digits='Product Price',
        help='Total value traded today'
    )
    
    vwap = fields.Float(
        string='VWAP',
        compute='_compute_today_stats',
        digits=(16, 4),
        help='Volume Weighted Average Price'
    )
    
    bid_count = fields.Integer(
        string='Bid Orders',
        compute='_compute_order_book',
        help='Number of active buy orders'
    )
    
    ask_count = fields.Integer(
        string='Ask Orders',
        compute='_compute_order_book',
        help='Number of active sell orders'
    )
    
    best_bid = fields.Float(
        string='Best Bid',
        compute='_compute_order_book',
        digits=(16, 4),
        help='Highest bid price'
    )
    
    best_ask = fields.Float(
        string='Best Ask',
        compute='_compute_order_book',
        digits=(16, 4),
        help='Lowest ask price'
    )
    
    @api.depends('current_price', 'session_start_price')
    def _compute_price_change(self):
        for security in self:
            if security.session_start_price:
                security.change_amount = security.current_price - security.session_start_price
                security.change_percentage = (security.change_amount / security.session_start_price) * 100
            else:
                security.change_amount = 0.0
                security.change_percentage = 0.0
    
    @api.depends('trade_ids')
    def _compute_today_stats(self):
        for security in self:
            # Get today's trades from active session
            active_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            if active_session:
                today_trades = security.trade_ids.filtered(
                    lambda t: t.session_id == active_session
                )
                
                security.volume_today = sum(today_trades.mapped('quantity'))
                security.value_today = sum(t.quantity * t.price for t in today_trades)
                
                # Calculate VWAP
                if security.volume_today > 0:
                    security.vwap = security.value_today / security.volume_today
                else:
                    security.vwap = security.current_price
            else:
                security.volume_today = 0
                security.value_today = 0.0
                security.vwap = security.current_price
    
    @api.depends('order_ids')
    def _compute_order_book(self):
        for security in self:
            active_orders = security.order_ids.filtered(
                lambda o: o.status in ['pending', 'partial']
            )
            
            bid_orders = active_orders.filtered(lambda o: o.side == 'buy')
            ask_orders = active_orders.filtered(lambda o: o.side == 'sell')
            
            security.bid_count = len(bid_orders)
            security.ask_count = len(ask_orders)
            
            if bid_orders:
                security.best_bid = max(bid_orders.mapped('price'))
            else:
                security.best_bid = 0.0
            
            if ask_orders:
                security.best_ask = min(ask_orders.mapped('price'))
            else:
                security.best_ask = 0.0
    
    @api.constrains('symbol')
    def _check_symbol_unique(self):
        for security in self:
            if self.search_count([('symbol', '=', security.symbol), ('id', '!=', security.id)]) > 0:
                raise ValidationError(f"Symbol '{security.symbol}' already exists.")
    
    @api.constrains('current_price', 'tick_size')
    def _check_price_validity(self):
        for security in self:
            if security.current_price <= 0:
                raise ValidationError("Price must be greater than zero.")
            if security.tick_size <= 0:
                raise ValidationError("Tick size must be greater than zero.")
            
            # Check if price is valid according to tick size
            if security.tick_size > 0:
                remainder = round(security.current_price % security.tick_size, 6)
                if remainder > 0.000001:  # Small tolerance for floating point
                    raise ValidationError(
                        f"Price {security.current_price} is not valid for tick size {security.tick_size}"
                    )
    
    def update_price(self, new_price):
        """Update security price with validation"""
        self.ensure_one()
        
        # Check tick size
        if self.tick_size > 0:
            remainder = round(new_price % self.tick_size, 6)
            if remainder > 0.000001:
                raise ValidationError(
                    f"Price {new_price} is not valid for tick size {self.tick_size}"
                )
        
        # Check circuit breakers
        active_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
        if active_session and self.session_start_price:
            change_pct = abs((new_price - self.session_start_price) / self.session_start_price * 100)
            
            if new_price > self.session_start_price:
                limit = active_session.circuit_breaker_upper
            else:
                limit = active_session.circuit_breaker_lower
            
            if change_pct > limit:
                raise ValidationError(
                    f"Price change exceeds circuit breaker limit of {limit}%"
                )
        
        # Record price history
        self.env['stock.price.history'].create({
            'security_id': self.id,
            'old_price': self.current_price,
            'new_price': new_price,
            'session_id': active_session.id if active_session else False,
        })
        
        # Update price
        self.current_price = new_price
    
    def action_view_order_book(self):
        """View order book for this security"""
        self.ensure_one()
        return {
            'name': f'Order Book - {self.symbol}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.order',
            'view_mode': 'tree,form',
            'domain': [
                ('security_id', '=', self.id),
                ('status', 'in', ['pending', 'partial'])
            ],
            'context': {
                'default_security_id': self.id,
                'search_default_group_by_side': 1
            }
        }
    
    def action_view_trades(self):
        """View recent trades for this security"""
        self.ensure_one()
        return {
            'name': f'Trades - {self.symbol}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.trade',
            'view_mode': 'tree,form',
            'domain': [('security_id', '=', self.id)],
            'context': {'default_security_id': self.id}
        } 