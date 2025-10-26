# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class StockTrade(models.Model):
    _name = 'stock.trade'
    _description = 'Executed Trade'
    _order = 'trade_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'stock.message.mixin']
    
    # Identity
    name = fields.Char(
        string='Trade Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('stock.trade') or 'New'
    )
    
    # Orders
    buy_order_id = fields.Many2one(
        'stock.order',
        string='Buy Order',
        required=True,
        readonly=True,
        ondelete='restrict'
    )
    
    sell_order_id = fields.Many2one(
        'stock.order',
        string='Sell Order',
        readonly=True,
        ondelete='restrict',
        help='Empty for IPO trades'
    )
    
    # Parties
    buyer_id = fields.Many2one(
        'res.users',
        string='Buyer',
        related='buy_order_id.user_id',
        store=True,
        readonly=True
    )
    
    seller_id = fields.Many2one(
        'res.users',
        string='Seller',
        related='sell_order_id.user_id',
        store=True,
        readonly=True
    )
    
    # Removed: buy_broker_id and sell_broker_id fields (default broker functionality removed)
    
    # Security and Session
    security_id = fields.Many2one(
        'stock.security',
        string='Security',
        related='buy_order_id.security_id',
        store=True,
        readonly=True,
        index=True
    )
    
    session_id = fields.Many2one(
        'stock.session',
        string='Trading Session',
        required=True,
        readonly=True,
        ondelete='restrict',
        index=True
    )
    
    # Trade Details
    quantity = fields.Integer(
        string='Quantity',
        required=True,
        readonly=True
    )
    
    price = fields.Float(
        string='Trade Price',
        digits=(16, 4),
        required=True,
        readonly=True
    )
    
    value = fields.Float(
        string='Trade Value',
        digits='Product Price',
        required=True,
        readonly=True,
        help='Quantity × Price'
    )
    
    # Commissions
    buy_commission = fields.Float(
        string='Buy Commission',
        digits='Product Price',
        readonly=True,
        help='Commission paid by buyer'
    )
    
    sell_commission = fields.Float(
        string='Sell Commission',
        digits='Product Price',
        readonly=True,
        help='Commission paid by seller'
    )
    
    total_commission = fields.Float(
        string='Total Commission',
        compute='_compute_total_commission',
        digits='Product Price',
        store=True
    )
    
    # Settlement
    settlement_status = fields.Selection([
        ('pending', 'Pending'),
        ('settled', 'Settled'),
        ('failed', 'Failed')
    ], string='Settlement Status', default='settled', readonly=True)
    
    trade_type = fields.Selection([
        ('regular', 'Regular'),
        ('ipo', 'IPO'),
        ('block', 'Block Trade')
    ], string='Trade Type', default='regular', readonly=True)
    
    # Timestamps
    trade_date = fields.Datetime(
        string='Trade Date',
        required=True,
        readonly=True,
        default=fields.Datetime.now,
        index=True
    )
    
    settlement_date = fields.Datetime(
        string='Settlement Date',
        readonly=True,
        help='T+N settlement date'
    )
    
    # Analytics
    buyer_pnl = fields.Float(
        string='Buyer P&L',
        compute='_compute_pnl',
        digits='Product Price',
        help='Unrealized P&L for buyer'
    )
    
    seller_pnl = fields.Float(
        string='Seller P&L',
        compute='_compute_pnl',
        digits='Product Price',
        help='Realized P&L for seller'
    )
    
    @api.depends('buy_commission', 'sell_commission')
    def _compute_total_commission(self):
        for trade in self:
            trade.total_commission = trade.buy_commission + trade.sell_commission
    
    @api.depends('security_id.current_price', 'price', 'quantity')
    def _compute_pnl(self):
        for trade in self:
            if trade.security_id:
                # Buyer P&L (unrealized)
                current_value = trade.quantity * trade.security_id.current_price
                cost_basis = trade.value + trade.buy_commission
                trade.buyer_pnl = current_value - cost_basis
                
                # Seller P&L (realized) - would need seller's cost basis
                # For now, just show proceeds
                trade.seller_pnl = trade.value - trade.sell_commission
            else:
                trade.buyer_pnl = 0.0
                trade.seller_pnl = 0.0
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.trade') or 'New'
        
        # Set settlement date (T+2 by default)
        if not vals.get('settlement_date'):
            from datetime import timedelta
            trade_date = fields.Datetime.from_string(vals.get('trade_date', fields.Datetime.now()))
            vals['settlement_date'] = trade_date + timedelta(days=2)
        
        trade = super().create(vals)
        
        # Log transactions for buyer and seller
        trade._log_trade_transactions()
        
        # Post to chatter
        trade._post_trade_message()
        
        return trade
    
    def _post_trade_message(self):
        """Post trade execution message to chatter"""
        self.ensure_one()
        
        body = f"""
        <p><strong>Trade Executed</strong></p>
        <ul>
            <li>Security: {self.security_id.symbol}</li>
            <li>Quantity: {self.quantity:,}</li>
            <li>Price: {self.price:.4f}</li>
            <li>Value: {self.value:,.2f}</li>
            <li>Buyer: {self.buyer_id.name}</li>
            <li>Seller: {self.seller_id.name if self.seller_id else 'IPO'}</li>
        </ul>
        """
        
        trade_details = f"Price: {self.price}, Quantity: {self.quantity}, Buyer: {self.buyer_id.name}, Seller: {self.seller_id.name if self.seller_id else 'IPO'}"
        self.log_action("Trade executed", trade_details)
    
    def _log_trade_transactions(self):
        """Log all transactions related to this trade"""
        self.ensure_one()
        transaction_log = self.env['stock.transaction.log']
        
        # Log buyer transactions
        if self.buyer_id:
            # Stock purchase transaction
            transaction_log.log_transaction(
                user_id=self.buyer_id.id,
                transaction_type='stock_purchase',
                amount=-(self.quantity * self.price),
                cash_impact=-(self.quantity * self.price),
                description=f'Purchased {self.quantity:,} shares of {self.security_id.symbol} at ${self.price:.2f}',
                transaction_date=self.trade_date,
                session_id=self.session_id.id,
                trade_id=self.id,
                security_id=self.security_id.id,
                quantity=self.quantity,
                price=self.price,
                reference=f'TRADE-{self.name}',
                notes=f'Trade #{self.name} - Buy side'
            )
            
            # Broker commission on buy (if applicable)
            if self.buy_commission > 0:
                transaction_log.log_transaction(
                    user_id=self.buyer_id.id,
                    transaction_type='broker_commission_buy',
                    amount=-self.buy_commission,
                    cash_impact=-self.buy_commission,
                    description=f'Broker commission on purchase of {self.security_id.symbol}',
                    transaction_date=self.trade_date,
                    session_id=self.session_id.id,
                    trade_id=self.id,
                    security_id=self.security_id.id,
                    reference=f'COMM-BUY-{self.name}',
                    notes=f'Commission for trade #{self.name}'
                )
        
        # Log seller transactions (if not IPO)
        if self.seller_id:
            # Stock sale transaction
            transaction_log.log_transaction(
                user_id=self.seller_id.id,
                transaction_type='stock_sale',
                amount=self.quantity * self.price,
                cash_impact=self.quantity * self.price,
                description=f'Sold {self.quantity:,} shares of {self.security_id.symbol} at ${self.price:.2f}',
                transaction_date=self.trade_date,
                session_id=self.session_id.id,
                trade_id=self.id,
                security_id=self.security_id.id,
                quantity=self.quantity,
                price=self.price,
                reference=f'TRADE-{self.name}',
                notes=f'Trade #{self.name} - Sell side'
            )
            
            # Broker commission on sell (if applicable)
            if self.sell_commission > 0:
                transaction_log.log_transaction(
                    user_id=self.seller_id.id,
                    transaction_type='broker_commission_sell',
                    amount=-self.sell_commission,
                    cash_impact=-self.sell_commission,
                    description=f'Broker commission on sale of {self.security_id.symbol}',
                    transaction_date=self.trade_date,
                    session_id=self.session_id.id,
                    trade_id=self.id,
                    security_id=self.security_id.id,
                    reference=f'COMM-SELL-{self.name}',
                    notes=f'Commission for trade #{self.name}'
                )
    
    def action_view_buy_order(self):
        """View the buy order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.order',
            'res_id': self.buy_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_sell_order(self):
        """View the sell order"""
        self.ensure_one()
        if self.sell_order_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.order',
                'res_id': self.sell_order_id.id,
                'view_mode': 'form',
                'target': 'current',
            } 