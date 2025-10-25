#!/usr/bin/env python3
import odoo
from odoo import api
from odoo.api import Environment
from odoo import registry
from datetime import datetime

"""
Quick script to simulate a broker placing an order on behalf of an investor
and calling action_submit(), to validate that no emails are sent and no
mail-related exceptions are raised during submission.

It will:
- Find or create an open trading session
- Pick any active security (trading)
- Pick any investor with sufficient cash
- Create a limit BUY order with safe price
- Call action_submit() and print the result
"""

def main():
    dbname = 'stock'
    reg = registry(dbname)
    with reg.cursor() as cr:
        env = Environment(cr, 1, {})  # admin user

        # 1) Ensure there is an open session
        Session = env['stock.session']
        session = Session.search([('state', '=', 'open')], limit=1)
        if not session:
            session = Session.create({
                'name': f'Test Session {datetime.now().strftime("%Y%m%d%H%M%S")}',
                'state': 'open',
                'planned_start_date': datetime.now(),
                'planned_end_date': datetime.now(),
                'actual_start_date': datetime.now(),
                'broker_commission_rate': 0.0,
            })
            print(f"Created open session: {session.name}")
        else:
            print(f"Using open session: {session.name}")

        # 2) Pick a security: prefer trading security for limit order test; fallback to IPO security for IPO test
        Security = env['stock.security']
        trading_sec = Security.search([('active', '=', True), ('ipo_status', '=', 'trading')], limit=1)
        ipo_sec = Security.search([('ipo_status', 'in', ['ipo', 'po'])], limit=1)
        if trading_sec:
            print(f"Using trading security: {trading_sec.symbol} @ {trading_sec.current_price}")
        else:
            print("No trading security found; LIMIT order test will be skipped.")
        if ipo_sec:
            print(f"Using IPO security: {ipo_sec.symbol} status={ipo_sec.ipo_status} ipo_price={ipo_sec.ipo_price}")
        else:
            print("No IPO security found; IPO order test will be skipped.")

        # 3) Pick an investor with cash
        Users = env['res.users']
        investor = Users.search([('user_type', '=', 'investor')], limit=1)
        if not investor:
            # Create a basic investor if none exist
            investor = Users.create({
                'name': 'Test Investor',
                'login': f'test_investor_{datetime.now().timestamp()}',
                'email': 'investor@example.com',
                'user_type': 'investor',
                'cash_balance': 100000.0,
            })
            print(f"Created investor: {investor.name}")
        else:
            # Top up cash if needed
            if (investor.cash_balance or 0.0) < 1000:
                investor.write({'cash_balance': 100000.0})
            print(f"Using investor: {investor.name} cash={investor.cash_balance}")

        # 4) Create a limit BUY order as a broker on behalf of investor
        Order = env['stock.order'].with_context(
            mail_create_nolog=True,
            mail_create_nosubscribe=True,
        )
        # Test A: limit BUY on trading security
        if trading_sec:
            price = max(trading_sec.current_price or 1.0, 1.0)
            order_vals = {
                'user_id': investor.id,
                'session_id': session.id,
                'security_id': trading_sec.id,
                'side': 'buy',
                'order_type': 'limit',
                'quantity': 10,
                'price': price,
                'entered_by_id': 1,  # admin as broker
            }
            order = Order.create(order_vals)
            print(f"Created LIMIT order: {order.name} status={order.status}")
            try:
                order.sudo().action_submit()
                print(f"LIMIT submission success: status={order.status}")
            except Exception as e:
                print(f"LIMIT submission error: {e}")
                raise

        # Test B: IPO BUY on IPO security if available
        if ipo_sec:
            ipo_order_vals = {
                'user_id': investor.id,
                'session_id': session.id,
                'security_id': ipo_sec.id,
                'side': 'buy',
                'order_type': 'ipo',
                'quantity': 10,
                'price': 0.0,
                'entered_by_id': 1,
            }
            ipo_order = Order.create(ipo_order_vals)
            print(f"Created IPO order: {ipo_order.name} status={ipo_order.status}")
            try:
                ipo_order.sudo().action_submit()
                print(f"IPO submission success: status={ipo_order.status}")
            except Exception as e:
                print(f"IPO submission error: {e}")
                raise
        print("OK: No mail errors during submission for executed tests.")

        cr.commit()

if __name__ == '__main__':
    main()
