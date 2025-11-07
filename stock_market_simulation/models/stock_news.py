# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class StockNews(models.Model):
    _name = 'stock.news'
    _description = 'Market News and Events'
    _order = 'start_session desc, create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Identity
    name = fields.Char(
        string='News Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('stock.news') or 'New'
    )
    
    # News Content
    headline = fields.Char(
        string='Headline/Title',
        required=True,
        tracking=True,
        help='News headline or title'
    )
    
    content = fields.Text(
        string='Content',
        required=True,
        help='Detailed news content'
    )
    
    summary = fields.Text(
        string='Summary',
        help='Brief summary of the news'
    )
    
    # News Classification
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='medium', required=True, tracking=True)
    
    news_type = fields.Selection([
        ('market', 'Market News'),
        ('company', 'Company News'),
        ('economic', 'Economic News'),
        ('regulatory', 'Regulatory News'),
        ('earnings', 'Earnings News'),
        ('analyst', 'Analyst Report'),
        ('event', 'Market Event'),
        ('announcement', 'Announcement'),
        ('other', 'Other')
    ], string='News Type', default='market', required=True, tracking=True)
    
    # Timing Control (from User Stories)
    start_session = fields.Integer(
        string='Start Session',
        help='Session number when news becomes visible'
    )
    
    end_session = fields.Integer(
        string='End Session', 
        help='Session number when news expires/becomes hidden'
    )
    
    start_minute = fields.Integer(
        string='Start Minute',
        help='Minute within session when news becomes visible'
    )
    
    end_minute = fields.Integer(
        string='End Minute',
        help='Minute within session when news expires'
    )
    
    # Status
    status = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, index=True)
    
    # Targeting
    stock_id = fields.Many2one(
        'stock.security',
        string='Related Stock',
        help='Stock ticker this news is related to (optional)'
    )
    
    sector_target = fields.Selection([
        ('energy', 'Energy'),
        ('financials', 'Financials'), 
        ('health_care', 'Health Care'),
        ('industrials', 'Industrials'),
        ('information_technology', 'Information Technology'),
        ('materials', 'Materials'),
        ('telecommunication_services', 'Telecommunication Services'),
        ('utilities', 'Utilities'),
        ('tourism', 'Tourism'),
        ('chemical', 'Chemical'),
        ('food_beverage', 'Food and Beverage'),
        ('medical_industry', 'Medical Industry'),
        ('real_estate', 'Real Estate'),
        ('media', 'Media'),
        ('construction', 'Construction'),
        ('fin_services', 'Financial Services'),
        ('banking', 'Banking'),
        ('transportation', 'Transportation')
    ], string='Sector Target', help='Target specific sector (optional)')
    
    geographic_relevance = fields.Selection([
        ('global', 'Global'),
        ('regional', 'Regional'),
        ('local', 'Local'),
        ('company_specific', 'Company Specific')
    ], string='Geographic Relevance', default='global')
    
    # Impact Simulation
    expected_impact = fields.Selection([
        ('very_negative', 'Very Negative'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
        ('positive', 'Positive'),
        ('very_positive', 'Very Positive')
    ], string='Expected Impact', default='neutral', help='Expected market impact')
    
    impact_magnitude = fields.Float(
        string='Impact Magnitude (%)',
        help='Expected price impact percentage'
    )
    
    # Publishing
    published_by_id = fields.Many2one(
        'res.users',
        string='Published By',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    publish_date = fields.Datetime(
        string='Publish Date',
        help='When the news was published'
    )
    
    # Computed Fields
    is_visible = fields.Boolean(
        string='Is Visible',
        compute='_compute_visibility',
        help='True if news should be visible now'
    )
    
    current_session_num = fields.Integer(
        string='Current Session Number',
        compute='_compute_current_session'
    )
    
    display_priority = fields.Char(
        string='Priority Display',
        compute='_compute_display_priority'
    )
    
    # Analytics
    view_count = fields.Integer(
        string='View Count',
        default=0,
        help='Number of times this news was viewed'
    )
    
    @api.depends('start_session', 'end_session', 'start_minute', 'end_minute', 'status')
    def _compute_visibility(self):
        for news in self:
            if news.status != 'active':
                news.is_visible = False
                continue
                
            current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            
            if not current_session:
                news.is_visible = False
                continue
                
            # Get current session number
            session_num = 0
            if current_session.name.startswith('Session '):
                try:
                    session_num = int(current_session.name.split(' ')[-1])
                except:
                    session_num = 0
            
            # Check session range
            if news.start_session and session_num < news.start_session:
                news.is_visible = False
                continue
                
            if news.end_session and session_num > news.end_session:
                news.is_visible = False
                continue
            
            # TODO: Add minute-level checking if needed
            # For now, if within session range, it's visible
            news.is_visible = True
    
    def _compute_current_session(self):
        for news in self:
            current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
            if current_session and current_session.name.startswith('Session '):
                try:
                    news.current_session_num = int(current_session.name.split(' ')[-1])
                except:
                    news.current_session_num = 0
            else:
                news.current_session_num = 0
    
    @api.depends('priority')
    def _compute_display_priority(self):
        for news in self:
            priority_map = {
                'low': '🟢 Low',
                'medium': '🟡 Medium', 
                'high': '🟠 High',
                'urgent': '🔴 Urgent'
            }
            news.display_priority = priority_map.get(news.priority, news.priority)
    
    @api.constrains('start_session', 'end_session')
    def _check_session_range(self):
        for news in self:
            if news.start_session and news.end_session:
                if news.start_session > news.end_session:
                    raise ValidationError("Start session must be less than or equal to end session.")
    
    @api.constrains('start_minute', 'end_minute')
    def _check_minute_range(self):
        for news in self:
            if news.start_minute and (news.start_minute < 0 or news.start_minute > 1440):
                raise ValidationError("Start minute must be between 0 and 1440.")
            if news.end_minute and (news.end_minute < 0 or news.end_minute > 1440):
                raise ValidationError("End minute must be between 0 and 1440.")
    
    def action_publish(self):
        """Publish the news (make it active)"""
        self.ensure_one()
        if self.status == 'draft':
            self.status = 'active'
            self.publish_date = fields.Datetime.now()
            self.message_post(
                body=f"News published by {self.env.user.name}",
                message_type='notification'
            )
    
    def action_schedule(self):
        """Schedule the news for future publication"""
        self.ensure_one()
        if self.status == 'draft':
            self.status = 'scheduled'
            self.message_post(
                body=f"News scheduled by {self.env.user.name}",
                message_type='notification'
            )
    
    def action_cancel(self):
        """Cancel the news"""
        self.ensure_one()
        if self.status in ['draft', 'scheduled', 'active']:
            self.status = 'cancelled'
            self.message_post(
                body=f"News cancelled by {self.env.user.name}",
                message_type='notification'
            )
    
    def action_expire(self):
        """Mark news as expired"""
        self.ensure_one()
        if self.status == 'active':
            self.status = 'expired'
            self.message_post(
                body="News expired automatically",
                message_type='notification'
            )
    
    def increment_view_count(self):
        """Increment view count when news is viewed"""
        self.ensure_one()
        self.view_count += 1
    
    @api.model
    def cron_update_news_status(self):
        """Cron job to update news status based on timing"""
        current_session = self.env['stock.session'].search([('state', '=', 'open')], limit=1)
        
        if not current_session:
            return
            
        # Get current session number
        session_num = 0
        if current_session.name.startswith('Session '):
            try:
                session_num = int(current_session.name.split(' ')[-1])
            except:
                session_num = 0
        
        # Activate scheduled news that should be active now
        scheduled_news = self.search([
            ('status', '=', 'scheduled'),
            ('start_session', '<=', session_num)
        ])
        
        for news in scheduled_news:
            news.action_publish()
        
        # Expire active news that should be expired now
        active_news = self.search([
            ('status', '=', 'active'),
            ('end_session', '<', session_num)
        ])
        
        for news in active_news:
            news.action_expire()
        
        _logger.info(f"Updated {len(scheduled_news)} scheduled news to active and {len(active_news)} active news to expired")
    
    @api.model
    def get_current_news(self, limit=None, stock_id=None, sector=None):
        """Get currently visible news with optional filtering"""
        domain = [('status', '=', 'active')]
        
        # Add stock filter
        if stock_id:
            domain.append(('stock_id', '=', stock_id))
        
        # Add sector filter
        if sector:
            domain.append(('sector_target', '=', sector))
        
        news = self.search(domain, order='priority desc, publish_date desc', limit=limit)
        
        # Filter by visibility
        visible_news = news.filtered('is_visible')
        
        return visible_news
    
    @api.model
    def get_news_for_user(self, user_id, limit=10):
        """Get relevant news for a specific user based on their portfolio"""
        user = self.env['res.users'].browse(user_id)
        
        # Get user's stock positions
        positions = self.env['stock.position'].search([('user_id', '=', user_id)])
        stock_ids = positions.mapped('security_id.id')
        
        # Get user's sectors
        sectors = positions.mapped('security_id.sector')
        
        # Build domain for relevant news
        domain = [('status', '=', 'active')]
        
        if stock_ids or sectors:
            stock_condition = [('stock_id', 'in', stock_ids)] if stock_ids else []
            sector_condition = [('sector_target', 'in', sectors)] if sectors else []
            general_condition = [('stock_id', '=', False), ('sector_target', '=', False)]
            
            # News related to user's stocks OR sectors OR general news
            domain.append('|')
            domain.append('|') 
            domain.extend(stock_condition if stock_condition else [('id', '=', -1)])
            domain.extend(sector_condition if sector_condition else [('id', '=', -1)])
            domain.extend(general_condition)
        
        news = self.search(domain, order='priority desc, publish_date desc', limit=limit)
        
        # Filter by visibility
        visible_news = news.filtered('is_visible')
        
        return visible_news