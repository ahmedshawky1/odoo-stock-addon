# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class StockUserBlock(models.Model):
    _name = 'stock.user.block'
    _description = 'User Blocking System'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Identity
    name = fields.Char(
        string='Block Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('stock.user.block') or 'New'
    )
    
    # User being blocked
    user_id = fields.Many2one(
        'res.users',
        string='Blocked User',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Block Details
    block_type = fields.Selection([
        ('time', 'Time-based Block'),
        ('session', 'Session-based Block')
    ], string='Block Type', required=True, default='time', tracking=True)
    
    block_reason = fields.Selection([
        ('trading_violation', 'Violation of Trading Rules'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('non_payment', 'Non-payment of Obligations'),
        ('system_abuse', 'System Abuse'),
        ('administrative', 'Administrative Purposes'),
        ('other', 'Other')
    ], string='Block Reason', required=True, tracking=True)
    
    custom_reason = fields.Text(
        string='Custom Reason',
        help='Additional details about the block reason'
    )
    
    # Time-based blocking
    blocked_from_date = fields.Datetime(
        string='Blocked From',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    
    blocked_to_date = fields.Datetime(
        string='Blocked Until',
        tracking=True,
        help='For time-based blocks: when the block expires'
    )
    
    duration_minutes = fields.Integer(
        string='Duration (Minutes)',
        help='Duration in minutes for time-based blocks'
    )
    
    # Session-based blocking
    blocked_until_session = fields.Integer(
        string='Blocked Until Session',
        help='For session-based blocks: session number when block expires'
    )
    
    # Status
    status = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='active', tracking=True, index=True)
    
    # Admin who created the block
    blocked_by_id = fields.Many2one(
        'res.users',
        string='Blocked By',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )
    
    # Automatic expiry tracking
    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_is_expired',
        store=True
    )
    
    remaining_time = fields.Char(
        string='Remaining Time',
        compute='_compute_remaining_time'
    )
    
    @api.depends('block_type', 'blocked_to_date', 'blocked_until_session', 'status')
    def _compute_is_expired(self):
        for block in self:
            if block.status != 'active':
                block.is_expired = True
                continue
                
            if block.block_type == 'time':
                if block.blocked_to_date and block.blocked_to_date <= fields.Datetime.now():
                    block.is_expired = True
                else:
                    block.is_expired = False
            elif block.block_type == 'session':
                if block.blocked_until_session:
                    # Get current session number
                    current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
                    if current_session:
                        session_num = int(current_session.name.split(' ')[-1]) if current_session.name.startswith('Session ') else 0
                        block.is_expired = session_num >= block.blocked_until_session
                    else:
                        block.is_expired = False
                else:
                    block.is_expired = False
            else:
                block.is_expired = False
    
    @api.depends('block_type', 'blocked_to_date', 'blocked_until_session', 'status')
    def _compute_remaining_time(self):
        for block in self:
            if block.status != 'active':
                block.remaining_time = 'Block not active'
                continue
                
            if block.block_type == 'time' and block.blocked_to_date:
                remaining = block.blocked_to_date - fields.Datetime.now()
                if remaining.total_seconds() > 0:
                    days = remaining.days
                    hours, remainder = divmod(remaining.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    if days > 0:
                        block.remaining_time = f"{days}d {hours}h {minutes}m"
                    elif hours > 0:
                        block.remaining_time = f"{hours}h {minutes}m"
                    else:
                        block.remaining_time = f"{minutes}m"
                else:
                    block.remaining_time = 'Expired'
            elif block.block_type == 'session' and block.blocked_until_session:
                current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
                if current_session:
                    session_num = int(current_session.name.split(' ')[-1]) if current_session.name.startswith('Session ') else 0
                    remaining_sessions = block.blocked_until_session - session_num
                    if remaining_sessions > 0:
                        block.remaining_time = f"{remaining_sessions} session(s)"
                    else:
                        block.remaining_time = 'Expired'
                else:
                    block.remaining_time = f"Until Session {block.blocked_until_session}"
            else:
                block.remaining_time = 'Unknown'
    
    @api.constrains('duration_minutes', 'blocked_to_date', 'blocked_until_session')
    def _check_block_parameters(self):
        for block in self:
            if block.block_type == 'time':
                if not block.blocked_to_date and not block.duration_minutes:
                    raise ValidationError("Time-based blocks must have either 'Blocked Until' date or 'Duration' specified.")
            elif block.block_type == 'session':
                if not block.blocked_until_session:
                    raise ValidationError("Session-based blocks must specify 'Blocked Until Session'.")
    
    @api.constrains('user_id', 'blocked_by_id')
    def _check_block_permissions(self):
        for block in self:
            # SuperAdmin users cannot be blocked by other users
            if block.user_id.user_type == 'superadmin' and block.blocked_by_id.user_type != 'superadmin':
                raise ValidationError("SuperAdmin users can only be blocked by other SuperAdmin users.")
    
    @api.model
    def create(self, vals):
        # Set blocked_to_date based on duration_minutes if provided
        if vals.get('duration_minutes') and vals.get('block_type') == 'time':
            duration = timedelta(minutes=vals['duration_minutes'])
            from_date = fields.Datetime.from_string(vals.get('blocked_from_date', fields.Datetime.now()))
            vals['blocked_to_date'] = fields.Datetime.to_string(from_date + duration)
        
        block = super(StockUserBlock, self).create(vals)
        
        # Log the blocking action
        block.message_post(
            body=f"User {block.user_id.name} blocked by {block.blocked_by_id.name}. "
                 f"Reason: {dict(block._fields['block_reason'].selection)[block.block_reason]}. "
                 f"Type: {dict(block._fields['block_type'].selection)[block.block_type]}",
            message_type='notification'
        )
        
        return block
    
    def action_cancel_block(self):
        """Cancel the block manually"""
        self.ensure_one()
        if self.status == 'active':
            self.status = 'cancelled'
            self.message_post(
                body=f"Block cancelled by {self.env.user.name}",
                message_type='notification'
            )
    
    def action_expire_block(self):
        """Mark block as expired"""
        self.ensure_one()
        if self.status == 'active':
            self.status = 'expired'
            self.message_post(
                body="Block expired automatically",
                message_type='notification'
            )
    
    @api.model
    def cron_expire_blocks(self):
        """Cron job to automatically expire blocks"""
        # Find expired time-based blocks
        time_blocks = self.search([
            ('status', '=', 'active'),
            ('block_type', '=', 'time'),
            ('blocked_to_date', '<=', fields.Datetime.now())
        ])
        
        for block in time_blocks:
            block.action_expire_block()
        
        # Find expired session-based blocks
        current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
        if current_session:
            session_num = int(current_session.name.split(' ')[-1]) if current_session.name.startswith('Session ') else 0
            session_blocks = self.search([
                ('status', '=', 'active'),
                ('block_type', '=', 'session'),
                ('blocked_until_session', '<=', session_num)
            ])
            
            for block in session_blocks:
                block.action_expire_block()
        
        _logger.info(f"Expired {len(time_blocks)} time-based blocks and {len(session_blocks) if current_session else 0} session-based blocks")
    
    @api.model
    def check_user_blocked(self, user_id):
        """Check if a user is currently blocked"""
        # Run expiry check first
        self.cron_expire_blocks()
        
        # Check for active blocks
        active_blocks = self.search([
            ('user_id', '=', user_id),
            ('status', '=', 'active')
        ])
        
        if active_blocks:
            block = active_blocks[0]  # Get the most recent active block
            return {
                'is_blocked': True,
                'block_id': block.id,
                'reason': dict(block._fields['block_reason'].selection)[block.block_reason],
                'custom_reason': block.custom_reason,
                'blocked_until': block.blocked_to_date if block.block_type == 'time' else f"Session {block.blocked_until_session}",
                'remaining_time': block.remaining_time
            }
        
        return {'is_blocked': False}