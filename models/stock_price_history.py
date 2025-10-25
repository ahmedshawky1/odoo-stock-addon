# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockPriceHistory(models.Model):
    _name = 'stock.price.history'
    _description = 'Stock Price History'
    _order = 'change_date desc'
    _rec_name = 'display_name'
    _inherit = ['stock.message.mixin']
    
    # Identity
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # Security
    security_id = fields.Many2one(
        'stock.security',
        string='Security',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Price Information
    old_price = fields.Float(
        string='Old Price',
        digits=(16, 4),
        required=True
    )
    
    new_price = fields.Float(
        string='New Price',
        digits=(16, 4),
        required=True
    )
    
    change_amount = fields.Float(
        string='Change Amount',
        compute='_compute_change',
        digits=(16, 4),
        store=True
    )
    
    change_percentage = fields.Float(
        string='Change %',
        compute='_compute_change',
        digits=(16, 2),
        store=True
    )
    
    # Context
    session_id = fields.Many2one(
        'stock.session',
        string='Trading Session',
        index=True
    )
    
    trigger_trade_id = fields.Many2one(
        'stock.trade',
        string='Trigger Trade',
        help='Trade that triggered this price change'
    )
    
    # Timestamp
    change_date = fields.Datetime(
        string='Change Date',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    
    # Additional Information
    change_reason = fields.Selection([
        ('trade', 'Trade Execution'),
        ('manual', 'Manual Adjustment'),
        ('ipo', 'IPO Pricing'),
        ('corporate', 'Corporate Action'),
        ('circuit', 'Circuit Breaker'),
        ('session_end', 'Session End Snapshot'),
    ], string='Change Reason', default='trade')
    
    notes = fields.Text(
        string='Notes',
        help='Additional notes about the price change'
    )
    
    @api.depends('security_id', 'change_date')
    def _compute_display_name(self):
        for history in self:
            if history.security_id and history.change_date:
                history.display_name = f"{history.security_id.symbol} - {history.change_date}"
            else:
                history.display_name = "Price Change"
    
    @api.depends('old_price', 'new_price')
    def _compute_change(self):
        for history in self:
            history.change_amount = history.new_price - history.old_price
            
            if history.old_price != 0:
                history.change_percentage = (history.change_amount / history.old_price) * 100
            else:
                history.change_percentage = 0.0
    
    @api.model
    def create(self, vals):
        history = super().create(vals)
        
        # Post to security chatter
        if history.security_id:
            body = f"""
            <p><strong>Price Updated</strong></p>
            <ul>
                <li>Old Price: {history.old_price:.4f}</li>
                <li>New Price: {history.new_price:.4f}</li>
                <li>Change: {history.change_amount:+.4f} ({history.change_percentage:+.2f}%)</li>
                <li>Reason: {dict(self._fields['change_reason'].selection).get(history.change_reason, '')}</li>
            </ul>
            """
            change_reason_display = dict(self._fields['change_reason'].selection).get(history.change_reason, '')
            price_details = f"New Price: {history.new_price}, Change: {history.change_amount:+.4f} ({history.change_percentage:+.2f}%), Reason: {change_reason_display}"
            history.security_id.log_action("Price updated", price_details)
        
        return history
    
    def get_price_at_date(self, security_id, target_date):
        """Get the price of a security at a specific date/time"""
        # Find the most recent price change before the target date
        history = self.search([
            ('security_id', '=', security_id),
            ('change_date', '<=', target_date)
        ], order='change_date desc', limit=1)
        
        if history:
            return history.new_price
        else:
            # No history before this date, return current price
            security = self.env['stock.security'].browse(security_id)
            return security.current_price if security else 0.0
    
    @api.model
    def get_price_range(self, security_id, start_date, end_date):
        """Get price history for a security within a date range"""
        return self.search([
            ('security_id', '=', security_id),
            ('change_date', '>=', start_date),
            ('change_date', '<=', end_date)
        ], order='change_date asc')
    
    @api.model
    def calculate_volatility(self, security_id, days=30):
        """Calculate price volatility over a period"""
        from datetime import timedelta
        import math
        
        end_date = fields.Datetime.now()
        start_date = end_date - timedelta(days=days)
        
        price_changes = self.get_price_range(security_id, start_date, end_date)
        
        if len(price_changes) < 2:
            return 0.0
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(price_changes)):
            prev_price = price_changes[i-1].new_price
            curr_price = price_changes[i].new_price
            
            if prev_price > 0:
                daily_return = (curr_price - prev_price) / prev_price
                returns.append(daily_return)
        
        if not returns:
            return 0.0
        
        # Calculate standard deviation of returns
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance) * math.sqrt(252)  # Annualized
        
        return volatility * 100  # As percentage 