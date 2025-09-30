# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class StockLoan(models.Model):
    _name = 'stock.loan'
    _description = 'Bank Loan'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Loan Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('stock.loan') or 'New'
    )
    
    # Parties
    user_id = fields.Many2one(
        'res.users',
        string='Borrower',
        required=True,
        readonly="status != 'draft'",
        domain=[('user_type', '=', 'investor')],
        tracking=True
    )
    
    banker_id = fields.Many2one(
        'res.users',
        string='Lender (Bank)',
        required=True,
        readonly="status != 'draft'",
        domain=[('user_type', '=', 'banker')],
        tracking=True
    )
    
    # Loan Details
    loan_type = fields.Selection([
        ('personal', 'Personal Loan'),
        ('margin', 'Margin Loan'),
        ('secured', 'Secured Loan')
    ], string='Loan Type', required=True, default='personal', tracking=True)
    
    amount = fields.Float(
        string='Loan Amount',
        digits='Product Price',
        required=True,
        readonly="status != 'draft'",
        tracking=True
    )
    
    interest_rate = fields.Float(
        string='Interest Rate (%)',
        digits=(16, 2),
        required=True,
        readonly="status != 'draft'",
        help='Annual interest rate',
        tracking=True
    )
    
    term_months = fields.Integer(
        string='Term (Months)',
        required=True,
        readonly="status != 'draft'",
        help='Loan term in months',
        tracking=True
    )
    
    # Collateral (for secured loans)
    collateral_security_id = fields.Many2one(
        'stock.security',
        string='Collateral Security',
        readonly="status != 'draft'",
        help='Security pledged as collateral'
    )
    
    collateral_quantity = fields.Integer(
        string='Collateral Quantity',
        readonly="status != 'draft'",
        help='Number of shares pledged'
    )
    
    collateral_value = fields.Float(
        string='Collateral Value',
        compute='_compute_collateral_value',
        digits='Product Price',
        help='Current market value of collateral'
    )
    
    ltv_ratio = fields.Float(
        string='LTV Ratio (%)',
        compute='_compute_ltv_ratio',
        digits=(16, 2),
        help='Loan to Value ratio'
    )
    
    # Dates
    disbursement_date = fields.Date(
        string='Disbursement Date',
        readonly=True,
        tracking=True
    )
    
    maturity_date = fields.Date(
        string='Maturity Date',
        compute='_compute_maturity_date',
        store=True,
        tracking=True
    )
    
    # Status
    status = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('paid', 'Paid'),
        ('defaulted', 'Defaulted'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Financial calculations
    principal_outstanding = fields.Float(
        string='Principal Outstanding',
        digits='Product Price',
        readonly=True,
        default=0.0,
        tracking=True
    )
    
    interest_accrued = fields.Float(
        string='Interest Accrued',
        compute='_compute_interest',
        digits='Product Price',
        help='Total interest accrued till date'
    )
    
    total_outstanding = fields.Float(
        string='Total Outstanding',
        compute='_compute_interest',
        digits='Product Price',
        help='Principal + Interest'
    )
    
    emi_amount = fields.Float(
        string='EMI Amount',
        compute='_compute_emi',
        digits='Product Price',
        help='Equated Monthly Installment'
    )
    
    # Payment tracking
    payment_ids = fields.One2many(
        'stock.loan.payment',
        'loan_id',
        string='Payments'
    )
    
    total_paid = fields.Float(
        string='Total Paid',
        compute='_compute_payments',
        digits='Product Price'
    )
    
    next_payment_date = fields.Date(
        string='Next Payment Date',
        compute='_compute_next_payment'
    )
    
    # Risk metrics
    margin_call_price = fields.Float(
        string='Margin Call Price',
        digits=(16, 4),
        help='Security price that triggers margin call'
    )
    
    margin_call_triggered = fields.Boolean(
        string='Margin Call Triggered',
        default=False,
        tracking=True
    )
    
    penalty_amount = fields.Float(
        string='Penalty Amount',
        digits='Product Price',
        default=0.0,
        tracking=True
    )
    
    session_id = fields.Many2one(
        'stock.session',
        string='Session Created',
        help='Trading session when loan was created'
    )
    
    @api.depends('collateral_security_id', 'collateral_quantity')
    def _compute_collateral_value(self):
        for loan in self:
            if loan.collateral_security_id and loan.collateral_quantity:
                loan.collateral_value = (
                    loan.collateral_quantity * 
                    loan.collateral_security_id.current_price
                )
            else:
                loan.collateral_value = 0.0
    
    @api.depends('amount', 'collateral_value')
    def _compute_ltv_ratio(self):
        for loan in self:
            if loan.collateral_value > 0:
                loan.ltv_ratio = (loan.amount / loan.collateral_value) * 100
            else:
                loan.ltv_ratio = 0.0
    
    @api.depends('disbursement_date', 'term_months')
    def _compute_maturity_date(self):
        for loan in self:
            if loan.disbursement_date and loan.term_months:
                loan.maturity_date = (
                    loan.disbursement_date + 
                    timedelta(days=loan.term_months * 30)
                )
            else:
                loan.maturity_date = False
    
    @api.depends('principal_outstanding', 'interest_rate', 'disbursement_date', 'status', 'penalty_amount')
    def _compute_interest(self):
        for loan in self:
            if loan.status == 'active' and loan.disbursement_date:
                days = (fields.Date.today() - loan.disbursement_date).days
                loan.interest_accrued = (
                    loan.principal_outstanding * 
                    loan.interest_rate * days
                ) / (365 * 100)
                loan.total_outstanding = (
                    loan.principal_outstanding + 
                    loan.interest_accrued +
                    loan.penalty_amount
                )
            else:
                loan.interest_accrued = 0.0
                loan.total_outstanding = loan.principal_outstanding + loan.penalty_amount
    
    @api.depends('amount', 'interest_rate', 'term_months')
    def _compute_emi(self):
        for loan in self:
            if loan.amount > 0 and loan.interest_rate > 0 and loan.term_months > 0:
                # EMI calculation using reducing balance method
                r = loan.interest_rate / (12 * 100)  # Monthly interest rate
                n = loan.term_months
                
                if r > 0:
                    emi = loan.amount * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
                else:
                    emi = loan.amount / n
                
                loan.emi_amount = round(emi, 2)
            else:
                loan.emi_amount = 0.0
    
    @api.depends('payment_ids.amount')
    def _compute_payments(self):
        for loan in self:
            loan.total_paid = sum(loan.payment_ids.mapped('amount'))
    
    @api.depends('payment_ids.payment_date', 'disbursement_date', 'status')
    def _compute_next_payment(self):
        for loan in self:
            if loan.status == 'active' and loan.disbursement_date:
                last_payment = loan.payment_ids.sorted('payment_date', reverse=True)[:1]
                if last_payment:
                    loan.next_payment_date = last_payment.payment_date + timedelta(days=30)
                else:
                    loan.next_payment_date = loan.disbursement_date + timedelta(days=30)
            else:
                loan.next_payment_date = False
    
    @api.constrains('amount')
    def _check_amount(self):
        for loan in self:
            if loan.amount <= 0:
                raise ValidationError("Loan amount must be positive.")
    
    @api.constrains('loan_type', 'collateral_security_id', 'collateral_quantity')
    def _check_collateral(self):
        for loan in self:
            if loan.loan_type in ['margin', 'secured']:
                if not loan.collateral_security_id:
                    raise ValidationError("Collateral security is required for secured loans.")
                if loan.collateral_quantity <= 0:
                    raise ValidationError("Collateral quantity must be positive.")
    
    def action_approve(self):
        """Approve the loan application"""
        for loan in self:
            if loan.status != 'draft':
                raise UserError("Only draft loans can be approved.")
            
            # Check collateral for secured loans
            if loan.loan_type in ['margin', 'secured']:
                position = self.env['stock.position'].search([
                    ('user_id', '=', loan.user_id.id),
                    ('security_id', '=', loan.collateral_security_id.id)
                ], limit=1)
                
                if not position or position.available_quantity < loan.collateral_quantity:
                    raise ValidationError(
                        f"Borrower does not have sufficient {loan.collateral_security_id.symbol} "
                        f"shares for collateral."
                    )
            
            loan.status = 'approved'
            loan.message_post(body="Loan application approved.")
    
    def action_disburse(self):
        """Disburse the loan amount"""
        for loan in self:
            if loan.status != 'approved':
                raise UserError("Only approved loans can be disbursed.")
            
            # Check bank has sufficient funds
            if loan.banker_id.cash_balance < loan.amount:
                raise ValidationError(
                    f"Bank has insufficient funds. "
                    f"Available: {loan.banker_id.cash_balance:.2f}, "
                    f"Required: {loan.amount:.2f}"
                )
            
            # Get active session
            active_session = self.env['stock.session'].search([
                ('state', '=', 'open')
            ], limit=1)
            
            # Block collateral if secured loan
            if loan.loan_type in ['margin', 'secured']:
                position = self.env['stock.position'].search([
                    ('user_id', '=', loan.user_id.id),
                    ('security_id', '=', loan.collateral_security_id.id)
                ], limit=1)
                
                if position:
                    position.block_shares(loan.collateral_quantity)
            
            # Transfer funds
            loan.banker_id.cash_balance -= loan.amount
            loan.user_id.cash_balance += loan.amount
            
            loan.write({
                'status': 'active',
                'disbursement_date': fields.Date.today(),
                'principal_outstanding': loan.amount,
                'session_id': active_session.id if active_session else False
            })
            
            # Set margin call price using configuration
            if loan.collateral_security_id:
                config = self.env['stock.config'].get_config()
                loan.margin_call_price = loan.collateral_security_id.current_price * (config.margin_call_threshold / 100)
            
            # Log the transaction
            loan.message_post(
                body=f"Loan disbursed. {loan.amount:,.2f} transferred from "
                     f"{loan.banker_id.name} to {loan.user_id.name}"
            )
    
    def action_make_payment(self):
        """Open wizard to make a payment"""
        self.ensure_one()
        
        return {
            'name': 'Make Loan Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.loan.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_loan_id': self.id,
                'default_amount': self.emi_amount
            }
        }
    
    def check_margin_call(self):
        """Check if margin call is triggered"""
        self.ensure_one()
        
        if (self.loan_type in ['margin', 'secured'] and 
            self.collateral_security_id and 
            self.status == 'active'):
            
            current_price = self.collateral_security_id.current_price
            
            if current_price <= self.margin_call_price and not self.margin_call_triggered:
                # Trigger margin call
                self.margin_call_triggered = True
                self.message_post(
                    body=f"⚠️ MARGIN CALL: {self.collateral_security_id.symbol} "
                         f"price ({current_price}) has fallen below margin call level "
                         f"({self.margin_call_price})",
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )
                
                # Execute margin call after grace period
                self.with_delay(eta=datetime.now() + timedelta(hours=24)).execute_margin_call()
                
                return True
        
        return False
    
    def execute_margin_call(self):
        """Execute margin call by liquidating collateral"""
        self.ensure_one()
        
        if (self.loan_type in ['margin', 'secured'] and 
            self.status == 'active' and 
            self.margin_call_triggered):
            
            # Get active session
            active_session = self.env['stock.session'].search([
                ('state', '=', 'open')
            ], limit=1)
            
            if not active_session:
                # Retry later if no active session
                self.with_delay(eta=datetime.now() + timedelta(hours=1)).execute_margin_call()
                return
            
            # Create sell order for collateral
            order_vals = {
                'user_id': self.user_id.id,
                'security_id': self.collateral_security_id.id,
                'side': 'sell',
                'order_type': 'market',
                'quantity': self.collateral_quantity,
                'session_id': active_session.id,
                'description': f'Margin call liquidation for loan {self.name}'
            }
            
            try:
                order = self.env['stock.order'].create(order_vals)
                order.action_submit()
                
                self.message_post(
                    body=f"Margin call executed - liquidating {self.collateral_quantity} "
                         f"shares of {self.collateral_security_id.symbol}"
                )
                
                # Mark loan as defaulted
                self.status = 'defaulted'
                
            except Exception as e:
                self.message_post(
                    body=f"Failed to execute margin call: {str(e)}",
                    message_type='comment'
                )
    
    def apply_default_penalty(self):
        """Apply penalties for overdue payments"""
        self.ensure_one()
        
        if self.status == 'active' and self.next_payment_date and self.next_payment_date < fields.Date.today():
            days_overdue = (fields.Date.today() - self.next_payment_date).days
            
            # Get configuration
            config = self.env['stock.config'].get_config()
            
            # Apply daily penalty based on configuration
            penalty_rate = (config.default_penalty_rate / 100) * days_overdue
            new_penalty = self.principal_outstanding * penalty_rate
            
            # Update penalty amount
            self.penalty_amount += new_penalty
            
            self.message_post(
                body=f"Late payment penalty applied: {new_penalty:,.2f} "
                     f"({days_overdue} days overdue)"
            )
            
            # Default after configured days
            if days_overdue > config.loan_default_days and self.status != 'defaulted':
                self.status = 'defaulted'
                
                # Block user from new loans
                self.user_id.message_post(
                    body=f"⚠️ Loan {self.name} has defaulted. "
                         f"You are blocked from taking new loans until this is cleared.",
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )
                
                # Notify banker
                self.banker_id.message_post(
                    body=f"⚠️ Loan {self.name} to {self.user_id.name} has defaulted. "
                         f"Total outstanding: {self.total_outstanding:,.2f}",
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment'
                )
    
    @api.model
    def check_overdue_loans(self):
        """Cron job to check for overdue loans and apply penalties"""
        overdue_loans = self.search([
            ('status', '=', 'active'),
            ('next_payment_date', '<', fields.Date.today())
        ])
        
        for loan in overdue_loans:
            try:
                loan.apply_default_penalty()
            except Exception as e:
                loan.message_post(
                    body=f"Failed to apply penalty: {str(e)}",
                    message_type='comment'
                )
        
        # Also check for margin calls
        margin_loans = self.search([
            ('status', '=', 'active'),
            ('loan_type', 'in', ['margin', 'secured']),
            ('margin_call_triggered', '=', False)
        ])
        
        for loan in margin_loans:
            try:
                loan.check_margin_call()
            except Exception as e:
                loan.message_post(
                    body=f"Failed to check margin call: {str(e)}",
                    message_type='comment'
                )


class StockLoanPayment(models.Model):
    _name = 'stock.loan.payment'
    _description = 'Loan Payment'
    _order = 'payment_date desc'
    
    loan_id = fields.Many2one(
        'stock.loan',
        string='Loan',
        required=True,
        ondelete='cascade'
    )
    
    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.today
    )
    
    amount = fields.Float(
        string='Amount',
        digits='Product Price',
        required=True
    )
    
    principal_component = fields.Float(
        string='Principal',
        digits='Product Price'
    )
    
    interest_component = fields.Float(
        string='Interest',
        digits='Product Price'
    )
    
    penalty_component = fields.Float(
        string='Penalty',
        digits='Product Price'
    )
    
    payment_type = fields.Selection([
        ('emi', 'EMI'),
        ('prepayment', 'Prepayment'),
        ('foreclosure', 'Foreclosure')
    ], string='Payment Type', default='emi')
    
    @api.model
    def create(self, vals):
        payment = super().create(vals)
        
        # Update loan principal and penalty
        if payment.principal_component:
            payment.loan_id.principal_outstanding -= payment.principal_component
        
        if payment.penalty_component:
            payment.loan_id.penalty_amount -= payment.penalty_component
            
        # Check if loan is fully paid
        if payment.loan_id.principal_outstanding <= 0:
            payment.loan_id.status = 'paid'
            
            # Release collateral
            if payment.loan_id.loan_type in ['margin', 'secured']:
                position = self.env['stock.position'].search([
                    ('user_id', '=', payment.loan_id.user_id.id),
                    ('security_id', '=', payment.loan_id.collateral_security_id.id)
                ], limit=1)
                
                if position:
                    position.unblock_shares(payment.loan_id.collateral_quantity)
        
        return payment 