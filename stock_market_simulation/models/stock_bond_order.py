# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockBondOrder(models.Model):
    _name = 'stock.bond.order'
    _description = 'Bond Trading Order'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Identity
    name = fields.Char(
        string='Order Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: 'New'
    )
    
    # Core Fields
    user_id = fields.Many2one(
        'res.users', string='Trader',
        required=True, index=True,
        default=lambda self: self.env.user,
        states={'draft': [('readonly', False)]},
        readonly=True,
        tracking=True
    )
    
    # Removed: broker_id related field (default broker functionality removed)
    
    entered_by_id = fields.Many2one(
        'res.users', string='Entered By',
        default=lambda self: self.env.user,
        index=True, readonly=True, tracking=True,
        help='User who placed the order in the portal (usually a broker or admin).'
    )
    
    session_id = fields.Many2one(
        'stock.session', string='Trading Session',
        required=True, index=True,
        domain=[('state', '=', 'open')],
        states={'draft': [('readonly', False)]},
        readonly=True,
        tracking=True
    )
    
    bond_id = fields.Many2one(
        'stock.bond', string='Bond',
        required=True, index=True,
        states={'draft': [('readonly', False)]},
        readonly=True,
        tracking=True
    )
    
    # Order Details
    order_type = fields.Selection([
        ('market', 'Market'),
        ('limit', 'Limit')
    ], string='Order Type', required=True, default='limit', tracking=True,
       states={'draft': [('readonly', False)]}, readonly=True)
    
    side = fields.Selection([
        ('buy', 'Buy'),
        ('sell', 'Sell')
    ], string='Side', required=True, tracking=True,
       states={'draft': [('readonly', False)]}, readonly=True)
    
    # BID/ASK display fields (computed from side for User Stories compatibility)
    order_side_display = fields.Selection([
        ('bid', 'BID'),
        ('ask', 'ASK')
    ], string='Order Type (BID/ASK)', compute='_compute_bid_ask_display', store=True,
       help='BID for buy orders, ASK for sell orders - matching User Stories terminology')
    
    price = fields.Float(
        string='Price',
        digits=(16, 4),
        required=True,
        tracking=True,
        states={'draft': [('readonly', False)]},
        readonly=True
    )
    
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        tracking=True,
        states={'draft': [('readonly', False)]},
        readonly=True
    )
    
    filled_quantity = fields.Integer(
        string='Filled Quantity',
        readonly=True,
        default=0,
        tracking=True
    )
    
    remaining_quantity = fields.Integer(
        string='Remaining Quantity',
        compute='_compute_remaining_quantity',
        store=True
    )
    
    # Status
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('open', 'Open'),
        ('partial', 'Partially Filled'),
        ('filled', 'Filled'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired')
    ], string='Status', default='draft', required=True, tracking=True, index=True)
    
    # Financial Information
    order_value = fields.Float(
        string='Order Value',
        compute='_compute_order_value',
        digits='Product Price',
        store=True
    )
    
    filled_value = fields.Float(
        string='Filled Value',
        compute='_compute_filled_value',
        digits='Product Price'
    )
    
    broker_commission_rate = fields.Float(
        string='Commission Rate (%)',
        related='session_id.broker_commission_rate',
        store=True
    )
    
    broker_commission = fields.Float(
        string='Broker Commission',
        compute='_compute_broker_commission',
        digits='Product Price',
        store=True
    )
    
    # Relationships
    trade_ids = fields.One2many(
        'stock.bond.trade',
        compute='_compute_trades',
        string='Trades'
    )
    
    # Additional Information
    description = fields.Text(
        string='Description',
        readonly=True
    )
    
    rejection_reason = fields.Text(
        string='Rejection Reason',
        readonly=True
    )
    
    @api.depends('quantity', 'filled_quantity')
    def _compute_remaining_quantity(self):
        for order in self:
            order.remaining_quantity = order.quantity - order.filled_quantity
    
    @api.depends('quantity', 'price')
    def _compute_order_value(self):
        for order in self:
            order.order_value = order.quantity * order.price
    
    @api.depends('filled_quantity', 'trade_ids')
    def _compute_filled_value(self):
        for order in self:
            order.filled_value = sum(
                trade.quantity * trade.price 
                for trade in order.trade_ids
            )
    
    @api.depends('filled_value', 'broker_commission_rate')
    def _compute_broker_commission(self):
        for order in self:
            order.broker_commission = order.filled_value * order.broker_commission_rate / 100
    
    @api.depends('side')
    def _compute_bid_ask_display(self):
        """Compute BID/ASK display fields from buy/sell side"""
        for order in self:
            if order.side == 'buy':
                order.order_side_display = 'bid'
            elif order.side == 'sell':
                order.order_side_display = 'ask'
            else:
                order.order_side_display = False
    
    def _compute_trades(self):
        for order in self:
            if order.side == 'buy':
                order.trade_ids = self.env['stock.bond.trade'].search([
                    ('buy_order_id', '=', order.id)
                ])
            else:
                order.trade_ids = self.env['stock.bond.trade'].search([
                    ('sell_order_id', '=', order.id)
                ])
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.bond.order') or 'New'
        
        order = super(StockBondOrder, self).create(vals)
        return order
    
    def action_submit(self):
        """Submit order for processing"""
        self.ensure_one()
        if self.status == 'draft':
            self._validate_order()
            self.status = 'submitted'
            self.message_post(body="Bond order submitted for processing")
    
    def action_cancel(self):
        """Cancel the order"""
        self.ensure_one()
        if self.status in ['draft', 'submitted', 'open', 'partial']:
            self.status = 'cancelled'
            self.message_post(body="Bond order cancelled")
    
    def _validate_order(self):
        """Validate order before submission"""
        self.ensure_one()
        
        # Check if bond is tradeable
        if not self.bond_id.is_active:
            raise ValidationError(f"Bond {self.bond_id.symbol} is not currently tradeable.")
        
        # Check user cash balance for buy orders
        if self.side == 'buy':
            required_cash = self.quantity * self.price
            if self.user_id.cash_balance < required_cash:
                raise ValidationError(
                    f"Insufficient funds. Required: ${required_cash:,.2f}, "
                    f"Available: ${self.user_id.cash_balance:,.2f}"
                )
        
        # Check user bond holdings for sell orders
        if self.side == 'sell':
            position = self.env['stock.bond.position'].search([
                ('user_id', '=', self.user_id.id),
                ('bond_id', '=', self.bond_id.id)
            ], limit=1)
            
            available_quantity = position.quantity if position else 0
            if available_quantity < self.quantity:
                raise ValidationError(
                    f"Insufficient bonds. Required: {self.quantity:,}, "
                    f"Available: {available_quantity:,}"
                )


class StockBondTrade(models.Model):
    _name = 'stock.bond.trade'
    _description = 'Bond Trade Execution'
    _order = 'trade_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Identity
    name = fields.Char(
        string='Trade Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('stock.bond.trade') or 'New'
    )
    
    # Orders
    buy_order_id = fields.Many2one(
        'stock.bond.order',
        string='Buy Order',
        required=True,
        readonly=True,
        ondelete='restrict',
        index=True
    )
    
    sell_order_id = fields.Many2one(
        'stock.bond.order',
        string='Sell Order',
        required=True,
        readonly=True,
        ondelete='restrict',
        index=True
    )
    
    # Parties
    buyer_id = fields.Many2one(
        'res.users',
        string='Buyer',
        related='buy_order_id.user_id',
        store=True,
        readonly=True
    )
    
    seller_id = fields.Many2one(
        'res.users',
        string='Seller',
        related='sell_order_id.user_id',
        store=True,
        readonly=True
    )
    
    # Bond and Session
    bond_id = fields.Many2one(
        'stock.bond',
        string='Bond',
        related='buy_order_id.bond_id',
        store=True,
        readonly=True,
        index=True
    )
    
    session_id = fields.Many2one(
        'stock.session',
        string='Trading Session',
        required=True,
        readonly=True,
        ondelete='restrict',
        index=True
    )
    
    # Trade Details
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        readonly=True
    )
    
    price = fields.Float(
        string='Trade Price',
        digits=(16, 4),
        required=True,
        readonly=True
    )
    
    trade_value = fields.Float(
        string='Trade Value',
        compute='_compute_trade_value',
        digits='Product Price',
        store=True
    )
    
    trade_date = fields.Datetime(
        string='Trade Date',
        default=fields.Datetime.now,
        readonly=True
    )
    
    @api.depends('quantity', 'price')
    def _compute_trade_value(self):
        for trade in self:
            trade.trade_value = trade.quantity * trade.price


class StockBondPosition(models.Model):
    _name = 'stock.bond.position'
    _description = 'Bond Position'
    _order = 'user_id, bond_id'
    
    # Unique constraint on user + bond
    _sql_constraints = [
        ('user_bond_unique', 
         'UNIQUE(user_id, bond_id)',
         'A user can only have one position per bond.')
    ]
    
    # Relationships
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    bond_id = fields.Many2one(
        'stock.bond',
        string='Bond',
        required=True,
        ondelete='restrict',
        index=True
    )
    
    # Position Details
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        default=0,
        help='Number of bonds held'
    )
    
    average_price = fields.Float(
        string='Average Price',
        digits=(16, 4),
        default=0.0,
        help='Volume-weighted average purchase price'
    )
    
    total_cost = fields.Float(
        string='Total Cost',
        digits='Product Price',
        default=0.0,
        help='Total amount invested'
    )
    
    # Computed Fields
    current_value = fields.Float(
        string='Current Value',
        compute='_compute_current_value',
        digits='Product Price',
        help='Current market value'
    )
    
    unrealized_pnl = fields.Float(
        string='Unrealized P&L',
        compute='_compute_pnl',
        digits='Product Price',
        help='Unrealized profit/loss'
    )
    
    unrealized_pnl_percent = fields.Float(
        string='Unrealized P&L %',
        compute='_compute_pnl',
        digits=(5, 2),
        help='Unrealized profit/loss percentage'
    )
    
    @api.depends('quantity', 'bond_id.current_price')
    def _compute_current_value(self):
        for position in self:
            position.current_value = position.quantity * position.bond_id.current_price
    
    @api.depends('current_value', 'total_cost')
    def _compute_pnl(self):
        for position in self:
            position.unrealized_pnl = position.current_value - position.total_cost
            
            if position.total_cost > 0:
                position.unrealized_pnl_percent = (position.unrealized_pnl / position.total_cost) * 100
            else:
                position.unrealized_pnl_percent = 0.0
    
    def update_position(self, quantity_change, price, is_buy=True):
        """Update position when bonds are bought or sold"""
        self.ensure_one()
        
        if is_buy:
            # Buying bonds - add to position
            new_total_cost = self.total_cost + (quantity_change * price)
            new_quantity = self.quantity + quantity_change
            
            if new_quantity > 0:
                self.average_price = new_total_cost / new_quantity
            else:
                self.average_price = 0.0
                
            self.quantity = new_quantity
            self.total_cost = new_total_cost
        else:
            # Selling bonds - reduce position
            if quantity_change > self.quantity:
                raise ValidationError(f"Cannot sell {quantity_change} bonds, only {self.quantity} available")
            
            # Reduce position proportionally
            if self.quantity > 0:
                cost_per_bond = self.total_cost / self.quantity
                cost_reduction = quantity_change * cost_per_bond
                self.total_cost -= cost_reduction
                self.quantity -= quantity_change
                
                # Average price stays the same when selling
            
            # If position becomes zero, reset average price
            if self.quantity == 0:
                self.average_price = 0.0
                self.total_cost = 0.0