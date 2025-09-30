# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class StockMatchingEngine(models.TransientModel):
    _name = 'stock.matching.engine'
    _description = 'Order Matching Engine'
    
    @api.model
    def match_all_securities(self, session):
        """Match orders for all active securities in the session"""
        # Check and activate stop orders first
        self._check_stop_orders(session)
        
        # Get all active securities
        securities = self.env['stock.security'].search([('active', '=', True)])
        
        for security in securities:
            try:
                # Create a savepoint for each security matching
                with self.env.cr.savepoint():
                    self._match_security_orders(security, session)
            except Exception as e:
                _logger.error(f"Failed to match orders for security {security.symbol}: {str(e)}")
                # Continue with next security even if one fails
                continue
    
    def _check_stop_orders(self, session):
        """Check and activate stop orders that have been triggered"""
        # Get all pending stop orders
        stop_orders = self.env['stock.order'].search([
            ('session_id', '=', session.id),
            ('order_type', 'in', ['stop_loss', 'stop_limit']),
            ('status', '=', 'submitted')
        ])
        
        for order in stop_orders:
            current_price = order.security_id.current_price
            
            # Check if stop price has been triggered
            triggered = False
            if order.side == 'sell' and current_price <= order.stop_price:
                triggered = True
            elif order.side == 'buy' and current_price >= order.stop_price:
                triggered = True
            
            if triggered:
                # Convert to market or limit order
                if order.order_type == 'stop_loss':
                    order.order_type = 'market'
                    order.price = 0  # Market orders don't have a price
                else:  # stop_limit
                    order.order_type = 'limit'
                    # Price is already set for stop limit orders
                
                order.status = 'open'
                _logger.info(f"Stop order {order.name} triggered at price {current_price}")
    
    def _match_security_orders(self, security, session):
        """Match buy and sell orders for a specific security"""
        # Lock the security record to prevent concurrent matching
        self.env.cr.execute(
            "SELECT id FROM stock_security WHERE id = %s FOR UPDATE NOWAIT",
            [security.id]
        )
        
        # Process IOC and FOK orders first
        self._process_immediate_orders(security, session)
        
        # Get active buy orders (sorted by price desc for priority, then time asc)
        buy_orders = self.env['stock.order'].search([
            ('security_id', '=', security.id),
            ('session_id', '=', session.id),
            ('side', '=', 'buy'),
            ('status', 'in', ['open', 'partial']),
            ('time_in_force', 'in', ['day', 'gtc'])
        ], order='order_type desc, price desc, create_date asc')
        
        # Get active sell orders (sorted by price asc, then time asc)
        sell_orders = self.env['stock.order'].search([
            ('security_id', '=', security.id),
            ('session_id', '=', session.id),
            ('side', '=', 'sell'),
            ('status', 'in', ['open', 'partial']),
            ('time_in_force', 'in', ['day', 'gtc'])
        ], order='order_type desc, price asc, create_date asc')
        
        # Match orders
        for buy_order in buy_orders:
            if buy_order.remaining_quantity <= 0:
                continue
                
            for sell_order in sell_orders:
                if sell_order.remaining_quantity <= 0:
                    continue
                
                # Check if orders can match
                if not self._can_match(buy_order, sell_order):
                    continue
                
                # Execute the trade with transaction management
                try:
                    with self.env.cr.savepoint():
                        self._execute_trade(buy_order, sell_order, session)
                except Exception as e:
                    _logger.error(f"Failed to execute trade between orders {buy_order.name} and {sell_order.name}: {str(e)}")
                    # Continue matching other orders
                    continue
                
                # Check if buy order is fully filled
                if buy_order.remaining_quantity <= 0:
                    break
    
    def _process_immediate_orders(self, security, session):
        """Process IOC and FOK orders that require immediate execution"""
        immediate_orders = self.env['stock.order'].search([
            ('security_id', '=', security.id),
            ('session_id', '=', session.id),
            ('status', 'in', ['open']),
            ('time_in_force', 'in', ['ioc', 'fok'])
        ], order='create_date asc')
        
        for order in immediate_orders:
            if order.time_in_force == 'ioc':
                # Try to fill as much as possible, cancel remainder
                self._try_immediate_fill(order, session)
                if order.remaining_quantity > 0:
                    order.status = 'cancelled'
                    order.message_post(body=f"IOC order partially filled. Remaining {order.remaining_quantity} cancelled.")
            
            elif order.time_in_force == 'fok':
                # Check if full quantity can be filled
                available_qty = self._get_available_quantity(order)
                if available_qty >= order.quantity:
                    self._try_immediate_fill(order, session)
                else:
                    order.status = 'cancelled'
                    order.message_post(body="FOK order cancelled - insufficient liquidity")
    
    def _try_immediate_fill(self, order, session):
        """Try to immediately fill an order against existing orders"""
        opposite_side = 'sell' if order.side == 'buy' else 'buy'
        price_condition = 'price asc' if order.side == 'buy' else 'price desc'
        
        matching_orders = self.env['stock.order'].search([
            ('security_id', '=', order.security_id.id),
            ('session_id', '=', session.id),
            ('side', '=', opposite_side),
            ('status', 'in', ['open', 'partial'])
        ], order=price_condition + ', create_date asc')
        
        for match_order in matching_orders:
            if order.remaining_quantity <= 0:
                break
            
            if self._can_match(order, match_order):
                self._execute_trade(order, match_order, session)
    
    def _get_available_quantity(self, order):
        """Get the total available quantity that can be matched for an order"""
        opposite_side = 'sell' if order.side == 'buy' else 'buy'
        
        matching_orders = self.env['stock.order'].search([
            ('security_id', '=', order.security_id.id),
            ('session_id', '=', order.session_id.id),
            ('side', '=', opposite_side),
            ('status', 'in', ['open', 'partial'])
        ])
        
        available = 0
        for match_order in matching_orders:
            if self._can_match(order, match_order):
                available += match_order.remaining_quantity
        
        return available
    def _can_match(self, buy_order, sell_order):
        """Check if two orders can match"""
        # Handle market orders - they match at any price
        if buy_order.order_type == 'market' or sell_order.order_type == 'market':
            # Market orders always match (price check not needed)
            pass
        else:
            # For limit orders: buy price must be >= sell price
            if buy_order.price < sell_order.price:
                return False
        
        # Prevent self-trading (same user)
        if buy_order.user_id == sell_order.user_id:
            _logger.info(f"Preventing self-trade for user {buy_order.user_id.name}")
            return False
        
        # Both orders must have remaining quantity
        if buy_order.remaining_quantity <= 0 or sell_order.remaining_quantity <= 0:
            return False
        
        return True
    
    def _execute_trade(self, buy_order, sell_order, session):
        """Execute a trade between buy and sell orders"""
        # Determine trade quantity (minimum of remaining quantities)
        trade_quantity = min(buy_order.remaining_quantity, sell_order.remaining_quantity)
        
        # Determine trade price (passive order price - sell order came first)
        # In a real exchange, this would be more complex
        trade_price = sell_order.price
        
        # Validate seller has sufficient stocks
        seller_position = self.env['stock.position'].search([
            ('user_id', '=', sell_order.user_id.id),
            ('security_id', '=', sell_order.security_id.id)
        ], limit=1)
        
        if not seller_position or seller_position.quantity < trade_quantity:
            _logger.warning(f"Seller {sell_order.user_id.name} has insufficient stocks")
            sell_order.write({
                'status': 'rejected',
                'rejection_reason': 'Insufficient stocks to complete order'
            })
            return
        
        # Calculate amounts
        trade_value = trade_quantity * trade_price
        buyer_commission = trade_value * buy_order.broker_commission_rate / 100
        seller_commission = trade_value * sell_order.broker_commission_rate / 100
        
        buyer_total_cost = trade_value + buyer_commission
        seller_net_proceeds = trade_value - seller_commission
        
        # Validate buyer has sufficient funds
        if buy_order.user_id.cash_balance < buyer_total_cost:
            _logger.warning(f"Buyer {buy_order.user_id.name} has insufficient funds")
            buy_order.write({
                'status': 'rejected',
                'rejection_reason': 'Insufficient funds to complete order'
            })
            return
        
        # Create trade record
        trade = self.env['stock.trade'].create({
            'buy_order_id': buy_order.id,
            'sell_order_id': sell_order.id,
            'security_id': sell_order.security_id.id,
            'session_id': session.id,
            'quantity': trade_quantity,
            'price': trade_price,
            'value': trade_value,
            'buy_commission': buyer_commission,
            'sell_commission': seller_commission,
        })
        
        # Update cash balances
        buy_order.user_id.cash_balance -= buyer_total_cost
        sell_order.user_id.cash_balance += seller_net_proceeds
        
        # Update broker balances
        if buy_order.broker_id:
            buy_order.broker_id.cash_balance += buyer_commission
        if sell_order.broker_id:
            sell_order.broker_id.cash_balance += seller_commission
        
        # Update positions
        self._update_positions(buy_order.user_id, sell_order.user_id, 
                             sell_order.security_id, trade_quantity)
        
        # Update order filled quantities
        buy_order.update_filled_quantity(trade_quantity)
        sell_order.update_filled_quantity(trade_quantity)
        
        # Log the trade
        _logger.info(
            f"Trade executed: {trade_quantity} shares of {sell_order.security_id.symbol} "
            f"at {trade_price} between {buy_order.user_id.name} and {sell_order.user_id.name}"
        )
        
        # Check if price update is needed
        self._check_price_update(sell_order.security_id, trade_price, trade_quantity, session)
        
        # Force a commit after successful trade execution
        self.env.cr.commit()
    
    def _update_positions(self, buyer, seller, security, quantity):
        """Update buyer and seller positions"""
        # Update seller position (reduce quantity)
        seller_position = self.env['stock.position'].search([
            ('user_id', '=', seller.id),
            ('security_id', '=', security.id)
        ], limit=1)
        
        if seller_position:
            seller_position.quantity -= quantity
            if seller_position.quantity == 0:
                seller_position.unlink()
        
        # Update buyer position (increase quantity)
        buyer_position = self.env['stock.position'].search([
            ('user_id', '=', buyer.id),
            ('security_id', '=', security.id)
        ], limit=1)
        
        if buyer_position:
            # Update average cost
            total_cost = (buyer_position.quantity * buyer_position.average_cost) + \
                        (quantity * security.current_price)
            total_quantity = buyer_position.quantity + quantity
            buyer_position.write({
                'quantity': total_quantity,
                'average_cost': total_cost / total_quantity if total_quantity > 0 else 0
            })
        else:
            # Create new position
            self.env['stock.position'].create({
                'user_id': buyer.id,
                'security_id': security.id,
                'quantity': quantity,
                'average_cost': security.current_price
            })
    
    def _check_price_update(self, security, trade_price, trade_quantity, session):
        """
        Check if price update is needed based on trading activity
        Implements the price change logic from C# Change_Price() method
        """
        # Get all trades for this security in current session
        today_trades = self.env['stock.trade'].search([
            ('security_id', '=', security.id),
            ('session_id', '=', session.id)
        ])
        
        if not today_trades:
            return
        
        # Calculate total quantity of all holdings
        total_holdings = sum(
            self.env['stock.position'].search([
                ('security_id', '=', security.id)
            ]).mapped('quantity')
        )
        
        if total_holdings <= 0:
            return
        
        # Calculate weighted average price
        total_value = sum(trade.quantity * trade.price for trade in today_trades)
        total_quantity = sum(trade.quantity for trade in today_trades)
        
        if total_quantity <= 0:
            return
        
        # Calculate new price (VWAP approach)
        new_price = total_value / total_quantity
        
        # Check if price change exceeds threshold
        old_price = security.current_price
        price_change_pct = abs(new_price - old_price) / old_price * 100
        
        if price_change_pct >= session.price_change_threshold:
            # Update security price
            try:
                security.update_price(new_price)
                _logger.info(
                    f"Price updated for {security.symbol}: "
                    f"{old_price} -> {new_price} ({price_change_pct:.2f}% change)"
                )
            except Exception as e:
                _logger.error(f"Failed to update price: {str(e)}")
    
    @api.model
    def process_ipo_orders(self, security_id, ipo_quantity, ipo_price):
        """
        Process IPO orders for a security
        Implements special IPO handling from C#
        """
        security = self.env['stock.security'].browse(security_id)
        if not security:
            return
        
        try:
            with self.env.cr.savepoint():
                # Get all IPO orders (orders placed before security was active)
                ipo_orders = self.env['stock.order'].search([
                    ('security_id', '=', security_id),
                    ('side', '=', 'buy'),
                    ('status', '=', 'pending'),
                    ('order_type', '=', 'ipo')  # Special IPO order type
                ], order='create_date asc')
                
                remaining_ipo_quantity = ipo_quantity
                
                for order in ipo_orders:
                    if remaining_ipo_quantity <= 0:
                        break
                    
                    # Allocate IPO shares
                    allocation = min(order.quantity, remaining_ipo_quantity)
                    
                    # Create IPO trade
                    trade_value = allocation * ipo_price
                    commission = trade_value * order.broker_commission_rate / 100
                    total_cost = trade_value + commission
                    
                    # Check buyer has funds
                    if order.user_id.cash_balance < total_cost:
                        order.write({
                            'status': 'rejected',
                            'rejection_reason': 'Insufficient funds for IPO allocation'
                        })
                        continue
                    
                    # Create trade
                    self.env['stock.trade'].create({
                        'buy_order_id': order.id,
                        'sell_order_id': False,  # No sell order for IPO
                        'security_id': security_id,
                        'quantity': allocation,
                        'price': ipo_price,
                        'value': trade_value,
                        'buy_commission': commission,
                        'sell_commission': 0,
                        'trade_type': 'ipo'
                    })
                    
                    # Update buyer's cash and position
                    order.user_id.cash_balance -= total_cost
                    if order.broker_id:
                        order.broker_id.cash_balance += commission
                    
                    # Create/update position
                    position = self.env['stock.position'].search([
                        ('user_id', '=', order.user_id.id),
                        ('security_id', '=', security_id)
                    ], limit=1)
                    
                    if position:
                        total_cost = (position.quantity * position.average_cost) + \
                                   (allocation * ipo_price)
                        total_quantity = position.quantity + allocation
                        position.write({
                            'quantity': total_quantity,
                            'average_cost': total_cost / total_quantity
                        })
                    else:
                        self.env['stock.position'].create({
                            'user_id': order.user_id.id,
                            'security_id': security_id,
                            'quantity': allocation,
                            'average_cost': ipo_price
                        })
                    
                    # Update order
                    order.update_filled_quantity(allocation)
                    remaining_ipo_quantity -= allocation
                    
                    _logger.info(f"IPO allocation: {allocation} shares to {order.user_id.name}")
                
                # Set security as active and tradeable
                security.write({
                    'active': True,
                    'ipo_price': ipo_price,
                    'current_price': ipo_price,
                    'session_start_price': ipo_price
                })
                
                # Commit IPO processing
                self.env.cr.commit()
                
        except Exception as e:
            _logger.error(f"Failed to process IPO orders: {str(e)}")
            raise UserError(f"IPO processing failed: {str(e)}") 