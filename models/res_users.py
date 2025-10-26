# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    # Override email field to have a default value
    email = fields.Char(
        string='Email',
        default='example@example.com',
        help='Email address of the user'
    )
    
    # User Type - Following User Stories 5-tier hierarchy
    user_type = fields.Selection([
        ('superadmin', 'Super Admin'),
        ('admin', 'Administrator'), 
        ('banker', 'Banker'),
        ('broker', 'Broker'),
        ('investor', 'Investor')
    ], string='User Type', default='investor', tracking=True, help='User role hierarchy: SuperAdmin > Admin > Banker/Broker/Investor')
    
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
    
    # User Stories aligned fields
    start_profit = fields.Float(
        string='Start Profit',
        digits='Product Price',
        default=0.0,
        help='Starting profit amount (from User Stories: StartProfit field)'
    )
    
    responsibility = fields.Char(
        string='Responsibility/Department', 
        help='User responsibility or department assignment'
    )
    
    mf_account = fields.Char(
        string='MF Account',
        help='Reference to MF account for bankers'
    )
    
    # Relationships
    # Default broker functionality removed
    
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
    
    # User blocking system
    block_ids = fields.One2many(
        'stock.user.block',
        'user_id',
        string='User Blocks'
    )
    
    is_blocked = fields.Boolean(
        string='Is Blocked',
        compute='_compute_is_blocked',
        help='True if user is currently blocked'
    )
    
    current_block_info = fields.Text(
        string='Block Information',
        compute='_compute_is_blocked',
        help='Information about current block if any'
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
        help='Current profit/loss calculated as: (Total Assets - Initial Capital)'
    )
    
    # User Stories aligned profit field
    profit = fields.Float(
        string='Profit (User Stories)',
        digits='Product Price',
        default=0.0,
        help='Current profit amount (aligned with User Stories Profit field)'
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
            loan.amount for loan in self.loan_ids 
                if loan.status == 'active'
            )
    
    @api.depends('cash_balance', 'portfolio_value', 'total_deposits', 'total_loans')
    def _compute_total_assets(self):
        for user in self:
            user.total_assets = user.cash_balance + user.portfolio_value + user.total_deposits - user.total_loans
    
    @api.depends('total_assets', 'initial_capital', 'start_profit')
    def _compute_profit_loss(self):
        for user in self:
            # Calculate profit/loss using User Stories approach
            # Profit = Current Total Assets - Initial Capital - Start Profit
            user.profit_loss = user.total_assets - user.initial_capital - user.start_profit
            
            # Update the User Stories aligned profit field
            user.profit = user.profit_loss
            if user.initial_capital:
                # Don't multiply by 100 since percentage widget handles this automatically
                user.profit_loss_percentage = user.profit_loss / user.initial_capital
            else:
                user.profit_loss_percentage = 0.0
    
    @api.depends('block_ids', 'block_ids.status')
    def _compute_is_blocked(self):
        for user in self:
            block_check = self.env['stock.user.block'].check_user_blocked(user.id)
            user.is_blocked = block_check['is_blocked']
            
            if block_check['is_blocked']:
                user.current_block_info = f"Blocked: {block_check['reason']}"
                if block_check.get('custom_reason'):
                    user.current_block_info += f"\nDetails: {block_check['custom_reason']}"
                user.current_block_info += f"\nUntil: {block_check['blocked_until']}"
                user.current_block_info += f"\nRemaining: {block_check['remaining_time']}"
            else:
                user.current_block_info = False

    @api.depends('order_ids')
    def _compute_order_count(self):
        for user in self:
            user.order_count = len(user.order_ids)
    
    @api.depends('user_type')
    def _compute_broker_commission(self):
        """Broker commission computation removed - no default broker relationships"""
        for user in self:
            user.total_commission = 0.0
    
    @api.constrains('cash_balance')
    def _check_cash_balance(self):
        for user in self:
            if user.cash_balance < 0:
                raise ValidationError("Cash balance cannot be negative.")

    @api.model
    @api.model
    def create(self, vals):
        """Seed investor wallet with initial capital on creation if cash_balance not provided."""
        # Support batch creates
        def _prepare(v):
            user_type = v.get('user_type') or 'investor'
            # Only seed for investors and only when not explicitly provided
            if user_type == 'investor' and 'cash_balance' not in v:
                init_cap = v.get('initial_capital')
                if init_cap is None:
                    # Fall back to field default (100000.0)
                    init_cap = 100000.0
                v = dict(v, cash_balance=init_cap)
            
            return v
        
        if isinstance(vals, list):
            vals = [_prepare(v) for v in vals]
        else:
            vals = _prepare(vals)
        
        # Create user
        users = super().create(vals)
        
        # Log initial capital for investors
        for user in users:
            if user.user_type == 'investor' and user.initial_capital > 0:
                try:
                    self.env['stock.transaction.log'].log_transaction(
                        user_id=user.id,
                        transaction_type='initial_capital',
                        amount=user.initial_capital,
                        cash_impact=user.initial_capital,
                        description=f'Initial capital allocation',
                        transaction_date=user.create_date or fields.Datetime.now(),
                        reference='INITIAL-CAP',
                        notes=f'Starting capital for investor {user.name}'
                    )
                except Exception as e:
                    # Don't fail user creation if transaction log fails
                    _logger.warning(f"Failed to log initial capital for user {user.name}: {str(e)}")
        
        return users
    
    def action_view_portfolio(self):
        """Open portfolio view for this user"""
        self.ensure_one()
        return {
            'name': f"{self.name}'s Portfolio",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.position',
            'view_mode': 'list,form',
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
            'view_mode': 'list,form',
            'domain': [('user_id', '=', self.id)],
            'context': {'default_user_id': self.id}
        }
    
    def action_block_user(self):
        """Open wizard to block this user"""
        self.ensure_one()
        return {
            'name': f"Block User: {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.user.block',
            'view_mode': 'form',
            'context': {'default_user_id': self.id},
            'target': 'new'
        }
    
    def action_view_blocks(self):
        """View all blocks for this user"""
        self.ensure_one()
        return {
            'name': f"Blocks - {self.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.user.block',
            'view_mode': 'list,form',
            'domain': [('user_id', '=', self.id)],
            'context': {'default_user_id': self.id}
        } 

    def action_seed_cash_from_initial(self):
        """Set cash_balance to initial_capital for this user if eligible.
        Eligibility: user_type == 'investor' (or unset), initial_capital > 0, and current cash <= 0.
        """
        for usr in self.sudo():
            if usr.user_type not in ('investor', False):
                continue
            if usr.initial_capital and usr.initial_capital > 0 and (not usr.cash_balance or usr.cash_balance <= 0.0):
                usr.cash_balance = usr.initial_capital
        return True

    @api.model
    def cron_backfill_cash_from_initial(self):
        """One-time backfill: set cash_balance to initial_capital for eligible users.
        Eligibility: initial_capital > 0, cash_balance == 0, user_type in ('investor', False).
        After executing, the cron deactivates itself.
        """
        # Use sudo to avoid access issues in scheduler context
        users = self.sudo().search([('initial_capital', '>', 0)])
        patched = 0
        for usr in users:
            if (not usr.cash_balance or usr.cash_balance == 0.0) and (usr.user_type in ('investor', False)):
                usr.cash_balance = usr.initial_capital
                patched += 1
        # Deactivate the cron if present
        try:
            cron = self.env.ref('stock_market_simulation.ir_cron_seed_investor_cash_once')
            if cron and cron.active:
                cron.active = False
        except Exception:
            # If ref not found or any issue, ignore
            pass
        return patched

    @api.model
    def fix_missing_emails(self):
        """Add default email to users without email to prevent email configuration errors"""
        try:
            users_without_email = self.sudo().search([
                '|', ('email', '=', False), ('email', '=', '')
            ])
            count = len(users_without_email)
            
            if count > 0:
                _logger.info(f"Fixing {count} users without email addresses")
                for user in users_without_email:
                    user.email = 'example@example.com'
                    # Also update the related partner if it exists
                    if user.partner_id and not user.partner_id.email:
                        user.partner_id.email = 'example@example.com'
                        
                _logger.info(f"Successfully updated {count} users with default email")
                return {'success': True, 'updated_count': count}
            else:
                _logger.info("All users already have email addresses")
                return {'success': True, 'updated_count': 0}
                
        except Exception as e:
            _logger.error(f"Error fixing user emails: {str(e)}")
            return {'success': False, 'error': str(e)}