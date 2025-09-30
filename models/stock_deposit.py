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
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain=[('user_type', '=', 'investor')],
        tracking=True
    )
    
    banker_id = fields.Many2one(
        'res.users',
        string='Bank',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
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
        readonly=True,
        states={'draft': [('readonly', False)]},
        tracking=True
    )
    
    interest_rate = fields.Float(
        string='Interest Rate (%)',
        digits=(16, 2),
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Annual interest rate',
        tracking=True
    )
    
    term_months = fields.Integer(
        string='Term (Months)',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Deposit term in months'
    )
    
    # Dates
    deposit_date = fields.Date(
        string='Deposit Date',
        required=True,
        default=fields.Date.today,
        readonly=True,
        states={'draft': [('readonly', False)]},
        tracking=True
    )
    
    maturity_date = fields.Date(
        string='Maturity Date',
        compute='_compute_maturity_date',
        store=True,
        readonly=False,
        states={'active': [('readonly', True)], 'matured': [('readonly', True)]},
        tracking=True
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
    
    days_to_maturity = fields.Integer(
        string='Days to Maturity',
        compute='_compute_days_to_maturity'
    )
    
    # Additional fields
    early_withdrawal_penalty = fields.Float(
        string='Early Withdrawal Penalty (%)',
        digits=(16, 2),
        default=2.0,
        help='Penalty for early withdrawal'
    )
    
    session_id = fields.Many2one(
        'stock.session',
        string='Session Created',
        help='Trading session when deposit was created'
    )
    
    withdrawal_date = fields.Date(
        string='Withdrawal Date',
        readonly=True
    )
    
    withdrawal_amount = fields.Float(
        string='Withdrawal Amount',
        digits='Product Price',
        readonly=True
    )
    
    @api.depends('deposit_date', 'term_months')
    def _compute_maturity_date(self):
        for deposit in self:
            if deposit.deposit_date and deposit.term_months:
                deposit.maturity_date = deposit.deposit_date + timedelta(days=deposit.term_months * 30)
            else:
                deposit.maturity_date = False
    
    @api.depends('amount', 'interest_rate', 'deposit_date', 'status')
    def _compute_interest(self):
        for deposit in self:
            if deposit.status in ['active', 'matured', 'withdrawn']:
                # Calculate days
                if deposit.status == 'withdrawn' and deposit.withdrawal_date:
                    end_date = deposit.withdrawal_date
                else:
                    end_date = fields.Date.today()
                
                days = (end_date - deposit.deposit_date).days
                
                # Simple interest calculation
                deposit.accrued_interest = (deposit.amount * deposit.interest_rate * days) / (365 * 100)
                
                # Maturity amount
                if deposit.maturity_date:
                    maturity_days = (deposit.maturity_date - deposit.deposit_date).days
                    maturity_interest = (deposit.amount * deposit.interest_rate * maturity_days) / (365 * 100)
                    deposit.maturity_amount = deposit.amount + maturity_interest
                else:
                    deposit.maturity_amount = deposit.amount
                
                deposit.current_value = deposit.amount + deposit.accrued_interest
            else:
                deposit.accrued_interest = 0.0
                deposit.maturity_amount = deposit.amount
                deposit.current_value = deposit.amount
    
    @api.depends('maturity_date', 'status')
    def _compute_days_to_maturity(self):
        for deposit in self:
            if deposit.maturity_date and deposit.status == 'active':
                days = (deposit.maturity_date - fields.Date.today()).days
                deposit.days_to_maturity = max(0, days)
            else:
                deposit.days_to_maturity = 0
    
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
            
            # Check user has sufficient funds
            if deposit.user_id.cash_balance < deposit.amount:
                raise ValidationError(
                    f"Insufficient funds. Available: {deposit.user_id.cash_balance:.2f}, "
                    f"Required: {deposit.amount:.2f}"
                )
            
            # Get active session
            active_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            
            # Transfer funds
            deposit.user_id.cash_balance -= deposit.amount
            deposit.banker_id.cash_balance += deposit.amount
            
            deposit.write({
                'status': 'active',
                'session_id': active_session.id if active_session else False
            })
            
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
            
            if fields.Date.today() < deposit.maturity_date:
                raise UserError(
                    f"Deposit has not reached maturity date ({deposit.maturity_date})."
                )
            
            deposit.status = 'matured'
            deposit.message_post(body="Deposit has matured and is ready for withdrawal.")
    
    def action_withdraw(self):
        """Withdraw the deposit"""
        for deposit in self:
            if deposit.status not in ['active', 'matured']:
                raise UserError("Only active or matured deposits can be withdrawn.")
            
            # Calculate withdrawal amount
            if deposit.status == 'active' and fields.Date.today() < deposit.maturity_date:
                # Early withdrawal - apply penalty
                penalty_amount = deposit.current_value * deposit.early_withdrawal_penalty / 100
                withdrawal_amount = deposit.current_value - penalty_amount
                
                deposit.message_post(
                    body=f"Early withdrawal penalty of {penalty_amount:,.2f} applied."
                )
            else:
                withdrawal_amount = deposit.current_value
            
            # Check bank has sufficient funds
            if deposit.banker_id.cash_balance < withdrawal_amount:
                raise ValidationError(
                    f"Bank has insufficient funds for withdrawal. "
                    f"Required: {withdrawal_amount:,.2f}"
                )
            
            # Transfer funds back
            deposit.banker_id.cash_balance -= withdrawal_amount
            deposit.user_id.cash_balance += withdrawal_amount
            
            deposit.write({
                'status': 'withdrawn',
                'withdrawal_date': fields.Date.today(),
                'withdrawal_amount': withdrawal_amount
            })
            
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
        """Cron job to automatically mark matured deposits"""
        matured_deposits = self.search([
            ('status', '=', 'active'),
            ('maturity_date', '<=', fields.Date.today())
        ])
        
        for deposit in matured_deposits:
            try:
                deposit.action_mature()
            except Exception as e:
                deposit.message_post(
                    body=f"Failed to auto-mature deposit: {str(e)}",
                    message_type='comment'
                ) 