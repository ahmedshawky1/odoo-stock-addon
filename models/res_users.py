# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    # User Type
    user_type = fields.Selection([
        ('investor', 'Investor'),
        ('broker', 'Broker'),
        ('banker', 'Banker'),
        ('admin', 'Administrator')
    ], string='User Type', default='investor', tracking=True)
    
    # Financial Fields
    cash_balance = fields.Float(
        string='Cash Balance',
        digits='Product Price',
        default=0.0,
        help='Current available cash balance'
    )
    
    initial_capital = fields.Float(
        string='Initial Capital',
        digits='Product Price',
        default=100000.0,
        help='Starting capital when user was created'
    )
    
    # Relationships
    broker_id = fields.Many2one(
        'res.users',
        string='Broker',
        domain=[('user_type', '=', 'broker')],
        help='Assigned broker for this investor'
    )
    
    client_ids = fields.One2many(
        'res.users',
        'broker_id',
        string='Clients',
        help='Investors assigned to this broker'
    )
    
    # Team Information
    team_members = fields.Text(
        string='Team Members',
        help='Names of team members (for group accounts)'
    )
    
    # Portfolio Information
    position_ids = fields.One2many(
        'stock.position',
        'user_id',
        string='Stock Positions'
    )
    
    order_ids = fields.One2many(
        'stock.order',
        'user_id',
        string='Orders'
    )
    
    deposit_ids = fields.One2many(
        'stock.deposit',
        'user_id',
        string='Deposits'
    )
    
    loan_ids = fields.One2many(
        'stock.loan',
        'user_id',
        string='Loans'
    )
    
    # Computed Fields
    portfolio_value = fields.Float(
        string='Portfolio Value',
        compute='_compute_portfolio_value',
        digits='Product Price',
        help='Current market value of all stock holdings'
    )
    
    total_deposits = fields.Float(
        string='Total Deposits',
        compute='_compute_total_deposits',
        digits='Product Price'
    )
    
    total_loans = fields.Float(
        string='Total Loans',
        compute='_compute_total_loans',
        digits='Product Price'
    )
    
    total_assets = fields.Float(
        string='Total Assets',
        compute='_compute_total_assets',
        digits='Product Price',
        help='Cash + Portfolio + Deposits - Loans'
    )
    
    profit_loss = fields.Float(
        string='Profit/Loss',
        compute='_compute_profit_loss',
        digits='Product Price',
        help='Total Assets - Initial Capital'
    )
    
    profit_loss_percentage = fields.Float(
        string='P&L %',
        compute='_compute_profit_loss',
        digits=(16, 2),
        help='Profit/Loss as percentage of initial capital'
    )
    
    # Broker specific fields
    total_commission = fields.Float(
        string='Total Commission Earned',
        compute='_compute_broker_commission',
        digits='Product Price'
    )
    
    # Count fields
    order_count = fields.Integer(
        string='Order Count',
        compute='_compute_order_count'
    )
    
    @api.depends('position_ids', 'position_ids.quantity', 'position_ids.security_id.current_price')
    def _compute_portfolio_value(self):
        for user in self:
            value = 0.0
            for position in user.position_ids:
                if position.quantity > 0 and position.security_id.current_price:
                    value += position.quantity * position.security_id.current_price
            user.portfolio_value = value
    
    @api.depends('deposit_ids', 'deposit_ids.amount', 'deposit_ids.status')
    def _compute_total_deposits(self):
        for user in self:
            user.total_deposits = sum(
                deposit.amount for deposit in user.deposit_ids 
                if deposit.status == 'active'
            )
    
    @api.depends('loan_ids', 'loan_ids.amount', 'loan_ids.status')
    def _compute_total_loans(self):
        for user in self:
            user.total_loans = sum(
                loan.amount for loan in user.loan_ids 
                if loan.status == 'active'
            )
    
    @api.depends('cash_balance', 'portfolio_value', 'total_deposits', 'total_loans')
    def _compute_total_assets(self):
        for user in self:
            user.total_assets = (
                user.cash_balance + 
                user.portfolio_value + 
                user.total_deposits - 
                user.total_loans
            )
    
    @api.depends('total_assets', 'initial_capital')
    def _compute_profit_loss(self):
        for user in self:
            user.profit_loss = user.total_assets - user.initial_capital
            if user.initial_capital:
                user.profit_loss_percentage = (user.profit_loss / user.initial_capital) * 100
            else:
                user.profit_loss_percentage = 0.0
    
    @api.depends('order_ids')
    def _compute_order_count(self):
        for user in self:
            user.order_count = len(user.order_ids)
    
    @api.depends('order_ids', 'order_ids.broker_commission')
    def _compute_broker_commission(self):
        for user in self:
            if user.user_type == 'broker':
                # Sum commissions from all orders where this user is the broker
                domain = [
                    ('broker_id', '=', user.id),
                    ('status', 'in', ['partial', 'filled'])
                ]
                orders = self.env['stock.order'].search(domain)
                user.total_commission = sum(orders.mapped('broker_commission'))
            else:
                user.total_commission = 0.0
    
    @api.constrains('user_type', 'broker_id')
    def _check_broker_assignment(self):
        for user in self:
            if user.user_type == 'investor' and not user.broker_id:
                raise ValidationError("Investors must be assigned to a broker.")
            if user.user_type != 'investor' and user.broker_id:
                raise ValidationError("Only investors can have an assigned broker.")
    
    @api.constrains('cash_balance')
    def _check_cash_balance(self):
        for user in self:
            if user.cash_balance < 0:
                raise ValidationError("Cash balance cannot be negative.")
    
    def action_view_portfolio(self):
        """Open portfolio view for this user"""
        self.ensure_one()
        return {
            'name': f"{self.name}'s Portfolio",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.position',
            'view_mode': 'tree,form',
            'domain': [('user_id', '=', self.id)],
            'context': {'default_user_id': self.id}
        }
    
    def action_view_orders(self):
        """Open orders view for this user"""
        self.ensure_one()
        return {
            'name': f"{self.name}'s Orders",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.order',
            'view_mode': 'tree,form',
            'domain': [('user_id', '=', self.id)],
            'context': {'default_user_id': self.id}
        } 