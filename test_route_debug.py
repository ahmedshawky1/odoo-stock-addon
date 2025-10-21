#!/usr/bin/env python3

import odoo
from odoo.api import Environment
from odoo import registry
from odoo.tests.common import HttpCase
import logging

# Test the three problematic routes
def test_routes():
    try:
        reg = registry('stock')
        with reg.cursor() as cr:
            env = Environment(cr, 1, {})
            
            # Test market_securities controller logic
            print("Testing market_securities logic...")
            securities = env['stock.security'].search([])
            print(f"Found {len(securities)} securities")
            
            if securities:
                sec = securities[0]
                print(f"Testing security: {sec.symbol}")
                
                # Test price history search
                latest_price = env['stock.price.history'].search([
                    ('security_id', '=', sec.id)
                ], order='change_date desc', limit=1)
                print(f"Latest price record: {latest_price.id if latest_price else 'None'}")
                
                if latest_price:
                    # Test the previous price logic 
                    previous_price = env['stock.price.history'].search([
                        ('security_id', '=', sec.id),
                        ('change_date', '<', latest_price.change_date)
                    ], order='change_date desc', limit=1)
                    print(f"Previous price record: {previous_price.id if previous_price else 'None'}")
                    
                    # Test the calculation logic
                    change = 0.0
                    change_percent = 0.0
                    if latest_price and previous_price:
                        change = latest_price.new_price - previous_price.new_price
                        change_percent = (change / previous_price.new_price) * 100 if previous_price.new_price else 0.0
                    
                    print(f"Change calculation: {change}, {change_percent}%")
            
            # Test market_session_info logic
            print("\nTesting market_session_info logic...")
            active_session = env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
            print(f"Active session: {active_session.name if active_session else 'None'}")
            
            if active_session:
                trades = env['stock.trade'].search([
                    ('session_id', '=', active_session.id)
                ])
                print(f"Session trades: {len(trades)}")
                
                if trades:
                    stats = {
                        'trades_count': len(trades),
                        'total_volume': sum(trades.mapped('quantity')),
                        'total_value': sum(trades.mapped('value')),
                        'unique_securities': len(trades.mapped('security_id')),
                        'unique_traders': len(set(trades.mapped('buyer_id').ids + trades.mapped('seller_id').ids)),
                    }
                    print(f"Session stats: {stats}")
            
            # Test market_reports logic
            print("\nTesting market_reports logic...")
            total_securities = env['stock.security'].search_count([])
            print(f"Total securities: {total_securities}")
            
            # Test today's trading stats
            from datetime import datetime, timedelta
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # Check if fields.Datetime.now() works correctly
            from odoo import fields
            current_time = fields.Datetime.now()
            print(f"Current time: {current_time}")
            
            today_trades = env['stock.trade'].search([
                ('trade_date', '>=', today_start),
                ('trade_date', '<', today_end)
            ])
            print(f"Today's trades: {len(today_trades)}")
            
            market_stats = {
                'total_securities': total_securities,
                'total_users': env['res.users'].search_count([('user_type', '!=', False)]),
                'total_trades_today': len(today_trades),
                'total_volume_today': sum(today_trades.mapped('quantity')),
                'total_value_today': sum(today_trades.mapped('value')),
            }
            print(f"Market stats: {market_stats}")
            
            print("\nAll route logic tests passed!")
                
    except Exception as e:
        print(f"Error in route testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_routes()
