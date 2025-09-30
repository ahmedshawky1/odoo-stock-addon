# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class StockSession(models.Model):
    _name = 'stock.session'
    _description = 'Stock Trading Session'
    _order = 'start_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(
        string='Session Name',
        required=True,
        tracking=True,
        help='Unique name for this trading session'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('settled', 'Settled')
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Timing
    start_date = fields.Datetime(
        string='Start Date',
        required=True,
        tracking=True,
        help='When trading starts'
    )
    
    end_date = fields.Datetime(
        string='End Date',
        required=True,
        tracking=True,
        help='When trading ends'
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
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for session in self:
            if session.end_date <= session.start_date:
                raise ValidationError("End date must be after start date.")
            
            # Check for overlapping sessions - comprehensive check
            domain = [
                ('id', '!=', session.id),
                ('state', 'in', ['open', 'closed']),
                '|', '|', '|',
                # New session starts within existing session
                '&', ('start_date', '<=', session.start_date), ('end_date', '>', session.start_date),
                # New session ends within existing session
                '&', ('start_date', '<', session.end_date), ('end_date', '>=', session.end_date),
                # New session completely contains existing session
                '&', ('start_date', '>=', session.start_date), ('end_date', '<=', session.end_date),
                # Existing session completely contains new session
                '&', ('start_date', '<=', session.start_date), ('end_date', '>=', session.end_date),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError("Session dates overlap with another session.")
    
    def action_open_session(self):
        """Open the trading session"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("Only draft sessions can be opened.")
        
        # Set session start prices for all securities
        securities = self.env['stock.security'].search([])
        for security in securities:
            security.session_start_price = security.current_price
        
        self.state = 'open'
        
        # Log the action
        self.message_post(body=f"Trading session opened at {fields.Datetime.now()}")
    
    def action_close_session(self):
        """Close the trading session"""
        self.ensure_one()
        if self.state != 'open':
            raise UserError("Only open sessions can be closed.")
        
        # Cancel all pending orders
        pending_orders = self.order_ids.filtered(lambda o: o.status in ['draft', 'pending', 'partial'])
        for order in pending_orders:
            order.action_cancel()
        
        self.state = 'closed'
        
        # Log the action
        self.message_post(body=f"Trading session closed at {fields.Datetime.now()}")
    
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
        
        # Log the action
        self.message_post(body=f"Trading session settled at {fields.Datetime.now()}")
    
    def _generate_session_report(self):
        """Generate end-of-session report"""
        # This would generate comprehensive reports for all participants
        # Implementation depends on reporting requirements
        pass
    
    @api.model
    def cron_check_session_times(self):
        """Cron job to automatically open/close sessions based on time"""
        now = fields.Datetime.now()
        
        # Auto-open sessions
        sessions_to_open = self.search([
            ('state', '=', 'draft'),
            ('start_date', '<=', now)
        ])
        for session in sessions_to_open:
            try:
                session.action_open_session()
            except Exception as e:
                session.message_post(body=f"Failed to auto-open session: {str(e)}")
        
        # Auto-close sessions
        sessions_to_close = self.search([
            ('state', '=', 'open'),
            ('end_date', '<=', now)
        ])
        for session in sessions_to_close:
            try:
                session.action_close_session()
            except Exception as e:
                session.message_post(body=f"Failed to auto-close session: {str(e)}")
    
    def action_view_orders(self):
        """View all orders in this session"""
        self.ensure_one()
        return {
            'name': f'Orders - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.order',
            'view_mode': 'tree,form',
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
            'view_mode': 'tree,form',
            'domain': [('session_id', '=', self.id)],
            'context': {'default_session_id': self.id}
        } 