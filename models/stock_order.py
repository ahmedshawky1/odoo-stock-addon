# -*- coding: utf-8 -*-

from decimal import Decimal
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class StockOrder(models.Model):
    _name = 'stock.order'
    _description = 'Stock Trading Order'
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
        domain=[('share', '=', False)],
        default=lambda self: self.env.user,
        readonly="status != 'draft'",
        tracking=True
    )
    
    broker_id = fields.Many2one(
        'res.users', string='Broker',
        related='user_id.broker_id',
        store=True, index=True,
        readonly=True
    )
    
    # Who entered/created the order (broker/admin). This differs from broker_id (investor's default broker).
    entered_by_id = fields.Many2one(
        'res.users', string='Entered By',
        index=True, readonly=True, tracking=True,
        help='User who placed the order in the portal (usually a broker or admin).'
    )
    
    session_id = fields.Many2one(
        'stock.session', string='Trading Session',
        required=True, index=True,
        domain=[('state', '=', 'open')],
        readonly="status != 'draft'",
        tracking=True
    )
    
    security_id = fields.Many2one(
        'stock.security', string='Security',
        required=True, index=True,
        readonly="status != 'draft'",
        tracking=True
    )
    
    # Order Details
    order_type = fields.Selection([
        ('market', 'Market'),
        ('limit', 'Limit'),
        ('stop_loss', 'Stop Loss'),
        ('stop_limit', 'Stop Limit'),
    ], string='Order Type', required=True, default='limit', tracking=True,
       readonly="status != 'draft'")
    
    time_in_force = fields.Selection([
        ('day', 'Day'),
        ('gtc', 'Good Till Cancelled'),
        ('ioc', 'Immediate or Cancel'),
        ('fok', 'Fill or Kill'),
    ], string='Time in Force', default='day', tracking=True,
       readonly="status != 'draft'")
    
    stop_price = fields.Float(
        string='Stop Price', 
        digits='Product Price',
        help="For stop orders: the price at which the order becomes active",
        readonly="status != 'draft'"
    )
    
    side = fields.Selection([
        ('buy', 'Buy'),
        ('sell', 'Sell')
    ], string='Side', required=True, tracking=True,
       readonly="status != 'draft'")
    
    price = fields.Float(
        string='Price',
        digits=(16, 4),
        required=True,
        tracking=True,
        readonly="status != 'draft'"
    )
    
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        tracking=True,
        readonly="status != 'draft'"
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
        'stock.trade',
        compute='_compute_trades',
        string='Trades'
    )
    
    # Timestamps
    order_date = fields.Datetime(
        string='Order Date',
        default=fields.Datetime.now,
        readonly=True,
        tracking=True
    )
    
    expiry_date = fields.Datetime(
        string='Expiry Date',
        help='Order expires at session end if not specified'
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
    
    def _compute_trades(self):
        for order in self:
            if order.side == 'buy':
                order.trade_ids = self.env['stock.trade'].search([
                    ('buy_order_id', '=', order.id)
                ])
            else:
                order.trade_ids = self.env['stock.trade'].search([
                    ('sell_order_id', '=', order.id)
                ])
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.order') or 'New'
        
        # Set market order price
        if vals.get('order_type') == 'market':
            security = self.env['stock.security'].browse(vals.get('security_id'))
            if vals.get('side') == 'buy':
                # For market buy, use a high price to ensure execution
                vals['price'] = security.current_price * 1.1
            else:
                # For market sell, use a low price to ensure execution
                vals['price'] = security.current_price * 0.9
        
        # Ensure the entered_by_id is set to the current env user if not provided
        if not vals.get('entered_by_id'):
            vals['entered_by_id'] = self.env.user.id
        
        return super().create(vals)
    
    @api.constrains('quantity', 'security_id')
    def _check_quantity(self):
        for order in self:
            if order.quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")
            
            # Check lot size
            if order.security_id.lot_size > 0:
                if order.quantity % order.security_id.lot_size != 0:
                    raise ValidationError(
                        f"Quantity must be a multiple of lot size ({order.security_id.lot_size})"
                    )
            
            # Check max order size
            if order.security_id.max_order_size > 0:
                if order.quantity > order.security_id.max_order_size:
                    raise ValidationError(
                        f"Quantity exceeds maximum order size ({order.security_id.max_order_size})"
                    )
    
    @api.constrains('price', 'security_id', 'order_type', 'stop_price')
    def _check_price(self):
        for order in self:
            if order.order_type in ['limit', 'stop_limit']:
                if order.price <= 0:
                    raise ValidationError("Price must be greater than zero.")
                
                # Check tick size
                if order.security_id.tick_size > 0:
                    # Use Decimal for precise validation
                    price_decimal = Decimal(str(order.price))
                    tick_decimal = Decimal(str(order.security_id.tick_size))
                    remainder = price_decimal % tick_decimal
                    if remainder > Decimal('0.000001'):
                        raise ValidationError(
                            f"Price must be a multiple of tick size ({order.security_id.tick_size})"
                        )
            
            # Validate stop price for stop orders
            if order.order_type in ['stop_loss', 'stop_limit']:
                if order.stop_price <= 0:
                    raise ValidationError("Stop price must be greater than zero.")
                
                # Check tick size for stop price
                if order.security_id.tick_size > 0:
                    # Use Decimal for precise validation
                    price_decimal = Decimal(str(order.stop_price))
                    tick_decimal = Decimal(str(order.security_id.tick_size))
                    remainder = price_decimal % tick_decimal
                    if remainder > Decimal('0.000001'):
                        raise ValidationError(
                            f"Stop price must be a multiple of tick size ({order.security_id.tick_size})"
                        )
    
    def _validate_order(self):
        """Validate order before submission"""
        self.ensure_one()
        
        # Get configuration
        config = self.env['stock.config'].get_config()
        
        # Check session is open
        if self.session_id.state != 'open':
            raise UserError("Cannot submit order to a closed session.")
        
        # Check security is active
        if not self.security_id.active:
            raise UserError("Cannot trade inactive securities.")
        
        # Check quantity
        if self.quantity <= 0:
            raise UserError("Quantity must be positive.")
        
        # Check minimum order value
        order_value = self.quantity * (self.price if self.order_type in ['limit', 'stop_limit'] else self.security_id.current_price)
        if order_value < config.min_order_value:
            raise UserError(f"Order value must be at least ${config.min_order_value:,.2f}")
        
        # Check maximum order value
        if order_value > config.max_order_value:
            raise UserError(f"Order value cannot exceed ${config.max_order_value:,.2f}")
        
        # Check daily trading limit
        today_orders = self.env['stock.order'].search([
            ('user_id', '=', self.user_id.id),
            ('create_date', '>=', fields.Date.today()),
            ('status', 'not in', ['cancelled', 'rejected'])
        ])
        today_volume = sum(o.order_value for o in today_orders)
        if today_volume + order_value > config.daily_trading_limit:
            remaining_limit = config.daily_trading_limit - today_volume
            raise UserError(f"Daily trading limit exceeded. Remaining limit: ${remaining_limit:,.2f}")
        
        # Check position limits for buy orders
        if self.side == 'buy':
            current_position = self.env['stock.position'].search([
                ('user_id', '=', self.user_id.id),
                ('security_id', '=', self.security_id.id)
            ], limit=1)
            current_quantity = current_position.quantity if current_position else 0
            
            # Check maximum position size
            max_position = int(config.max_order_value / self.security_id.current_price)
            if current_quantity + self.quantity > max_position:
                raise UserError(f"Position limit exceeded. Maximum position: {max_position} shares")
        
        # Validate user has sufficient funds/securities
        if self.side == 'buy':
            required_cash = order_value
            if self.user_id.cash_balance < required_cash:
                raise UserError(f"Insufficient funds. Required: ${required_cash:,.2f}, Available: ${self.user_id.cash_balance:,.2f}")
        else:  # sell
            position = self.env['stock.position'].search([
                ('user_id', '=', self.user_id.id),
                ('security_id', '=', self.security_id.id)
            ], limit=1)
            available_quantity = position.quantity if position else 0
            if available_quantity < self.quantity:
                raise UserError(f"Insufficient shares. Required: {self.quantity}, Available: {available_quantity}")
        
        # Validate stop orders
        if self.order_type in ['stop_loss', 'stop_limit']:
            if not self.stop_price or self.stop_price <= 0:
                raise UserError("Stop price is required for stop orders.")
            
            current_price = self.security_id.current_price
            if self.side == 'sell' and self.stop_price >= current_price:
                raise UserError("Stop price for sell orders must be below current market price.")
            elif self.side == 'buy' and self.stop_price <= current_price:
                raise UserError("Stop price for buy orders must be above current market price.")
        
        # For buy orders, check available cash
        if self.side == 'buy':
            # Calculate required amount including commission
            if self.order_type == 'market':
                # For market orders, use current price + 10% buffer
                estimated_price = self.security_id.current_price * 1.1
            else:
                estimated_price = self.price
            
            required_amount = self.quantity * estimated_price
            commission = required_amount * (self.broker_commission_rate / 100)
            total_required = required_amount + commission
            
            if self.user_id.cash_balance < total_required:
                raise UserError(
                    f"Insufficient funds. Required: {total_required:,.2f}, "
                    f"Available: {self.user_id.cash_balance:,.2f}"
                )
        
        # For sell orders, check available shares
        elif self.side == 'sell':
            position = self.env['stock.position'].search([
                ('user_id', '=', self.user_id.id),
                ('security_id', '=', self.security_id.id)
            ], limit=1)
            
            available_shares = position.quantity if position else 0
            
            # Check pending sell orders
            pending_sells = self.env['stock.order'].search([
                ('user_id', '=', self.user_id.id),
                ('security_id', '=', self.security_id.id),
                ('side', '=', 'sell'),
                ('status', 'in', ['submitted', 'open', 'partial']),
                ('id', '!=', self.id)
            ])
            
            committed_shares = sum(pending_sells.mapped('remaining_quantity'))
            available_shares -= committed_shares
            
            if available_shares < self.quantity:
                raise UserError(
                    f"Insufficient shares. Available: {available_shares}, "
                    f"Required: {self.quantity}"
                )
        
        # Check daily trading limit
        today_start = fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_orders = self.search([
            ('user_id', '=', self.user_id.id),
            ('create_date', '>=', today_start),
            ('status', 'in', ['filled', 'partial']),
            ('id', '!=', self.id)
        ])
        
        today_volume = sum(o.filled_quantity * o.average_price for o in today_orders)
        if self.order_type in ['limit', 'stop_limit']:
            new_volume = self.quantity * self.price
        else:
            new_volume = self.quantity * self.security_id.current_price
        
        if today_volume + new_volume > config.daily_trading_limit:
            raise UserError(
                f"Daily trading limit exceeded. Limit: {config.daily_trading_limit:,.2f}, "
                f"Already traded: {today_volume:,.2f}"
            )
        
        # Check position limits
        if self.side == 'buy':
            # Calculate potential new position
            current_position = self.env['stock.position'].search([
                ('user_id', '=', self.user_id.id),
                ('security_id', '=', self.security_id.id)
            ], limit=1)
            
            current_qty = current_position.quantity if current_position else 0
            new_total_qty = current_qty + self.quantity
            
            # Check against position limit
            total_shares = self.security_id.total_shares
            if total_shares > 0:
                position_percent = (new_total_qty / total_shares) * 100
                if position_percent > config.position_limit_percent:
                    raise UserError(
                        f"Position limit exceeded. Maximum allowed: {config.position_limit_percent}% "
                        f"of total shares. Your position would be: {position_percent:.2f}%"
                    )
    
    def action_submit(self):
        """Submit order for execution"""
        for order in self:
            if order.status != 'draft':
                raise UserError("Only draft orders can be submitted.")
            
            order._validate_order()
            
            # Set appropriate status based on order type
            if order.order_type in ['stop_loss', 'stop_limit']:
                order.status = 'submitted'  # Stop orders wait for trigger
            else:
                order.status = 'open'  # Regular orders are immediately open
            
            # Trigger matching engine
            self.env['stock.matching.engine'].match_all_securities(order.session_id)
            
            # Log the action
            order.message_post(body=f"Order submitted at {fields.Datetime.now()}")
    
    def action_cancel(self):
        """Cancel the order"""
        for order in self:
            if order.status not in ['pending', 'partial']:
                raise UserError("Only pending or partially filled orders can be cancelled.")
            
            order.status = 'cancelled'
            order.description = "Order cancelled by user"
            
            # Log the action
            order.message_post(body=f"Order cancelled at {fields.Datetime.now()}")
    
    def update_filled_quantity(self, qty):
        """Update filled quantity after trade execution"""
        self.ensure_one()
        self.filled_quantity += qty
        
        if self.filled_quantity >= self.quantity:
            self.status = 'filled'
        elif self.filled_quantity > 0:
            self.status = 'partial'
    
    @api.model
    def expire_orders(self):
        """Cron job to expire orders past their expiry date"""
        expired_orders = self.search([
            ('status', 'in', ['pending', 'partial']),
            ('expiry_date', '<=', fields.Datetime.now())
        ])
        
        for order in expired_orders:
            order.status = 'expired'
            order.description = "Order expired"
            order.message_post(body="Order expired due to time limit") 

    @api.model
    def expire_day_orders(self):
        """Expire day orders at end of session - called by cron or session close"""
        # Find all open day orders from closed sessions
        expired_orders = self.search([
            ('time_in_force', '=', 'day'),
            ('status', 'in', ['submitted', 'open', 'partial']),
            ('session_id.state', '=', 'closed')
        ])
        
        for order in expired_orders:
            order.status = 'expired'
            order.message_post(body="Order expired at end of trading session") 
    
    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """Override search to apply user visibility filtering unless explicitly skipped.
        - Skip filtering when context key 'skip_portal_order_filter' is True (controllers control domain).
        - Never restrict system administrators (base.group_system).
        - For other users who are not brokers/admins (by user_type), restrict to their own orders.
        """
        if not self.env.context.get('skip_portal_order_filter'):
            try:
                is_system_admin = self.env.user.has_group('base.group_system')
            except Exception:
                is_system_admin = False
            if not is_system_admin and self.env.user.user_type not in ['broker', 'admin']:
                domain = list(domain) + [('user_id', '=', self.env.user.id)]
        return super(StockOrder, self)._search(domain, offset=offset, limit=limit, order=order)