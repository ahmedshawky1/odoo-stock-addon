#!/usr/bin/env python3
"""
Diagnostic script to check order matching issues in session 04
"""

import odoo
from odoo import api, SUPERUSER_ID
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

def diagnose_orders():
    # Initialize Odoo environment
    odoo.tools.config.parse_config(['--config=/etc/odoo/odoo.conf'])
    registry = odoo.registry('stock')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Find session 04
        sessions = env['stock.session'].search([])
        session_04 = None
        
        for session in sessions:
            if '04' in session.name or session.id == 4:
                session_04 = session
                break
        
        if not session_04:
            _logger.info("Session 04 not found. Available sessions:")
            for session in sessions:
                _logger.info(f"  - Session {session.id}: {session.name} (state: {session.state})")
            return
        
        _logger.info(f"Found session: {session_04.name} (ID: {session_04.id}, state: {session_04.state})")
        
        # Check orders in session 04
        orders = env['stock.order'].search([('session_id', '=', session_04.id)])
        _logger.info(f"Total orders in session: {len(orders)}")
        
        if not orders:
            _logger.info("No orders found in session 04")
            return
        
        # Group orders by status
        order_stats = {}
        for order in orders:
            status = order.status
            if status not in order_stats:
                order_stats[status] = []
            order_stats[status].append(order)
        
        _logger.info("Order statistics by status:")
        for status, order_list in order_stats.items():
            _logger.info(f"  - {status}: {len(order_list)} orders")
        
        # Check buy vs sell orders
        buy_orders = orders.filtered(lambda o: o.side == 'buy')
        sell_orders = orders.filtered(lambda o: o.side == 'sell')
        
        _logger.info(f"Buy orders: {len(buy_orders)}")
        _logger.info(f"Sell orders: {len(sell_orders)}")
        
        # Check orders by security
        securities = {}
        for order in orders:
            sec = order.security_id
            if sec not in securities:
                securities[sec] = {'buy': [], 'sell': []}
            securities[sec][order.side].append(order)
        
        _logger.info("Orders by security:")
        for security, sides in securities.items():
            _logger.info(f"  {security.symbol}:")
            _logger.info(f"    Buy orders: {len(sides['buy'])}")
            _logger.info(f"    Sell orders: {len(sides['sell'])}")
            
            # Show specific orders
            for order in sides['buy'][:3]:  # Show first 3 buy orders
                _logger.info(f"      BUY: {order.name} - {order.quantity}@{order.price} ({order.status})")
            for order in sides['sell'][:3]:  # Show first 3 sell orders
                _logger.info(f"      SELL: {order.name} - {order.quantity}@{order.price} ({order.status})")
        
        # Check if session is open
        if session_04.state != 'open':
            _logger.info(f"WARNING: Session is not open! Current state: {session_04.state}")
            return
        
        # Check matching eligibility
        matchable_buy = orders.filtered(lambda o: o.side == 'buy' and o.status in ['open', 'partial'] and o.remaining_quantity > 0)
        matchable_sell = orders.filtered(lambda o: o.side == 'sell' and o.status in ['open', 'partial'] and o.remaining_quantity > 0)
        
        _logger.info(f"Matchable buy orders: {len(matchable_buy)}")
        _logger.info(f"Matchable sell orders: {len(matchable_sell)}")
        
        if matchable_buy and matchable_sell:
            _logger.info("Potential matches found. Checking specific pairs...")
            
            for buy_order in matchable_buy[:5]:  # Check first 5
                for sell_order in matchable_sell:
                    if buy_order.security_id == sell_order.security_id:
                        can_match = True
                        reasons = []
                        
                        # Check price compatibility
                        if buy_order.order_type != 'market' and sell_order.order_type != 'market':
                            if buy_order.price < sell_order.price:
                                can_match = False
                                reasons.append(f"Price mismatch: bid {buy_order.price} < ask {sell_order.price}")
                        
                        # Check users
                        if buy_order.user_id == sell_order.user_id:
                            can_match = False
                            reasons.append("Same user")
                        
                        # Check quantities
                        if buy_order.remaining_quantity <= 0 or sell_order.remaining_quantity <= 0:
                            can_match = False
                            reasons.append("Zero remaining quantity")
                        
                        match_status = "CAN MATCH" if can_match else "BLOCKED"
                        _logger.info(f"  {match_status}: {buy_order.name} vs {sell_order.name}")
                        if reasons:
                            _logger.info(f"    Reasons: {', '.join(reasons)}")

if __name__ == '__main__':
    diagnose_orders()