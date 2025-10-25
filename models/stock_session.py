# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class StockSession(models.Model):
    _name = 'stock.session'
    _description = 'Stock Trading Session'
    _order = 'session_number desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'stock.message.mixin']
    
    name = fields.Char(
        string='Session Name',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        help='Auto-generated session number (e.g., Session 01)'
    )
    
    session_number = fields.Integer(
        string='Session Number',
        required=True,
        readonly=True,
        copy=False,
        help='Sequential session number for ordering and calculations'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('settled', 'Settled')
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Planned Timing (Optional - for scheduling)
    planned_start_date = fields.Datetime(
        string='Planned Start Date',
        tracking=True,
        help='Optional: Schedule when session should start (will auto-open at this time). Disabled once session is opened.'
    )
    
    planned_end_date = fields.Datetime(
        string='Planned End Date',
        tracking=True,
        help='Optional: Schedule when session should end (will auto-close at this time). Disabled once session is closed.'
    )
    
    # Actual Timing (Read-only - set by system)
    actual_start_date = fields.Datetime(
        string='Actual Start Date',
        readonly=True,
        tracking=True,
        help='Actual date/time when session was opened (set automatically)'
    )
    
    actual_end_date = fields.Datetime(
        string='Actual End Date',
        readonly=True,
        tracking=True,
        help='Actual date/time when session was closed (set automatically)'
    )
    
    # Session Duration
    planned_duration = fields.Float(
        string='Planned Duration (hours)',
        compute='_compute_planned_duration',
        store=True,
        help='Calculated from planned start/end dates'
    )
    
    actual_duration = fields.Float(
        string='Actual Duration (hours)',
        compute='_compute_actual_duration',
        store=True,
        help='Actual session duration calculated from actual start/end dates'
    )
    
    # Configuration
    price_change_threshold = fields.Float(
        string='Price Change Threshold (%)',
        default=20.0,
        digits=(16, 2),
        help='Percentage change required to update stock price'
    )
    
    broker_commission_rate = fields.Float(
        string='Broker Commission Rate (%)',
        default=0.5,
        digits=(16, 2),
        help='Default commission rate for brokers'
    )
    
    tick_size = fields.Float(
        string='Tick Size',
        default=0.01,
        digits=(16, 4),
        help='Minimum price increment'
    )
    
    circuit_breaker_upper = fields.Float(
        string='Circuit Breaker Upper Limit (%)',
        default=10.0,
        digits=(16, 2),
        help='Maximum allowed price increase in session'
    )
    
    circuit_breaker_lower = fields.Float(
        string='Circuit Breaker Lower Limit (%)',
        default=10.0,
        digits=(16, 2),
        help='Maximum allowed price decrease in session'
    )
    
    # Relationships
    order_ids = fields.One2many(
        'stock.order',
        'session_id',
        string='Orders'
    )
    
    trade_ids = fields.One2many(
        'stock.trade',
        'session_id',
        string='Trades'
    )
    
    # Statistics
    total_orders = fields.Integer(
        string='Total Orders',
        compute='_compute_statistics'
    )
    
    total_trades = fields.Integer(
        string='Total Trades',
        compute='_compute_statistics'
    )
    
    total_volume = fields.Float(
        string='Total Volume',
        compute='_compute_statistics',
        digits='Product Price'
    )
    
    total_value = fields.Float(
        string='Total Value Traded',
        compute='_compute_statistics',
        digits='Product Price'
    )
    
    @api.depends('order_ids', 'trade_ids')
    def _compute_statistics(self):
        for session in self:
            session.total_orders = len(session.order_ids)
            session.total_trades = len(session.trade_ids)
            session.total_volume = sum(trade.quantity for trade in session.trade_ids)
            session.total_value = sum(trade.quantity * trade.price for trade in session.trade_ids)
    
    @api.depends('planned_start_date', 'planned_end_date')
    def _compute_planned_duration(self):
        """Calculate planned session duration in hours"""
        for session in self:
            if session.planned_start_date and session.planned_end_date:
                duration = session.planned_end_date - session.planned_start_date
                session.planned_duration = duration.total_seconds() / 3600.0
            else:
                session.planned_duration = 0.0
    
    @api.depends('actual_start_date', 'actual_end_date')
    def _compute_actual_duration(self):
        """Calculate actual session duration in hours"""
        for session in self:
            if session.actual_start_date and session.actual_end_date:
                duration = session.actual_end_date - session.actual_start_date
                session.actual_duration = duration.total_seconds() / 3600.0
            else:
                session.actual_duration = 0.0
    
    @api.model
    def create(self, vals):
        """Auto-generate session name with serial number in format 'Session 01', 'Session 02', etc."""
        if not vals.get('name') or not vals.get('session_number'):
            # Get the last session number by searching for sessions with Session pattern
            last_session = self.search([
                ('name', 'like', 'Session %')
            ], order='id desc', limit=1)
            
            if last_session:
                try:
                    # Extract number from "Session 01", "Session 02", etc.
                    session_parts = last_session.name.split(' ')
                    if len(session_parts) >= 2:
                        last_num = int(session_parts[1])
                        new_num = last_num + 1
                    else:
                        new_num = 1
                except (ValueError, IndexError):
                    # If parsing fails, default to 1
                    new_num = 1
            else:
                new_num = 1
            
            if not vals.get('name'):
                vals['name'] = f'Session {new_num:02d}'
            if not vals.get('session_number'):
                vals['session_number'] = new_num
        
        return super(StockSession, self).create(vals)
    
    @api.model
    def _ensure_initial_session_exists(self):
        """Ensure at least one session exists in the system"""
        existing_sessions = self.search_count([])
        if existing_sessions == 0:
            # Create the first session
            self.create({
                'name': 'Session 01',
                'state': 'draft',
                'price_change_threshold': 10.0,
                'broker_commission_rate': 0.25,
                'tick_size': 0.01,
                'circuit_breaker_upper': 15.0,
                'circuit_breaker_lower': 15.0,
            })
            _logger.info("Created initial session: Session 01")
    
    def unlink(self):
        """Prevent deletion of all sessions - sessions cannot be deleted"""
        for session in self:
            raise UserError(
                f"Cannot delete session '{session.name}'. "
                "Trading sessions cannot be deleted to maintain audit trail and data integrity."
            )
        
        return super(StockSession, self).unlink()
    
    @api.constrains('planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date')
    def _check_dates(self):
        for session in self:
            # Validate planned dates
            if session.planned_start_date and session.planned_end_date:
                if session.planned_end_date <= session.planned_start_date:
                    raise ValidationError("Planned end date must be after planned start date.")
            
            # Validate actual dates
            if session.actual_start_date and session.actual_end_date:
                if session.actual_end_date <= session.actual_start_date:
                    raise ValidationError("Actual end date must be after actual start date.")
                
                # Check for overlapping sessions - only for open/closed sessions
                if session.state in ['open', 'closed']:
                    domain = [
                        ('id', '!=', session.id),
                        ('state', 'in', ['open']),
                        ('actual_start_date', '!=', False),
                        ('actual_end_date', '!=', False),
                        '|', '|', '|',
                        # New session starts within existing session
                        '&', ('actual_start_date', '<=', session.actual_start_date), ('actual_end_date', '>', session.actual_start_date),
                        # New session ends within existing session
                        '&', ('actual_start_date', '<', session.actual_end_date), ('actual_end_date', '>=', session.actual_end_date),
                        # New session completely contains existing session
                        '&', ('actual_start_date', '>=', session.actual_start_date), ('actual_end_date', '<=', session.actual_end_date),
                        # Existing session completely contains new session
                        '&', ('actual_start_date', '<=', session.actual_start_date), ('actual_end_date', '>=', session.actual_end_date),
                    ]
                    if self.search_count(domain) > 0:
                        raise ValidationError("Session dates overlap with another open session.")
    
    def action_open_session(self):
        """Open the trading session - sets actual_start_date to NOW"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Only draft sessions can be opened.")
        
        # Set actual start date to current time
        now = fields.Datetime.now()
        
        # Set session start prices for all active securities
        # Matches C#: "SELECT Row_ID, price FROM stocks WHERE status<>'liquidated'"
        active_securities = self.env['stock.security'].search([
            ('active', '=', True)
        ])
        
        for security in active_securities:
            # Update both session_start_price AND price_to_compare_with
            # Matches C#: sessionStartPrice={0}, PriceToCompareWith={0}
            security.write({
                'session_start_price': security.current_price,
                'price_to_compare_with': security.current_price,
            })
        
        # Update session status and actual start date
        self.write({
            'state': 'open',
            'actual_start_date': now,
        })
        
        # Log the action using centralized method
        self.log_action("Session started", f"Started at {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        _logger.info(f"Session {self.name} started at {now} - Updated {len(active_securities)} securities")
    
    def action_close_session(self):
        """Close the trading session - sets actual_end_date to NOW"""
        self.ensure_one()
        if self.state != 'open':
            raise UserError("Only open sessions can be closed.")
        
        # Check if there are IPO/PO securities that need attention
        ipo_securities = self.env['stock.security'].search([
            ('status', 'in', ['ipo', 'po'])
        ])
        
        if ipo_securities:
            # Launch IPO management wizard before closing session
            return {
                'type': 'ir.actions.act_window',
                'name': 'Manage IPO Securities',
                'res_model': 'session.end.ipo.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'active_id': self.id}
            }
        
        # No IPO securities, proceed with normal session close
        return self._perform_session_close()
    
    def _perform_session_close(self):
        """Perform the actual session close operations"""
        self.ensure_one()
        
        # Set actual end date to current time
        now = fields.Datetime.now()
        
        # Handle any orphaned submitted orders for securities that are now trading
        # This covers cases where securities were manually changed to trading status
        self._handle_orphaned_submitted_orders()
        
        # Cancel all pending orders EXCEPT IPO orders (they carry over)
        pending_orders = self.order_ids.filtered(
            lambda o: o.status in ['draft', 'pending', 'partial'] and o.order_type != 'ipo'
        )
        for order in pending_orders:
            order.action_cancel()
            
        # Log IPO orders that are carrying over
        ipo_orders = self.order_ids.filtered(
            lambda o: o.status in ['submitted', 'open'] and o.order_type == 'ipo'
        )
        if ipo_orders:
            _logger.info(f"Session {self.name}: {len(ipo_orders)} IPO orders carrying over to next session")
        
        # Record price history snapshots for all active securities
        # Matches C#: Insert into stockpricehistory/bondpricehistory
        active_securities = self.env['stock.security'].search([
            ('active', '=', True)
        ])
        
        price_history_obj = self.env['stock.price.history']
        history_count = 0
        
        for security in active_securities:
            # Create price history record for this session end
            price_history_obj.create({
                'security_id': security.id,
                'session_id': self.id,
                'old_price': security.session_start_price or security.current_price,
                'new_price': security.current_price,
                'change_date': now,
                'change_reason': 'session_end',
            })
            
            # Update session start price and price to compare with for next session
            # Matches C#: sessionStartPrice={0}, PriceToCompareWith={0}
            security.write({
                'session_start_price': security.current_price,
                'price_to_compare_with': security.current_price,
                'previous_close': security.current_price,
            })
            history_count += 1
        
        # Process interest calculations for deposits and loans
        self._process_session_interest()
        
        # Update session status and actual end date
        self.write({
            'state': 'closed',
            'actual_end_date': now,
        })
        
        # Calculate session duration
        if self.actual_start_date:
            duration = (now - self.actual_start_date).total_seconds() / 3600.0
            duration_str = f"{duration:.2f} hours"
        else:
            duration_str = "unknown"
        
        # Log the action (matches C# news system)
        self.log_action("Session ended", f"Ended at {now.strftime('%Y-%m-%d %H:%M:%S')} - Duration: {duration_str} - Recorded {history_count} price snapshots")
        
        # Auto-create next session (always enabled)
        next_session = self._create_next_session()
        
        _logger.info(f"Session {self.name} closed at {now} (duration: {duration_str}) - Recorded {history_count} price snapshots - Created next session: {next_session.name}")
        
        return True  # Return success for wizard completion
    
    def action_force_close_after_ipo(self):
        """Force close session after IPO wizard completion"""
        return self._perform_session_close()
    
    def _handle_orphaned_submitted_orders(self):
        """Handle submitted orders for securities that are now in trading status"""
        self.ensure_one()
        
        # Find submitted orders for securities that are now trading
        submitted_orders = self.env['stock.order'].search([
            ('status', '=', 'submitted'),
            ('security_id.status', '=', 'trade')  # Security is now trading
        ])
        
        if submitted_orders:
            _logger.info(f"Found {len(submitted_orders)} submitted orders for trading securities - promoting to open")
            
            for order in submitted_orders:
                if order.order_type == 'ipo':
                    # IPO orders for trading securities should be cancelled/rejected
                    order.write({
                        'status': 'rejected',
                        'rejection_reason': 'IPO order for security that is already trading'
                    })
                    order.log_action("Order rejected", "IPO order rejected - security already trading")
                else:
                    # Regular orders should be promoted to open
                    order.write({'status': 'open'})
                    order.log_action("Order promoted", "Promoted from Submitted to Open - security now trading")
    
    @api.model 
    def cleanup_orphaned_orders(self):
        """Utility method to clean up orphaned submitted orders across all sessions"""
        # Find submitted orders for securities that are now trading
        submitted_orders = self.env['stock.order'].search([
            ('status', '=', 'submitted'),
            ('security_id.status', '=', 'trade')  # Security is now trading
        ])
        
        if submitted_orders:
            _logger.info(f"Cleanup: Found {len(submitted_orders)} submitted orders for trading securities")
            
            for order in submitted_orders:
                if order.order_type == 'ipo':
                    # IPO orders for trading securities should be cancelled/rejected
                    order.write({
                        'status': 'rejected',
                        'rejection_reason': 'IPO order for security that is already trading'
                    })
                    order.log_action("Order rejected", "IPO order rejected - security already trading (cleanup)")
                else:
                    # Regular orders should be promoted to open
                    order.write({'status': 'open'})
                    order.log_action("Order promoted", "Promoted from Submitted to Open - security now trading (cleanup)")
            
            return f"Cleaned up {len(submitted_orders)} orphaned orders"
        else:
            return "No orphaned orders found"
    
    def _process_session_interest(self):
        """Process interest calculations for deposits and loans at session end"""
        self.ensure_one()
        
        # Process deposit interest
        active_deposits = self.env['stock.deposit'].search([
            ('status', '=', 'approved')
        ])
        
        for deposit in active_deposits:
            try:
                deposit._calculate_interest()
            except Exception as e:
                _logger.error(f"Error calculating interest for deposit {deposit.id}: {str(e)}")
        
        # Process loan interest
        active_loans = self.env['stock.loan'].search([
            ('status', '=', 'approved')
        ])
        
        for loan in active_loans:
            try:
                loan._calculate_interest()
            except Exception as e:
                _logger.error(f"Error calculating interest for loan {loan.id}: {str(e)}")
        
        _logger.info(f"Processed interest for {len(active_deposits)} deposits and {len(active_loans)} loans")
    
    def _create_next_session(self):
        """Auto-create the next session (draft state, no dates set)"""
        self.ensure_one()
        
        # Create next session with same configuration as current session
        # Name will be auto-generated by create method (Session 02, Session 03, etc.)
        next_session = self.create({
            'state': 'draft',
            'planned_duration': self.planned_duration or 8.0,  # Default 8 hours
            'price_change_threshold': self.price_change_threshold or 10.0,
            'broker_commission_rate': self.broker_commission_rate or 0.25,
            'tick_size': self.tick_size or 0.01,
            'circuit_breaker_upper': self.circuit_breaker_upper or 15.0,
            'circuit_breaker_lower': self.circuit_breaker_lower or 15.0,
        })
        
        _logger.info(f"Auto-created next session: {next_session.name}")
        
        return next_session
    
    def action_settle_session(self):
        """Settle all trades in the session"""
        self.ensure_one()
        if self.state != 'closed':
            raise UserError("Only closed sessions can be settled.")
        
        # Perform any final settlement tasks
        # In this simulation, trades are settled immediately, so this is mainly for workflow
        
        self.state = 'settled'
        
        # Generate session report
        self._generate_session_report()
        
        # Log the action using centralized method
        self.log_action("Session settled", "Trading session settlement completed")
    
    def _generate_session_report(self):
        """Generate end-of-session report"""
        # This would generate comprehensive reports for all participants
        # Implementation depends on reporting requirements
        pass
    
    @api.model
    def cron_check_session_times(self):
        """Cron job to auto-open/close sessions based on planned dates"""
        now = fields.Datetime.now()
        
        # Auto-open sessions whose planned start time has arrived
        sessions_to_open = self.search([
            ('state', '=', 'draft'),
            ('planned_start_date', '!=', False),
            ('planned_start_date', '<=', now),
        ])
        
        for session in sessions_to_open:
            try:
                session.action_open_session()
                _logger.info(f"Auto-opened session {session.name} at planned start time {session.planned_start_date}")
            except Exception as e:
                _logger.error(f"Failed to auto-open session {session.name}: {str(e)}")
        
        # Auto-close sessions whose planned end time has arrived
        sessions_to_close = self.search([
            ('state', '=', 'open'),
            ('planned_end_date', '!=', False),
            ('planned_end_date', '<=', now),
        ])
        
        for session in sessions_to_close:
            try:
                session.action_close_session()
                _logger.info(f"Auto-closed session {session.name} at planned end time {session.planned_end_date}")
            except Exception as e:
                _logger.error(f"Failed to auto-close session {session.name}: {str(e)}")
    
    def action_view_orders(self):
        """View all orders in this session"""
        self.ensure_one()
        return {
            'name': f'Orders - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.order',
            'view_mode': 'list,form',
            'domain': [('session_id', '=', self.id)],
            'context': {'default_session_id': self.id}
        }
    
    def action_view_trades(self):
        """View all trades in this session"""
        self.ensure_one()
        return {
            'name': f'Trades - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.trade',
            'view_mode': 'list,form',
            'domain': [('session_id', '=', self.id)],
            'context': {'default_session_id': self.id}
        } 