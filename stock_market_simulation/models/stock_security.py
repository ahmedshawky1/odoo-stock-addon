# -*- coding: utf-8 -*-

from decimal import Decimal
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockSecurity(models.Model):
    _name = 'stock.security'
    _description = 'Tradeable Security'
    _order = 'symbol'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'stock.message.mixin']
    
    # Basic Information
    symbol = fields.Char(
        string='Symbol/Reuters Code',
        required=True,
        index=True,
        tracking=True,
        help='Trading symbol or Reuters code (e.g., AAPL, GOOGL)'
    )
    
    name = fields.Char(
        string='Company Name',
        required=True,
        tracking=True,
        help='Full company name'
    )
    
    sector = fields.Selection([
        ('energy', 'Energy'),
        ('financials', 'Financials'), 
        ('health_care', 'Health Care'),
        ('industrials', 'Industrials'),
        ('information_technology', 'Information Technology'),
        ('materials', 'Materials'),
        ('telecommunication_services', 'Telecommunication Services'),
        ('utilities', 'Utilities'),
        ('tourism', 'Tourism'),
        ('chemical', 'Chemical'),
        ('food_beverage', 'Food and Beverage'),
        ('medical_industry', 'Medical Industry'),
        ('real_estate', 'Real Estate'),
        ('media', 'Media'),
        ('construction', 'Construction'),
        ('fin_services', 'Financial Services'),
        ('banking', 'Banking'),
        ('transportation', 'Transportation')
    ], string='Sector', required=True, tracking=True, help='Business sector classification')
    
    logo = fields.Binary(
        string='Company Logo',
        help='Company logo image'
    )
    
    logo_filename = fields.Char(
        string='Logo Filename'
    )
    
    security_type = fields.Selection([
        ('stock', 'Stock'),
        ('bond', 'Bond'),
        ('mf', 'Mutual Fund')
    ], string='Type', default='stock', required=True, tracking=True)
    
    # Stock Status (from User Stories)
    status = fields.Selection([
        ('ipo', 'IPO - Initial Public Offering'),
        ('po', 'PO - Public Offering'), 
        ('trade', 'Trade - Normal Trading'),
        ('hidden', 'Hidden - Not Visible'),
        ('hold_10min', 'Hold 10 Minutes'),
        ('hold_1session', 'Hold 1 Session')
    ], string='Status', default='trade', required=True, tracking=True,
       help='Stock trading status following User Stories specification')
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Inactive securities cannot be traded'
    )
    
    # Legacy IPO Status (for backward compatibility)
    ipo_status = fields.Selection([
        ('ipo', 'IPO - Initial Public Offering'),
        ('po', 'PO - Public Offering'),
        ('trading', 'Trading - Normal Market')
    ], string='IPO Status (Legacy)', compute='_compute_legacy_ipo_status', store=True,
       help='Computed from status field for backward compatibility')
    
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
    
    price_to_compare_with = fields.Float(
        string='Price to Compare With',
        digits=(16, 4),
        help='Reference price for comparison (updated at session start/end)'
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
    
    hidden_price = fields.Float(
        string='Hidden Price',
        digits=(16, 4),
        help='Hidden price used when status is hidden'
    )
    
    # Shares Outstanding
    total_shares = fields.Integer(
        string='Total Shares',
        default=0,
        help='Total shares outstanding or issued. Used for IPO and position limits.'
    )
    
    # IPO/PO tracking
    current_offering_quantity = fields.Integer(
        string='Current Offering Quantity',
        default=0,
        help='Quantity available for current IPO/PO round'
    )
    
    offering_round = fields.Integer(
        string='Offering Round',
        default=1,
        help='Current offering round number (1=IPO, 2+=PO)'
    )
    
    # History of offering prices for tracking
    offering_history = fields.Text(
        string='Offering History',
        help='JSON history of offering rounds, prices, and quantities'
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
                # Don't multiply by 100 since percentage widget handles this automatically
                security.change_percentage = security.change_amount / security.session_start_price
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
    
    @api.depends('status')
    def _compute_legacy_ipo_status(self):
        """Compute legacy ipo_status from new status field for backward compatibility"""
        for security in self:
            if security.status in ['ipo']:
                security.ipo_status = 'ipo'
            elif security.status in ['po']:
                security.ipo_status = 'po'
            else:
                security.ipo_status = 'trading'
    
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
                # Use Decimal for precise validation
                price_decimal = Decimal(str(security.current_price))
                tick_decimal = Decimal(str(security.tick_size))
                remainder = price_decimal % tick_decimal
                if remainder > Decimal('0.000001'):  # Small tolerance
                    raise ValidationError(
                        f"Price {security.current_price} is not valid for tick size {security.tick_size}"
                    )
    
    def update_price(self, new_price):
        """Update security price with validation"""
        self.ensure_one()
        
        # Check tick size
        if self.tick_size > 0:
            # Use Decimal for precise validation
            price_decimal = Decimal(str(new_price))
            tick_decimal = Decimal(str(self.tick_size))
            remainder = price_decimal % tick_decimal
            if remainder > Decimal('0.000001'):
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
            'view_mode': 'list,form',
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
            'view_mode': 'list,form',
            'domain': [('security_id', '=', self.id)],
            'context': {'default_security_id': self.id}
        }
    
    @api.constrains('ipo_status', 'active')
    def _check_ipo_status(self):
        """Validate IPO status and active state consistency"""
        for security in self:
            # IPO/PO securities should typically be inactive until they go to trading
            if security.ipo_status in ['ipo', 'po'] and not hasattr(self.env.context, 'skip_ipo_validation'):
                # This is just a warning, not enforced constraint
                pass
    
    def action_change_to_trading(self):
        """Change IPO/PO security to trading status and activate normal trading"""
        for security in self:
            if security.ipo_status not in ['ipo', 'po']:
                continue
            
            # Process any pending IPO orders first
            if security.ipo_status in ['ipo', 'po']:
                # This will be called by the session end wizard
                security.write({
                    'ipo_status': 'trading',
                    'active': True,
                    'current_price': security.ipo_price or security.current_price,
                    'session_start_price': security.ipo_price or security.current_price
                })
    
    def can_accept_ipo_orders(self):
        """Check if security can accept IPO orders"""
        self.ensure_one()
        return self.ipo_status in ['ipo', 'po']
    
    def can_accept_regular_orders(self):
        """Check if security can accept regular market orders"""
        self.ensure_one()
        return self.ipo_status == 'trading' and self.active
    
    def start_po_round(self, quantity, price):
        """Start a new PO (Public Offering) round for additional shares"""
        self.ensure_one()
        import json
        
        # Record current round in history
        history = []
        if self.offering_history:
            try:
                history = json.loads(self.offering_history)
            except:
                history = []
        
        # Add current round to history
        history.append({
            'round': self.offering_round,
            'status': self.ipo_status,
            'quantity': self.current_offering_quantity,
            'price': self.ipo_price,
            'date': fields.Datetime.now().isoformat()
        })
        
        # Update for new PO round
        self.write({
            'status': 'po',  # Change to PO status (canonical field)
            'offering_round': self.offering_round + 1,
            'current_offering_quantity': quantity,
            'ipo_price': price,  # New PO price
            'offering_history': json.dumps(history)
        })
        
        return True
    
    def get_offering_history(self):
        """Get the offering history as a list"""
        import json
        try:
            return json.loads(self.offering_history) if self.offering_history else []
        except:
            return [] 