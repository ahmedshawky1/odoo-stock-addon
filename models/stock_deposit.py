# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class StockDeposit(models.Model):
    _name = 'stock.deposit'
    _description = 'Bank Deposit'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Deposit Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('stock.deposit') or 'New'
    )
    
    # Parties
    user_id = fields.Many2one(
        'res.users',
        string='Depositor',
        required=True,
        states={'draft': [('readonly', False)]},
        readonly=True,
        domain=[('user_type', '=', 'investor')],
        tracking=True
    )
    
    banker_id = fields.Many2one(
        'res.users',
        string='Bank',
        required=True,
        states={'draft': [('readonly', False)]},
        readonly=True,
        domain=[('user_type', '=', 'banker')],
        tracking=True
    )
    
    # Deposit Details
    deposit_type = fields.Selection([
        ('fixed', 'Fixed Deposit'),
        ('savings', 'Savings Account'),
        ('current', 'Current Account')
    ], string='Deposit Type', required=True, default='fixed', tracking=True)
    
    amount = fields.Float(
        string='Principal Amount',
        digits='Product Price',
        required=True,
        states={'draft': [('readonly', False)]},
        readonly=True,
        tracking=True
    )
    
    interest_rate = fields.Float(
        string='Interest Rate (%)',
        digits=(16, 2),
        required=True,
        states={'draft': [('readonly', False)]},
        readonly=True,
        help='Annual interest rate',
        tracking=True
    )
    
    term_sessions = fields.Integer(
        string='Term (Sessions)',
        states={'draft': [('readonly', False)]},
        readonly=True,
        help='Deposit term in trading sessions'
    )
    
    # Sessions
    deposit_session_id = fields.Many2one(
        'stock.session',
        string='Deposit Session',
        required=True,
        states={'draft': [('readonly', False)]},
        readonly=True,
        tracking=True,
        help='Session when deposit was created'
    )
    
    maturity_session_id = fields.Many2one(
        'stock.session',
        string='Maturity Session',
        compute='_compute_maturity_session',
        store=True,
        states={'draft': [('readonly', False)]},
        readonly=True,
        tracking=True,
        help='Session when deposit matures'
    )
    
    # Status
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('matured', 'Matured'),
        ('withdrawn', 'Withdrawn'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Computed fields
    accrued_interest = fields.Float(
        string='Accrued Interest',
        compute='_compute_interest',
        digits='Product Price',
        help='Interest earned till date'
    )
    
    maturity_amount = fields.Float(
        string='Maturity Amount',
        compute='_compute_interest',
        digits='Product Price',
        help='Amount payable at maturity'
    )
    
    current_value = fields.Float(
        string='Current Value',
        compute='_compute_interest',
        digits='Product Price',
        help='Principal + Accrued Interest'
    )
    
    sessions_to_maturity = fields.Integer(
        string='Sessions to Maturity',
        compute='_compute_sessions_to_maturity',
        help='Number of sessions until maturity'
    )
    
    # Additional fields
    early_withdrawal_penalty = fields.Float(
        string='Early Withdrawal Penalty (%)',
        digits=(16, 2),
        default=2.0,
        help='Penalty for early withdrawal'
    )
    
    withdrawal_session_id = fields.Many2one(
        'stock.session',
        string='Withdrawal Session',
        readonly=True,
        help='Session when deposit was withdrawn'
    )
    
    withdrawal_amount = fields.Float(
        string='Withdrawal Amount',
        digits='Product Price',
        readonly=True
    )
    
    @api.depends('deposit_session_id', 'term_sessions')
    def _compute_maturity_session(self):
        for deposit in self:
            if deposit.deposit_session_id and deposit.term_sessions:
                # Find the session that is term_sessions after the deposit session
                all_sessions = self.env['stock.session'].search([
                    ('session_number', '>=', deposit.deposit_session_id.session_number)
                ], order='session_number')
                
                if len(all_sessions) >= deposit.term_sessions:
                    deposit.maturity_session_id = all_sessions[deposit.term_sessions - 1]
                else:
                    deposit.maturity_session_id = False
            else:
                deposit.maturity_session_id = False
    
    @api.depends('amount', 'interest_rate', 'deposit_session_id', 'status')
    def _compute_interest(self):
        for deposit in self:
            if deposit.status in ['active', 'matured', 'withdrawn']:
                # Calculate sessions elapsed
                current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
                if not current_session:
                    # Use latest session if no open session
                    current_session = self.env['stock.session'].search([], order='session_number desc', limit=1)
                
                if current_session and deposit.deposit_session_id:
                    sessions_elapsed = max(0, current_session.session_number - deposit.deposit_session_id.session_number + 1)
                else:
                    sessions_elapsed = 0
                
                # Session-based interest calculation (interest per session)
                # Convert annual rate to per-session rate (assuming ~12 trading sessions per year)
                sessions_per_year = 12
                session_interest_rate = deposit.interest_rate / sessions_per_year
                deposit.accrued_interest = (deposit.amount * session_interest_rate * sessions_elapsed) / 100
                
                # Maturity amount
                if deposit.maturity_session_id and deposit.term_sessions:
                    maturity_interest = (deposit.amount * session_interest_rate * deposit.term_sessions) / 100
                    deposit.maturity_amount = deposit.amount + maturity_interest
                else:
                    deposit.maturity_amount = deposit.amount
                
                deposit.current_value = deposit.amount + deposit.accrued_interest
            else:
                deposit.accrued_interest = 0.0
                deposit.maturity_amount = deposit.amount
                deposit.current_value = deposit.amount
    
    @api.depends('maturity_session_id', 'status')
    def _compute_sessions_to_maturity(self):
        for deposit in self:
            if deposit.maturity_session_id and deposit.status == 'active':
                # Get current session
                current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
                if current_session:
                    sessions_diff = deposit.maturity_session_id.session_number - current_session.session_number
                    deposit.sessions_to_maturity = max(0, sessions_diff)
                else:
                    deposit.sessions_to_maturity = 0
            else:
                deposit.sessions_to_maturity = 0
    
    @api.constrains('amount')
    def _check_amount(self):
        for deposit in self:
            if deposit.amount <= 0:
                raise ValidationError("Deposit amount must be positive.")
    
    @api.constrains('interest_rate')
    def _check_interest_rate(self):
        for deposit in self:
            if deposit.interest_rate < 0:
                raise ValidationError("Interest rate cannot be negative.")
            if deposit.interest_rate > 50:
                raise ValidationError("Interest rate seems too high (>50%).")
    
    def action_confirm(self):
        """Confirm the deposit and transfer funds"""
        for deposit in self:
            if deposit.status != 'draft':
                raise UserError("Only draft deposits can be confirmed.")
            
            # Use sudo to ensure proper access for fund transfers
            deposit_sudo = deposit.sudo()
            user_sudo = deposit_sudo.user_id.sudo()
            banker_sudo = deposit_sudo.banker_id.sudo()
            
            # Check user has sufficient funds
            if user_sudo.cash_balance < deposit_sudo.amount:
                raise ValidationError(
                    f"Insufficient funds. Available: {user_sudo.cash_balance:.2f}, "
                    f"Required: {deposit_sudo.amount:.2f}"
                )
            
            # Get active session
            active_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            if not active_session:
                raise UserError("No active trading session found. Please ensure a session is open before confirming deposits.")
            
            # Transfer funds with sudo privileges
            user_sudo.write({'cash_balance': user_sudo.cash_balance - deposit_sudo.amount})
            banker_sudo.write({'cash_balance': banker_sudo.cash_balance + deposit_sudo.amount})
            
            deposit_sudo.write({
                'status': 'active',
                'deposit_session_id': active_session.id
            })
            
            # Log the transaction
            self.env['stock.transaction.log'].log_transaction(
                user_id=deposit.user_id.id,
                transaction_type='deposit_investment',
                amount=-deposit.amount,
                cash_impact=-deposit.amount,
                description=f'Deposit investment - {deposit.deposit_type}',
                session_id=active_session.id,
                deposit_id=deposit.id,
                reference=f'DEP-{deposit.name}',
                notes=f'Deposit confirmed with banker {deposit.banker_id.name}'
            )
            
            # Log the transaction
            deposit.message_post(
                body=f"Deposit confirmed. {deposit.amount:,.2f} transferred from "
                     f"{deposit.user_id.name} to {deposit.banker_id.name}"
            )
    
    def action_mature(self):
        """Mark deposit as matured"""
        for deposit in self:
            if deposit.status != 'active':
                raise UserError("Only active deposits can be matured.")
            
            # Check if deposit has reached maturity session
            current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            if not current_session:
                current_session = self.env['stock.session'].search([], order='session_number desc', limit=1)
            
            if deposit.maturity_session_id and current_session:
                if current_session.session_number < deposit.maturity_session_id.session_number:
                    raise UserError(
                        f"Deposit has not reached maturity session ({deposit.maturity_session_id.name})."
                    )
            
            deposit.status = 'matured'
            deposit.message_post(body="Deposit has matured and is ready for withdrawal.")
    
    def action_withdraw(self):
        """Withdraw the deposit"""
        for deposit in self:
            if deposit.status not in ['active', 'matured']:
                raise UserError("Only active or matured deposits can be withdrawn.")
            
            # Get current session
            current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            if not current_session:
                current_session = self.env['stock.session'].search([], order='session_number desc', limit=1)
            
            # Calculate withdrawal amount
            early_withdrawal = False
            if deposit.status == 'active' and deposit.maturity_session_id and current_session:
                if current_session.session_number < deposit.maturity_session_id.session_number:
                    early_withdrawal = True
            
            if early_withdrawal:
                # Early withdrawal - apply penalty
                penalty_amount = deposit.current_value * deposit.early_withdrawal_penalty / 100
                withdrawal_amount = deposit.current_value - penalty_amount
                
                deposit.message_post(
                    body=f"Early withdrawal penalty of {penalty_amount:,.2f} applied."
                )
            else:
                withdrawal_amount = deposit.current_value
            
            # Use sudo to ensure proper access for fund transfers
            deposit_sudo = deposit.sudo()
            user_sudo = deposit_sudo.user_id.sudo()
            banker_sudo = deposit_sudo.banker_id.sudo()
            
            # Check bank has sufficient funds
            if banker_sudo.cash_balance < withdrawal_amount:
                raise ValidationError(
                    f"Bank has insufficient funds for withdrawal. "
                    f"Required: {withdrawal_amount:,.2f}"
                )
            
            # Transfer funds back with sudo privileges
            banker_sudo.write({'cash_balance': banker_sudo.cash_balance - withdrawal_amount})
            user_sudo.write({'cash_balance': user_sudo.cash_balance + withdrawal_amount})
            
            deposit_sudo.write({
                'status': 'withdrawn',
                'withdrawal_session_id': current_session.id if current_session else False,
                'withdrawal_amount': withdrawal_amount
            })
            
            # Log interest earned transaction if any
            interest_earned = deposit.accrued_interest
            if interest_earned > 0:
                self.env['stock.transaction.log'].log_transaction(
                    user_id=deposit.user_id.id,
                    transaction_type='deposit_interest',
                    amount=interest_earned,
                    cash_impact=interest_earned,
                    description=f'Interest earned on deposit - {deposit.deposit_type}',
                    session_id=current_session.id if current_session else False,
                    deposit_id=deposit.id,
                    reference=f'INT-DEP-{deposit.name}',
                    notes=f'Interest from deposit #{deposit.name}'
                )
            
            # Log withdrawal transaction (principal amount)
            self.env['stock.transaction.log'].log_transaction(
                user_id=deposit.user_id.id,
                transaction_type='deposit_withdrawal',
                amount=deposit.amount,
                cash_impact=deposit.amount,
                description=f'Deposit withdrawal - {deposit.deposit_type}',
                session_id=current_session.id if current_session else False,
                deposit_id=deposit.id,
                reference=f'WTH-DEP-{deposit.name}',
                notes=f'Principal withdrawal from deposit #{deposit.name}'
            )
            
            # If early withdrawal with penalty, log the penalty
            if early_withdrawal:
                penalty_amount = deposit.current_value * deposit.early_withdrawal_penalty / 100
                self.env['stock.transaction.log'].log_transaction(
                    user_id=deposit.user_id.id,
                    transaction_type='fee',
                    amount=-penalty_amount,
                    cash_impact=-penalty_amount,
                    description=f'Early withdrawal penalty - {deposit.deposit_type}',
                    session_id=current_session.id if current_session else False,
                    deposit_id=deposit.id,
                    reference=f'PEN-DEP-{deposit.name}',
                    notes=f'Early withdrawal penalty from deposit #{deposit.name}'
                )
            
            # Log the transaction
            deposit.message_post(
                body=f"Deposit withdrawn. {withdrawal_amount:,.2f} transferred from "
                     f"{deposit.banker_id.name} to {deposit.user_id.name}"
            )
    
    def action_cancel(self):
        """Cancel a draft deposit"""
        for deposit in self:
            if deposit.status != 'draft':
                raise UserError("Only draft deposits can be cancelled.")
            
            deposit.status = 'cancelled'
            deposit.message_post(body="Deposit cancelled.")
    
    @api.model
    def check_matured_deposits(self):
        """Check for deposits that have reached maturity session"""
        current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
        if not current_session:
            current_session = self.env['stock.session'].search([], order='session_number desc', limit=1)
        
        if current_session:
            matured_deposits = self.search([
                ('status', '=', 'active'),
                ('maturity_session_id', '!=', False),
                ('maturity_session_id.session_number', '<=', current_session.session_number)
            ])
            
            for deposit in matured_deposits:
                try:
                    deposit.action_mature()
                except Exception as e:
                    deposit.message_post(
                        body=f"Failed to auto-mature deposit: {str(e)}",
                        message_type='comment'
                    )
    
    def _calculate_interest(self):
        """Calculate and apply interest for active deposits (called at session end)"""
        self.ensure_one()
        
        if self.status != 'approved':
            return
        
        try:
            # Calculate interest based on deposit type
            if self.deposit_type == 'fixed':
                # Simple interest calculation
                days_elapsed = (fields.Date.today() - self.deposit_date).days
                if days_elapsed > 0:
                    interest = (self.amount * self.interest_rate * days_elapsed) / (365 * 100)
                    new_value = self.current_value + interest
                    
                    self.write({
                        'current_value': new_value,
                        'interest_earned': self.interest_earned + interest,
                    })
                    
                    _logger.info(f"Deposit {self.name}: Added interest {interest:.2f}, new value {new_value:.2f}")
        except Exception as e:
            _logger.error(f"Error calculating interest for deposit {self.name}: {str(e)}")
            raise 