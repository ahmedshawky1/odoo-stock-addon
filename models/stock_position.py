# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class StockPosition(models.Model):
    _name = 'stock.position'
    _description = 'Stock Position'
    _order = 'user_id, security_id'
    _rec_name = 'display_name'
    
    # Unique constraint on user + security
    _sql_constraints = [
        ('user_security_unique', 
         'UNIQUE(user_id, security_id)',
         'A user can only have one position per security.')
    ]
    
    # Identity
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # Relationships
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    security_id = fields.Many2one(
        'stock.security',
        string='Security',
        required=True,
        ondelete='restrict',
        index=True
    )
    
    # Position Details
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        default=0,
        help='Number of shares held'
    )
    
    average_cost = fields.Float(
        string='Average Cost',
        digits=(16, 4),
        required=True,
        default=0.0,
        help='Average purchase price per share'
    )
    
    # Computed Values
    cost_basis = fields.Float(
        string='Cost Basis',
        compute='_compute_values',
        digits='Product Price',
        store=True,
        help='Total investment (quantity × average cost)'
    )
    
    market_value = fields.Float(
        string='Market Value',
        compute='_compute_values',
        digits='Product Price',
        help='Current value (quantity × current price)'
    )
    
    unrealized_pnl = fields.Float(
        string='Unrealized P&L',
        compute='_compute_values',
        digits='Product Price',
        help='Market value - Cost basis'
    )
    
    unrealized_pnl_percent = fields.Float(
        string='Unrealized P&L %',
        compute='_compute_values',
        digits=(16, 2),
        help='Percentage gain/loss'
    )
    
    # Allocation
    portfolio_weight = fields.Float(
        string='Portfolio Weight %',
        compute='_compute_portfolio_weight',
        digits=(16, 2),
        help='Percentage of total portfolio value'
    )
    
    # Additional Information
    blocked_quantity = fields.Integer(
        string='Blocked Quantity',
        default=0,
        help='Shares blocked for pending sell orders'
    )
    
    available_quantity = fields.Integer(
        string='Available Quantity',
        compute='_compute_available_quantity',
        help='Quantity available for selling'
    )
    
    first_purchase_date = fields.Datetime(
        string='First Purchase Date',
        help='Date of first purchase'
    )
    
    last_transaction_date = fields.Datetime(
        string='Last Transaction Date',
        help='Date of last buy/sell'
    )
    
    @api.depends('user_id', 'security_id')
    def _compute_display_name(self):
        for position in self:
            if position.user_id and position.security_id:
                position.display_name = f"{position.user_id.name} - {position.security_id.symbol}"
            else:
                position.display_name = "New Position"
    
    @api.depends('quantity', 'average_cost', 'security_id.current_price')
    def _compute_values(self):
        for position in self:
            # Cost basis
            position.cost_basis = position.quantity * position.average_cost
            
            # Market value
            if position.security_id:
                position.market_value = position.quantity * position.security_id.current_price
                
                # P&L
                position.unrealized_pnl = position.market_value - position.cost_basis
                
                # P&L percentage
                if position.cost_basis > 0:
                    # Don't multiply by 100 since percentage widget handles this automatically
                    position.unrealized_pnl_percent = position.unrealized_pnl / position.cost_basis
                else:
                    position.unrealized_pnl_percent = 0.0
            else:
                position.market_value = 0.0
                position.unrealized_pnl = 0.0
                position.unrealized_pnl_percent = 0.0
    
    @api.depends('market_value', 'user_id.portfolio_value')
    def _compute_portfolio_weight(self):
        for position in self:
            if position.user_id and position.user_id.portfolio_value > 0:
                # Don't multiply by 100 since percentage widget handles this automatically
                position.portfolio_weight = position.market_value / position.user_id.portfolio_value
            else:
                position.portfolio_weight = 0.0
    
    @api.depends('quantity', 'blocked_quantity')
    def _compute_available_quantity(self):
        for position in self:
            position.available_quantity = position.quantity - position.blocked_quantity
    
    @api.constrains('quantity')
    def _check_quantity(self):
        for position in self:
            if position.quantity < 0:
                raise ValidationError("Position quantity cannot be negative.")
            # Keep zero positions (don't unlink) to avoid concurrent access issues during matching
            # UI or a cleanup cron may safely delete zero-qty positions later if needed
    
    @api.constrains('blocked_quantity')
    def _check_blocked_quantity(self):
        for position in self:
            if position.blocked_quantity < 0:
                raise ValidationError("Blocked quantity cannot be negative.")
            if position.blocked_quantity > position.quantity:
                raise ValidationError("Blocked quantity cannot exceed total quantity.")
    
    def update_position(self, quantity_change, price, transaction_type='buy'):
        """
        Update position after a trade
        
        :param quantity_change: Number of shares bought/sold
        :param price: Transaction price
        :param transaction_type: 'buy' or 'sell'
        """
        self.ensure_one()
        
        if transaction_type == 'buy':
            # Calculate new average cost
            total_cost = (self.quantity * self.average_cost) + (quantity_change * price)
            new_quantity = self.quantity + quantity_change
            
            if new_quantity > 0:
                new_avg_cost = total_cost / new_quantity
            else:
                new_avg_cost = 0.0
            
            self.write({
                'quantity': new_quantity,
                'average_cost': new_avg_cost,
                'last_transaction_date': fields.Datetime.now()
            })
            
            if not self.first_purchase_date:
                self.first_purchase_date = fields.Datetime.now()
                
        elif transaction_type == 'sell':
            new_quantity = self.quantity - quantity_change
            
            if new_quantity < 0:
                raise ValidationError("Cannot sell more shares than owned.")
            
            self.write({
                'quantity': new_quantity,
                'last_transaction_date': fields.Datetime.now()
            })
            
            # Keep zero positions (don't unlink) to avoid concurrent access issues during matching
    
    def block_shares(self, quantity):
        """Block shares for a pending sell order"""
        self.ensure_one()
        
        if quantity > self.available_quantity:
            raise ValidationError(
                f"Cannot block {quantity} shares. Only {self.available_quantity} available."
            )
        
        self.blocked_quantity += quantity
    
    def unblock_shares(self, quantity):
        """Unblock shares when order is cancelled or filled"""
        self.ensure_one()
        
        if quantity > self.blocked_quantity:
            raise ValidationError(
                f"Cannot unblock {quantity} shares. Only {self.blocked_quantity} blocked."
            )
        
        self.blocked_quantity -= quantity
    
    def action_view_trades(self):
        """View all trades for this position"""
        self.ensure_one()
        
        # Get trades where user is buyer or seller of this security
        domain = [
            ('security_id', '=', self.security_id.id),
            '|',
            ('buyer_id', '=', self.user_id.id),
            ('seller_id', '=', self.user_id.id)
        ]
        
        return {
            'name': f'Trades - {self.security_id.symbol}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.trade',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {
                'default_security_id': self.security_id.id,
                'search_default_group_by_trade_date': 1
            }
        }
    
    def action_sell_position(self):
        """Quick action to create a sell order for this position"""
        self.ensure_one()
        
        # Get active session
        active_session = self.env['stock.session'].search([
            ('state', '=', 'open')
        ], limit=1)
        
        if not active_session:
            raise ValidationError("No active trading session.")
        
        return {
            'name': f'Sell {self.security_id.symbol}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.order',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_user_id': self.user_id.id,
                'default_security_id': self.security_id.id,
                'default_session_id': active_session.id,
                'default_side': 'sell',
                'default_quantity': self.available_quantity,
                'default_price': self.security_id.current_price,
                'default_order_type': 'limit'
            }
        }
    
    def _apply_ir_rules(self, query, mode='read'):
        """Override to allow full access for system admins and relax for broker/admin user_type"""
        try:
            is_system_admin = self.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if is_system_admin or self.env.user.user_type in ['broker', 'admin']:
            # System admins, brokers, and admins can see all positions
            return super(StockPosition, self)._apply_ir_rules(query, mode)
        # Other users only see their own positions - use domain filtering instead
        # In Odoo 18, we should use domain filtering rather than direct query manipulation
        return super(StockPosition, self)._apply_ir_rules(query, mode)
    
    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """Override search to apply user_type/group based filtering"""
        try:
            is_system_admin = self.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if not is_system_admin and self.env.user.user_type not in ['broker', 'admin']:
            # Add domain filter for non-broker/admin users
            domain = list(domain) + [('user_id', '=', self.env.user.id)]
        return super(StockPosition, self)._search(domain, offset=offset, limit=limit, order=order)