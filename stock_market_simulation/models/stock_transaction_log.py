# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class StockTransactionLog(models.Model):
    _name = 'stock.transaction.log'
    _description = 'Stock Market Transaction Log'
    _order = 'transaction_date desc, id desc'
    _rec_name = 'description'

    # Basic Transaction Info
    transaction_date = fields.Datetime(
        string='Transaction Date',
        required=True,
        default=fields.Datetime.now,
        help='When the transaction occurred'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        help='User affected by this transaction'
    )
    
    session_id = fields.Many2one(
        'stock.session',
        string='Session',
        help='Trading session when transaction occurred'
    )
    
    # Transaction Classification
    transaction_type = fields.Selection([
        # Cash movements
        ('initial_capital', 'Initial Capital'),
        ('deposit_investment', 'Deposit Investment'),
        ('deposit_withdrawal', 'Deposit Withdrawal'),
        ('deposit_interest', 'Deposit Interest'),
        ('loan_disbursement', 'Loan Disbursement'),
        ('loan_payment', 'Loan Payment'),
        ('loan_interest', 'Loan Interest'),
        ('loan_penalty', 'Loan Penalty'),
        
        # Trading transactions
        ('stock_purchase', 'Stock Purchase'),
        ('stock_sale', 'Stock Sale'),
        ('broker_commission_buy', 'Broker Commission (Buy)'),
        ('broker_commission_sell', 'Broker Commission (Sell)'),
        ('trading_fee', 'Trading Fee'),
        
        # IPO transactions
        ('ipo_allocation', 'IPO Allocation'),
        ('ipo_payment', 'IPO Payment'),
        
        # Other
        ('dividend', 'Dividend Payment'),
        ('interest_payment', 'Interest Payment'),
        ('fee', 'Fee'),
        ('adjustment', 'Balance Adjustment'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
    ], string='Transaction Type', required=True, help='Type of transaction')
    
    category = fields.Selection([
        ('cash_inflow', 'Cash Inflow'),
        ('cash_outflow', 'Cash Outflow'),
        ('stock_purchase', 'Stock Purchase'),
        ('stock_sale', 'Stock Sale'),
        ('fees_commissions', 'Fees & Commissions'),
        ('interest_income', 'Interest Income'),
        ('interest_expense', 'Interest Expense'),
        ('deposit_banking', 'Deposit Banking'),
        ('loan_banking', 'Loan Banking'),
        ('ipo_activity', 'IPO Activity'),
        ('adjustment', 'Adjustment'),
    ], string='Category', required=True, compute='_compute_category', store=True, readonly=False)
    
    # Amounts
    amount = fields.Float(
        string='Amount',
        required=True,
        help='Transaction amount (positive for inflows, negative for outflows)'
    )
    
    cash_impact = fields.Float(
        string='Cash Impact',
        required=True,
        help='Impact on cash balance (positive increases cash, negative decreases cash)'
    )
    
    running_balance = fields.Float(
        string='Running Cash Balance',
        help='Cash balance after this transaction'
    )
    
    # Description and Reference
    description = fields.Text(
        string='Description',
        required=True,
        help='Detailed description of the transaction'
    )
    
    reference = fields.Char(
        string='Reference',
        help='Reference number or external identifier'
    )
    
    # Related Records
    order_id = fields.Many2one('stock.order', string='Related Order')
    trade_id = fields.Many2one('stock.trade', string='Related Trade')
    deposit_id = fields.Many2one('stock.deposit', string='Related Deposit')
    loan_id = fields.Many2one('stock.loan', string='Related Loan')
    security_id = fields.Many2one('stock.security', string='Related Security')
    
    # Additional Details
    quantity = fields.Float(string='Quantity', help='Quantity of shares for stock transactions')
    price = fields.Float(string='Price per Share', help='Price per share for stock transactions')
    
    # Metadata
    entered_by_id = fields.Many2one('res.users', string='Entered By', default=lambda self: self.env.user)
    notes = fields.Text(string='Notes')
    
    @api.depends('transaction_type')
    def _compute_category(self):
        """Automatically determine category based on transaction type"""
        category_mapping = {
            'initial_capital': 'cash_inflow',
            'deposit_investment': 'deposit_banking',
            'deposit_withdrawal': 'deposit_banking',
            'deposit_interest': 'interest_income',
            'loan_disbursement': 'loan_banking',
            'loan_payment': 'loan_banking',
            'loan_interest': 'interest_expense',
            'loan_penalty': 'interest_expense',
            'stock_purchase': 'stock_purchase',
            'stock_sale': 'stock_sale',
            'broker_commission_buy': 'fees_commissions',
            'broker_commission_sell': 'fees_commissions',
            'trading_fee': 'fees_commissions',
            'ipo_allocation': 'ipo_activity',
            'ipo_payment': 'ipo_activity',
            'dividend': 'interest_income',
            'interest_payment': 'interest_income',
            'fee': 'fees_commissions',
            'adjustment': 'adjustment',
            'transfer_in': 'cash_inflow',
            'transfer_out': 'cash_outflow',
        }
        
        for record in self:
            record.category = category_mapping.get(record.transaction_type, 'adjustment')
    
    @api.model
    def log_transaction(self, user_id, transaction_type, amount, cash_impact, description, **kwargs):
        """
        Central method to log a transaction
        
        Args:
            user_id (int): User ID affected by transaction
            transaction_type (str): Type of transaction (see selection options)
            amount (float): Transaction amount
            cash_impact (float): Impact on cash balance
            description (str): Transaction description
            **kwargs: Additional fields (session_id, order_id, trade_id, etc.)
        
        Returns:
            stock.transaction.log: Created transaction record
        """
        try:
            # Get user to update running balance
            user = self.env['res.users'].browse(user_id)
            if not user.exists():
                raise ValidationError(f"User {user_id} not found")
            
            # Map transaction type to category
            category_mapping = {
                'initial_capital': 'cash_inflow',
                'deposit_investment': 'deposit_banking',
                'deposit_withdrawal': 'deposit_banking',
                'deposit_interest': 'interest_income',
                'loan_disbursement': 'loan_banking',
                'loan_payment': 'loan_banking',
                'loan_interest': 'interest_expense',
                'loan_penalty': 'interest_expense',
                'stock_purchase': 'stock_purchase',
                'stock_sale': 'stock_sale',
                'broker_commission_buy': 'fees_commissions',
                'broker_commission_sell': 'fees_commissions',
                'trading_fee': 'fees_commissions',
                'ipo_allocation': 'ipo_activity',
                'ipo_payment': 'ipo_activity',
                'dividend': 'interest_income',
                'interest_payment': 'interest_income',
                'fee': 'fees_commissions',
                'adjustment': 'adjustment',
                'transfer_in': 'cash_inflow',
                'transfer_out': 'cash_outflow',
            }
            
            # Get the current running balance from the last transaction (race condition safe)
            last_transaction = self.search([
                ('user_id', '=', user_id)
            ], order='transaction_date desc, id desc', limit=1)
            
            if last_transaction:
                current_balance = last_transaction.running_balance
            else:
                # No previous transactions, use user's current cash balance
                current_balance = user.cash_balance or 0
            
            # Prepare transaction data
            vals = {
                'user_id': user_id,
                'transaction_type': transaction_type,
                'category': category_mapping.get(transaction_type, 'adjustment'),
                'amount': amount,
                'cash_impact': cash_impact,
                'description': description,
                'transaction_date': kwargs.get('transaction_date', fields.Datetime.now()),
                'running_balance': current_balance + cash_impact,
            }
            
            # Add optional fields
            optional_fields = [
                'session_id', 'order_id', 'trade_id', 'deposit_id', 'loan_id', 
                'security_id', 'quantity', 'price', 'reference', 'notes', 'entered_by_id'
            ]
            
            for field in optional_fields:
                if field in kwargs:
                    vals[field] = kwargs[field]
            
            # Create transaction log with savepoint for atomicity
            with self.env.cr.savepoint():
                transaction = self.create(vals)
                
                # Update user's cash balance with the correct running balance
                user.write({'cash_balance': vals['running_balance']})
                
                # Validate balance consistency after update
                user._invalidate_cache()  # Ensure we have the latest data
                if abs(user.cash_balance - vals['running_balance']) > 0.01:
                    _logger.warning(f"Balance inconsistency detected for user {user.name}: user.cash_balance={user.cash_balance}, transaction.running_balance={vals['running_balance']}")
                    user.write({'cash_balance': vals['running_balance']})  # Force sync
                
                _logger.info(f"Transaction logged: {transaction_type} for user {user.name}, amount: {cash_impact}, new balance: {vals['running_balance']}")
                
                return transaction
            
        except Exception as e:
            _logger.error(f"Error logging transaction: {str(e)}")
            raise ValidationError(f"Failed to log transaction: {str(e)}")
    
    @api.model
    def validate_and_fix_cash_balances(self, user_ids=None):
        """
        Validate and fix cash balance inconsistencies for users
        
        Args:
            user_ids (list): List of user IDs to check, if None checks all users with transactions
            
        Returns:
            dict: Results of validation and fixes
        """
        if user_ids is None:
            # Get all users who have transactions
            users_with_transactions = self.search([]).mapped('user_id')
            user_ids = users_with_transactions.ids
        
        results = {
            'checked': 0,
            'fixed': 0,
            'inconsistencies': []
        }
        
        for user_id in user_ids:
            user = self.env['res.users'].browse(user_id)
            if not user.exists():
                continue
                
            # Get the latest transaction for this user
            latest_transaction = self.search([
                ('user_id', '=', user_id)
            ], order='transaction_date desc, id desc', limit=1)
            
            if latest_transaction:
                expected_balance = latest_transaction.running_balance
                current_balance = user.cash_balance
                
                results['checked'] += 1
                
                if abs(current_balance - expected_balance) > 0.01:
                    # Found inconsistency
                    inconsistency = {
                        'user': user.name,
                        'user_id': user_id,
                        'current_balance': current_balance,
                        'expected_balance': expected_balance,
                        'difference': current_balance - expected_balance
                    }
                    results['inconsistencies'].append(inconsistency)
                    
                    # Fix the balance
                    user.write({'cash_balance': expected_balance})
                    results['fixed'] += 1
                    
                    _logger.warning(f"Fixed balance inconsistency for user {user.name}: {current_balance} -> {expected_balance}")
        
        return results

    @api.model
    def get_user_balance_sheet(self, user_id, date_from=None, date_to=None):
        """
        Get complete balance sheet for a user
        
        Args:
            user_id (int): User ID
            date_from (datetime): Start date filter
            date_to (datetime): End date filter
            
        Returns:
            dict: Balance sheet data with categorized transactions
        """
        domain = [('user_id', '=', user_id)]
        
        if date_from:
            domain.append(('transaction_date', '>=', date_from))
        if date_to:
            domain.append(('transaction_date', '<=', date_to))
        
        transactions = self.search(domain, order='transaction_date, id')
        
        # Categorize transactions
        categories = {}
        total_inflows = 0
        total_outflows = 0
        
        for txn in transactions:
            category = txn.category
            if category not in categories:
                categories[category] = {
                    'transactions': [],
                    'total_amount': 0,
                    'total_cash_impact': 0,
                }
            
            categories[category]['transactions'].append(txn)
            categories[category]['total_amount'] += txn.amount
            categories[category]['total_cash_impact'] += txn.cash_impact
            
            if txn.cash_impact > 0:
                total_inflows += txn.cash_impact
            else:
                total_outflows += abs(txn.cash_impact)
        
        return {
            'transactions': transactions,
            'categories': categories,
            'total_inflows': total_inflows,
            'total_outflows': total_outflows,
            'net_change': total_inflows - total_outflows,
            'final_balance': transactions[-1].running_balance if transactions else 0,
        }
    
    @api.model
    def migrate_existing_data(self):
        """
        Migrate existing trades, deposits, loans to transaction log
        This should be run once when implementing the transaction log system
        """
        _logger.info("Starting migration of existing data to transaction log...")
        
        # Get all users with financial activity
        users = self.env['res.users'].search([('user_type', 'in', ['investor', 'banker', 'admin'])])
        
        for user in users:
            _logger.info(f"Migrating data for user: {user.name}")
            
            # Log initial capital if not already logged
            existing_initial = self.search([
                ('user_id', '=', user.id),
                ('transaction_type', '=', 'initial_capital')
            ], limit=1)
            
            if not existing_initial and user.initial_capital:
                self.log_transaction(
                    user_id=user.id,
                    transaction_type='initial_capital',
                    amount=user.initial_capital,
                    cash_impact=user.initial_capital,
                    description=f'Initial capital allocation',
                    transaction_date=user.create_date or fields.Datetime.now(),
                    reference='MIGRATION'
                )
            
            # Migrate trades
            trades = self.env['stock.trade'].search([
                '|', ('buyer_id', '=', user.id), ('seller_id', '=', user.id)
            ])
            
            for trade in trades:
                # Check if already migrated
                existing = self.search([
                    ('trade_id', '=', trade.id),
                    ('user_id', '=', user.id)
                ], limit=1)
                
                if existing:
                    continue
                
                if trade.buyer_id.id == user.id:
                    # Stock purchase
                    self.log_transaction(
                        user_id=user.id,
                        transaction_type='stock_purchase',
                        amount=-(trade.quantity * trade.price),
                        cash_impact=-(trade.quantity * trade.price),
                        description=f'Purchased {trade.quantity} shares of {trade.security_id.symbol} at ${trade.price:.2f}',
                        transaction_date=trade.trade_date,
                        trade_id=trade.id,
                        security_id=trade.security_id.id,
                        quantity=trade.quantity,
                        price=trade.price,
                        session_id=trade.session_id.id if trade.session_id else None,
                        reference=f'TRADE-{trade.id}'
                    )
                    
                    # Broker commission on buy
                    if trade.buy_commission > 0:
                        self.log_transaction(
                            user_id=user.id,
                            transaction_type='broker_commission_buy',
                            amount=-trade.buy_commission,
                            cash_impact=-trade.buy_commission,
                            description=f'Broker commission on purchase of {trade.security_id.symbol}',
                            transaction_date=trade.trade_date,
                            trade_id=trade.id,
                            security_id=trade.security_id.id,
                            reference=f'COMM-BUY-{trade.id}'
                        )
                
                if trade.seller_id.id == user.id:
                    # Stock sale
                    self.log_transaction(
                        user_id=user.id,
                        transaction_type='stock_sale',
                        amount=trade.quantity * trade.price,
                        cash_impact=trade.quantity * trade.price,
                        description=f'Sold {trade.quantity} shares of {trade.security_id.symbol} at ${trade.price:.2f}',
                        transaction_date=trade.trade_date,
                        trade_id=trade.id,
                        security_id=trade.security_id.id,
                        quantity=trade.quantity,
                        price=trade.price,
                        session_id=trade.session_id.id if trade.session_id else None,
                        reference=f'TRADE-{trade.id}'
                    )
                    
                    # Broker commission on sell
                    if trade.sell_commission > 0:
                        self.log_transaction(
                            user_id=user.id,
                            transaction_type='broker_commission_sell',
                            amount=-trade.sell_commission,
                            cash_impact=-trade.sell_commission,
                            description=f'Broker commission on sale of {trade.security_id.symbol}',
                            transaction_date=trade.trade_date,
                            trade_id=trade.id,
                            security_id=trade.security_id.id,
                            reference=f'COMM-SELL-{trade.id}'
                        )
            
            # Migrate deposits
            deposits = self.env['stock.deposit'].search([('user_id', '=', user.id)])
            for deposit in deposits:
                # Check if already migrated
                existing = self.search([
                    ('deposit_id', '=', deposit.id),
                    ('transaction_type', 'in', ['deposit_investment', 'deposit_withdrawal', 'deposit_interest'])
                ], limit=1)
                
                if existing:
                    continue
                
                # Deposit investment
                if deposit.status in ['active', 'matured', 'withdrawn']:
                    self.log_transaction(
                        user_id=user.id,
                        transaction_type='deposit_investment',
                        amount=-deposit.amount,
                        cash_impact=-deposit.amount,
                        description=f'Deposit investment - {deposit.deposit_type}',
                        transaction_date=deposit.create_date,
                        deposit_id=deposit.id,
                        reference=f'DEP-{deposit.id}'
                    )
                
                # Interest earned (if any)
                if hasattr(deposit, 'accrued_interest') and deposit.accrued_interest > 0:
                    self.log_transaction(
                        user_id=user.id,
                        transaction_type='deposit_interest',
                        amount=deposit.accrued_interest,
                        cash_impact=deposit.accrued_interest,
                        description=f'Interest earned on deposit - {deposit.deposit_type}',
                        transaction_date=deposit.write_date or deposit.create_date,
                        deposit_id=deposit.id,
                        reference=f'INT-DEP-{deposit.id}'
                    )
            
            # Migrate loans
            loans = self.env['stock.loan'].search([('user_id', '=', user.id)])
            for loan in loans:
                # Check if already migrated
                existing = self.search([
                    ('loan_id', '=', loan.id),
                    ('transaction_type', 'in', ['loan_disbursement', 'loan_payment', 'loan_interest'])
                ], limit=1)
                
                if existing:
                    continue
                
                # Loan disbursement
                if loan.status in ['active', 'paid', 'defaulted']:
                    self.log_transaction(
                        user_id=user.id,
                        transaction_type='loan_disbursement',
                        amount=loan.amount,
                        cash_impact=loan.amount,
                        description=f'Loan disbursement - {loan.loan_type}',
                        transaction_date=loan.create_date,
                        loan_id=loan.id,
                        reference=f'LOAN-{loan.id}'
                    )
                
                # Interest charges (if any)
                if hasattr(loan, 'interest_accrued') and loan.interest_accrued > 0:
                    self.log_transaction(
                        user_id=user.id,
                        transaction_type='loan_interest',
                        amount=-loan.interest_accrued,
                        cash_impact=-loan.interest_accrued,
                        description=f'Interest on loan - {loan.loan_type}',
                        transaction_date=loan.write_date or loan.create_date,
                        loan_id=loan.id,
                        reference=f'INT-LOAN-{loan.id}'
                    )
        
        _logger.info("Migration completed successfully")
        return True
    
    @api.model
    def validate_and_fix_cash_balances(self):
        """
        Validate and fix cash balance discrepancies between user records and transaction log
        
        Returns:
            dict: Summary of fixes applied
        """
        _logger.info("Starting cash balance validation and fix...")
        
        # Get all users with transaction logs
        users_with_transactions = self.env['res.users'].search([
            ('id', 'in', self.search([]).mapped('user_id.id'))
        ])
        
        fixes_applied = []
        total_users = len(users_with_transactions)
        
        for user in users_with_transactions:
            # Get latest transaction for this user
            latest_txn = self.search([('user_id', '=', user.id)], order='id desc', limit=1)
            
            if latest_txn:
                expected_balance = latest_txn.running_balance
                actual_balance = user.cash_balance
                
                if abs(expected_balance - actual_balance) > 0.01:  # Allow for small floating point differences
                    _logger.warning(f"Balance discrepancy for user {user.name}: user.cash_balance={actual_balance}, expected={expected_balance}")
                    
                    # Fix the discrepancy
                    user.write({'cash_balance': expected_balance})
                    
                    fixes_applied.append({
                        'user_id': user.id,
                        'user_name': user.name,
                        'old_balance': actual_balance,
                        'new_balance': expected_balance,
                        'difference': expected_balance - actual_balance
                    })
        
        summary = {
            'total_users_checked': total_users,
            'fixes_applied': len(fixes_applied),
            'fixes_details': fixes_applied
        }
        
        _logger.info(f"Cash balance validation completed. Checked {total_users} users, applied {len(fixes_applied)} fixes")
        
        return summary