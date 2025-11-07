# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class StockBond(models.Model):
    _name = 'stock.bond'
    _description = 'Tradeable Bonds'
    _order = 'symbol'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Basic Information (from User Stories bonds table)
    symbol = fields.Char(
        string='Reuters Code',
        required=True,
        index=True,
        tracking=True,
        help='Bond Reuters code identifier'
    )
    
    name = fields.Char(
        string='Company Name',
        required=True,
        tracking=True,
        help='Bond issuer company name'
    )
    
    sector = fields.Char(
        string='Sector',
        required=True,
        help='Business sector of the bond issuer'
    )
    
    # Bond Status (from User Stories)
    status = fields.Selection([
        ('ipo', 'IPO'),
        ('po', 'PO'),
        ('trade', 'Trade'),
        ('hidden', 'Hidden')
    ], string='Status', default='trade', required=True, tracking=True)
    
    # Pricing Information
    ipo_price = fields.Float(
        string='IPO Price',
        digits=(16, 4),
        required=True,
        help='Initial public offering price'
    )
    
    current_price = fields.Float(
        string='Current Price',
        digits=(16, 4),
        required=True,
        tracking=True,
        help='Current market price'
    )
    
    hidden_price = fields.Float(
        string='Hidden Price',
        digits=(16, 4),
        help='Hidden price when status is hidden'
    )
    
    price_to_compare_with = fields.Float(
        string='Price to Compare With',
        digits=(16, 4),
        help='Reference price for comparison'
    )
    
    session_start_price = fields.Float(
        string='Session Start Price',
        digits=(16, 4),
        help='Price at start of current session'
    )
    
    # Bond Characteristics
    quantity = fields.Integer(
        string='Available Quantity',
        required=True,
        default=0,
        help='Total quantity available for trading'
    )
    
    start_session = fields.Integer(
        string='Start Session',
        required=True,
        help='Session when bond becomes available for trading'
    )
    
    end_session = fields.Integer(
        string='End Session',
        required=True,
        help='Session when bond matures/expires'
    )
    
    # Bond Types (from User Stories)
    bond_type = fields.Selection([
        ('conventional', 'Conventional Bond'),
        ('amortizing', 'Amortizing Bond')
    ], string='Bond Type', required=True, default='conventional')
    
    rate_type = fields.Selection([
        ('conventional', 'Conventional Bond'),
        ('zero_coupon', 'Zero Coupon Bond (Discount)'),
        ('accrual', 'Accrual Bond'),
        ('deferred_coupon', 'Deferred Coupon Bond'),
        ('step_up_coupon', 'Step-up Coupon Bond'),
        ('advanced_coupon', 'Advanced Coupon Bond')
    ], string='Rate Type', required=True, default='conventional')
    
    # Financial Terms
    return_price = fields.Float(
        string='Return Price',
        digits=(16, 4),
        required=True,
        help='Maturity value/face value of the bond'
    )
    
    percentage_rate_session = fields.Float(
        string='Percentage Rate per Session',
        digits=(5, 3),
        required=True,
        help='Interest rate per session (percentage)'
    )
    
    first_pay_session = fields.Integer(
        string='First Payment Session',
        required=True,
        help='Session when first interest payment is due'
    )
    
    compensation_rate = fields.Float(
        string='Compensation Rate',
        digits=(5, 3),
        required=True,
        help='Compensation rate for the bond'
    )
    
    final_rate_session = fields.Integer(
        string='Final Rate Session',
        help='Session for final rate calculation'
    )
    
    step_percentage = fields.Float(
        string='Step Percentage',
        digits=(5, 3),
        help='Step percentage for step-up bonds'
    )
    
    # Computed Fields
    time_to_maturity = fields.Integer(
        string='Sessions to Maturity',
        compute='_compute_time_to_maturity',
        help='Number of sessions until maturity'
    )
    
    current_yield = fields.Float(
        string='Current Yield (%)',
        compute='_compute_yield',
        digits=(5, 3),
        help='Current yield based on current price'
    )
    
    ytm = fields.Float(
        string='Yield to Maturity (%)',
        compute='_compute_yield',
        digits=(5, 3),
        help='Yield to maturity calculation'
    )
    
    is_active = fields.Boolean(
        string='Is Active',
        compute='_compute_is_active',
        help='True if bond is currently tradeable'
    )
    
    accrued_interest = fields.Float(
        string='Accrued Interest',
        compute='_compute_accrued_interest',
        digits=(16, 4),
        help='Accrued interest to date'
    )
    
    # Relationships
    order_ids = fields.One2many(
        'stock.bond.order',
        'bond_id',
        string='Orders'
    )
    
    trade_ids = fields.One2many(
        'stock.bond.trade',
        'bond_id',
        string='Trades'
    )
    
    position_ids = fields.One2many(
        'stock.bond.position',
        'bond_id',
        string='Positions'
    )
    
    # Order Book Information
    bid_count = fields.Integer(
        string='Bid Orders',
        compute='_compute_order_book'
    )
    
    ask_count = fields.Integer(
        string='Ask Orders',
        compute='_compute_order_book'
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
    
    @api.depends('start_session', 'end_session')
    def _compute_is_active(self):
        for bond in self:
            current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            if current_session:
                session_num = 0
                if current_session.name.startswith('Session '):
                    try:
                        session_num = int(current_session.name.split(' ')[-1])
                    except:
                        session_num = 0
                
                bond.is_active = (bond.start_session <= session_num <= bond.end_session and 
                                bond.status == 'trade')
            else:
                bond.is_active = False
    
    @api.depends('end_session')
    def _compute_time_to_maturity(self):
        for bond in self:
            current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            if current_session:
                session_num = 0
                if current_session.name.startswith('Session '):
                    try:
                        session_num = int(current_session.name.split(' ')[-1])
                    except:
                        session_num = 0
                
                bond.time_to_maturity = max(0, bond.end_session - session_num)
            else:
                bond.time_to_maturity = bond.end_session - bond.start_session
    
    @api.depends('current_price', 'return_price', 'percentage_rate_session', 'time_to_maturity')
    def _compute_yield(self):
        for bond in self:
            if bond.current_price > 0:
                # Current Yield = (Annual Interest / Current Price) * 100
                annual_interest = bond.return_price * (bond.percentage_rate_session / 100)
                bond.current_yield = (annual_interest / bond.current_price) * 100
                
                # Simple YTM approximation
                if bond.time_to_maturity > 0:
                    total_return = bond.return_price - bond.current_price
                    annual_return = total_return / bond.time_to_maturity
                    bond.ytm = ((annual_interest + annual_return) / bond.current_price) * 100
                else:
                    bond.ytm = bond.current_yield
            else:
                bond.current_yield = 0.0
                bond.ytm = 0.0
    
    @api.depends('first_pay_session', 'percentage_rate_session')
    def _compute_accrued_interest(self):
        for bond in self:
            current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            if current_session:
                session_num = 0
                if current_session.name.startswith('Session '):
                    try:
                        session_num = int(current_session.name.split(' ')[-1])
                    except:
                        session_num = 0
                
                if session_num >= bond.first_pay_session:
                    sessions_since_first = session_num - bond.first_pay_session
                    bond.accrued_interest = (bond.return_price * 
                                           (bond.percentage_rate_session / 100) * 
                                           sessions_since_first)
                else:
                    bond.accrued_interest = 0.0
            else:
                bond.accrued_interest = 0.0
    
    @api.depends('order_ids')
    def _compute_order_book(self):
        for bond in self:
            active_orders = bond.order_ids.filtered(
                lambda o: o.status in ['open', 'partial']
            )
            
            bid_orders = active_orders.filtered(lambda o: o.side == 'buy')
            ask_orders = active_orders.filtered(lambda o: o.side == 'sell')
            
            bond.bid_count = len(bid_orders)
            bond.ask_count = len(ask_orders)
            
            if bid_orders:
                bond.best_bid = max(bid_orders.mapped('price'))
            else:
                bond.best_bid = 0.0
            
            if ask_orders:
                bond.best_ask = min(ask_orders.mapped('price'))
            else:
                bond.best_ask = 0.0
    
    @api.constrains('symbol')
    def _check_symbol_unique(self):
        for bond in self:
            if self.search_count([('symbol', '=', bond.symbol), ('id', '!=', bond.id)]) > 0:
                raise ValidationError(f"Bond symbol '{bond.symbol}' already exists.")
    
    @api.constrains('start_session', 'end_session')
    def _check_session_dates(self):
        for bond in self:
            if bond.start_session >= bond.end_session:
                raise ValidationError("Start session must be before end session.")
    
    @api.constrains('first_pay_session', 'start_session', 'end_session')
    def _check_payment_session(self):
        for bond in self:
            if bond.first_pay_session < bond.start_session:
                raise ValidationError("First payment session cannot be before start session.")
            if bond.first_pay_session > bond.end_session:
                raise ValidationError("First payment session cannot be after end session.")
    
    def calculate_bond_price_by_time(self, target_session=None):
        """Calculate bond price based on time to maturity"""
        self.ensure_one()
        
        if target_session is None:
            current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            if current_session and current_session.name.startswith('Session '):
                try:
                    target_session = int(current_session.name.split(' ')[-1])
                except:
                    target_session = self.start_session
            else:
                target_session = self.start_session
        
        sessions_to_maturity = max(0, self.end_session - target_session)
        
        if sessions_to_maturity == 0:
            # Bond has matured, return face value
            return self.return_price
        
        # Time-based pricing calculation based on bond type
        if self.rate_type == 'zero_coupon':
            # Zero coupon bond - discount from face value
            discount_rate = self.percentage_rate_session / 100
            present_value = self.return_price / ((1 + discount_rate) ** sessions_to_maturity)
            return present_value
        else:
            # For other bond types, return current price adjusted for time
            # This is a simplified calculation - could be enhanced
            time_factor = sessions_to_maturity / (self.end_session - self.start_session)
            price_adjustment = (self.return_price - self.ipo_price) * (1 - time_factor)
            return self.ipo_price + price_adjustment
    
    def calculate_interest_payment(self, session_number):
        """Calculate interest payment for a specific session"""
        self.ensure_one()
        
        if session_number < self.first_pay_session or session_number > self.end_session:
            return 0.0
        
        if self.rate_type == 'zero_coupon':
            # Zero coupon bonds don't pay periodic interest
            return 0.0
        elif self.rate_type == 'step_up_coupon':
            # Step-up bonds increase interest over time
            sessions_since_first = session_number - self.first_pay_session
            step_multiplier = 1 + (self.step_percentage / 100) * sessions_since_first
            base_interest = self.return_price * (self.percentage_rate_session / 100)
            return base_interest * step_multiplier
        else:
            # Standard interest calculation
            return self.return_price * (self.percentage_rate_session / 100)
    
    def action_mature_bond(self):
        """Process bond maturity - pay final amount to holders"""
        self.ensure_one()
        
        current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
        if not current_session:
            raise ValidationError("No active session to process bond maturity.")
        
        session_num = 0
        if current_session.name.startswith('Session '):
            try:
                session_num = int(current_session.name.split(' ')[-1])
            except:
                session_num = 0
        
        if session_num < self.end_session:
            raise ValidationError("Bond has not yet reached maturity.")
        
        # Get all current bond holders
        positions = self.env['stock.bond.position'].search([
            ('bond_id', '=', self.id),
            ('quantity', '>', 0)
        ])
        
        total_payout = 0.0
        for position in positions:
            # Calculate final payout (face value + any final interest)
            payout_per_bond = self.return_price
            if self.rate_type != 'zero_coupon':
                final_interest = self.calculate_interest_payment(session_num)
                payout_per_bond += final_interest
            
            total_payout_for_position = payout_per_bond * position.quantity
            
            # Credit the user's cash account
            position.user_id.cash_balance += total_payout_for_position
            
            # Clear the position
            position.quantity = 0
            
            total_payout += total_payout_for_position
            
            # Log the maturity
            position.user_id.message_post(
                body=f"Bond {self.symbol} matured. Received ${total_payout_for_position:,.2f} "
                     f"for {position.quantity} bonds at ${payout_per_bond:.2f} per bond.",
                message_type='notification'
            )
        
        # Update bond status
        self.status = 'hidden'
        
        self.message_post(
            body=f"Bond matured in session {session_num}. "
                 f"Total payout: ${total_payout:,.2f} to {len(positions)} holders.",
            message_type='notification'
        )
        
        _logger.info(f"Bond {self.symbol} matured with total payout ${total_payout:,.2f}")
        
        return total_payout