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
        states={'draft': [('readonly', False)]},
        readonly=True,
        domain=[('user_type', '=', 'investor')],
        tracking=True
    )
    
    banker_id = fields.Many2one(
        'res.users',
        string='Lender (Bank)',
        required=True,
        states={'draft': [('readonly', False)]},
        readonly=True,
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
        required=True,
        states={'draft': [('readonly', False)]},
        readonly=True,
        help='Loan term in trading sessions',
        tracking=True
    )
    
    # Collateral (for secured loans)
    collateral_security_id = fields.Many2one(
        'stock.security',
        string='Collateral Security',
        states={'draft': [('readonly', False)]},
        readonly=True,
        help='Security pledged as collateral'
    )
    
    collateral_quantity = fields.Integer(
        string='Collateral Quantity',
        states={'draft': [('readonly', False)]},
        readonly=True,
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
    disbursement_session_id = fields.Many2one(
        'stock.session',
        string='Disbursement Session',
        readonly=True,
        tracking=True,
        help='Session when loan was disbursed'
    )
    
    maturity_session_id = fields.Many2one(
        'stock.session',
        string='Maturity Session',
        compute='_compute_maturity_session',
        store=True,
        tracking=True,
        help='Session when loan matures'
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
    
    @api.depends('disbursement_session_id', 'term_sessions')
    def _compute_maturity_session(self):
        for loan in self:
            if loan.disbursement_session_id and loan.term_sessions:
                # Find the session that is term_sessions after the disbursement session
                all_sessions = self.env['stock.session'].search([
                    ('session_number', '>=', loan.disbursement_session_id.session_number)
                ], order='session_number')
                
                if len(all_sessions) >= loan.term_sessions:
                    loan.maturity_session_id = all_sessions[loan.term_sessions - 1]
                else:
                    loan.maturity_session_id = False
            else:
                loan.maturity_session_id = False
    
    @api.depends('principal_outstanding', 'interest_rate', 'disbursement_session_id', 'status', 'penalty_amount')
    def _compute_interest(self):
        for loan in self:
            if loan.status == 'active' and loan.disbursement_session_id:
                # Calculate sessions elapsed
                current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
                if not current_session:
                    current_session = self.env['stock.session'].search([], order='session_number desc', limit=1)
                
                if current_session:
                    sessions_elapsed = max(0, current_session.session_number - loan.disbursement_session_id.session_number + 1)
                else:
                    sessions_elapsed = 0
                # Session-based interest calculation
                sessions_per_year = 12
                session_interest_rate = loan.interest_rate / sessions_per_year
                loan.interest_accrued = (
                    loan.principal_outstanding * 
                    session_interest_rate * sessions_elapsed
                ) / 100
                loan.total_outstanding = (
                    loan.principal_outstanding + 
                    loan.interest_accrued +
                    loan.penalty_amount
                )
            else:
                loan.interest_accrued = 0.0
                loan.total_outstanding = loan.principal_outstanding + loan.penalty_amount
    
    @api.depends('amount', 'interest_rate', 'term_sessions')
    def _compute_emi(self):
        for loan in self:
            if loan.amount > 0 and loan.interest_rate > 0 and loan.term_sessions > 0:
                # EMI calculation using reducing balance method (session-based)
                # Convert annual rate to per-session rate (assuming ~12 trading sessions per year)
                sessions_per_year = 12
                r = loan.interest_rate / (sessions_per_year * 100)  # Session interest rate
                n = loan.term_sessions
                
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
    
    @api.depends('payment_ids.payment_session_id', 'disbursement_session_id', 'status')
    def _compute_next_payment(self):
        for loan in self:
            if loan.status == 'active' and loan.disbursement_session_id:
                # For session-based loans, next payment is due next session
                last_payment = loan.payment_ids.sorted('payment_session_id', reverse=True)[:1]
                if last_payment and last_payment.payment_session_id:
                    # Find next session after last payment
                    next_session = self.env['stock.session'].search([
                        ('session_number', '>', last_payment.payment_session_id.session_number)
                    ], limit=1, order='session_number asc')
                    loan.next_payment_date = next_session.date if next_session else False
                else:
                    # First payment due next session after disbursement
                    next_session = self.env['stock.session'].search([
                        ('session_number', '>', loan.disbursement_session_id.session_number)
                    ], limit=1, order='session_number asc')
                    loan.next_payment_date = next_session.date if next_session else False
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
            
            # Use sudo to ensure proper access for fund transfers
            loan_sudo = loan.sudo()
            banker_sudo = loan_sudo.banker_id.sudo()
            user_sudo = loan_sudo.user_id.sudo()
            
            # Check bank has sufficient funds
            if banker_sudo.cash_balance < loan_sudo.amount:
                raise ValidationError(
                    f"Bank has insufficient funds. "
                    f"Available: {banker_sudo.cash_balance:.2f}, "
                    f"Required: {loan_sudo.amount:.2f}"
                )
            
            # Get active session
            active_session = self.env['stock.session'].search([
                ('state', '=', 'open')
            ], limit=1)
            
            # Block collateral if secured loan
            if loan_sudo.loan_type in ['margin', 'secured']:
                position = self.env['stock.position'].search([
                    ('user_id', '=', loan_sudo.user_id.id),
                    ('security_id', '=', loan_sudo.collateral_security_id.id)
                ], limit=1)
                
                if position:
                    position.block_shares(loan_sudo.collateral_quantity)
            
            # Transfer funds with sudo privileges
            banker_sudo.write({'cash_balance': banker_sudo.cash_balance - loan_sudo.amount})
            user_sudo.write({'cash_balance': user_sudo.cash_balance + loan_sudo.amount})
            
            loan_sudo.write({
                'status': 'active',
                'disbursement_session_id': active_session.id,
                'principal_outstanding': loan_sudo.amount
            })
            
            # Log the disbursement transaction
            self.env['stock.transaction.log'].log_transaction(
                user_id=loan.user_id.id,
                transaction_type='loan_disbursement',
                amount=loan.amount,
                cash_impact=loan.amount,
                description=f'Loan disbursement - {loan.loan_type}',
                session_id=active_session.id if active_session else False,
                loan_id=loan.id,
                reference=f'LOAN-{loan.name}',
                notes=f'Loan disbursed by banker {loan.banker_id.name}'
            )
            
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
    
    def _calculate_interest(self):
        """Calculate and apply interest for active loans (called at session end)"""
        self.ensure_one()
        
        if self.status != 'approved':
            return
        
        try:
            # Calculate accrued interest (session-based)
            if self.disbursement_session_id:
                current_session = self.env['stock.session'].search([('status', '=', 'active')], limit=1)
                if current_session and current_session.session_number > self.disbursement_session_id.session_number:
                    sessions_elapsed = current_session.session_number - self.disbursement_session_id.session_number
                    if sessions_elapsed > 0:
                        # Interest per session = (annual_rate / 12 sessions per year)
                        session_interest_rate = self.interest_rate / 12
                        interest = (self.amount * session_interest_rate * sessions_elapsed) / 100
                        new_outstanding = self.outstanding_balance + interest
                        
                        self.write({
                            'outstanding_balance': new_outstanding,
                            'total_interest': self.total_interest + interest,
                        })
                        
                        _logger.info(f"Loan {self.name}: Added {sessions_elapsed} sessions interest {interest:.2f}, new outstanding {new_outstanding:.2f}")
        except Exception as e:
            _logger.error(f"Error calculating interest for loan {self.name}: {str(e)}")
            raise


class StockLoanPayment(models.Model):
    _name = 'stock.loan.payment'
    _description = 'Loan Payment'
    _order = 'payment_session_id desc, payment_date desc'
    
    loan_id = fields.Many2one(
        'stock.loan',
        string='Loan',
        required=True,
        ondelete='cascade'
    )
    
    payment_session_id = fields.Many2one(
        'stock.session',
        string='Payment Session',
        required=True,
        help='Session when payment was made'
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
        
        # Log payment transactions
        current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
        
        # Log loan payment transaction
        self.env['stock.transaction.log'].log_transaction(
            user_id=payment.loan_id.user_id.id,
            transaction_type='loan_payment',
            amount=-payment.amount,
            cash_impact=-payment.amount,
            description=f'Loan payment - {payment.loan_id.loan_type}',
            session_id=current_session.id if current_session else False,
            loan_id=payment.loan_id.id,
            reference=f'PAY-{payment.loan_id.name}-{payment.id}',
            notes=f'Payment for loan #{payment.loan_id.name} (Principal: {payment.principal_component}, Interest: {payment.interest_component}, Penalty: {payment.penalty_component})'
        )
        
        # If there's interest, log it as separate interest expense
        if payment.interest_component > 0:
            self.env['stock.transaction.log'].log_transaction(
                user_id=payment.loan_id.user_id.id,
                transaction_type='loan_interest',
                amount=-payment.interest_component,
                cash_impact=0,  # Already accounted in the payment above
                description=f'Interest on loan - {payment.loan_id.loan_type}',
                session_id=current_session.id if current_session else False,
                loan_id=payment.loan_id.id,
                reference=f'INT-{payment.loan_id.name}-{payment.id}',
                notes=f'Interest component of payment for loan #{payment.loan_id.name}'
            )
        
        # If there's penalty, log it as separate fee
        if payment.penalty_component > 0:
            self.env['stock.transaction.log'].log_transaction(
                user_id=payment.loan_id.user_id.id,
                transaction_type='loan_penalty',
                amount=-payment.penalty_component,
                cash_impact=0,  # Already accounted in the payment above
                description=f'Penalty on loan - {payment.loan_id.loan_type}',
                session_id=current_session.id if current_session else False,
                loan_id=payment.loan_id.id,
                reference=f'PEN-{payment.loan_id.name}-{payment.id}',
                notes=f'Penalty component of payment for loan #{payment.loan_id.name}'
            )
        
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