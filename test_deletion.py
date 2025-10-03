#!/usr/bin/env python3
"""Test session deletion prevention"""

# Run this from inside the container:
# sudo docker exec odoo_stock python3 /mnt/extra-addons/stock_market_simulation/test_deletion.py

import sys
import odoo
from odoo import api

# Initialize Odoo
odoo.tools.config.parse_config(['-c', '/etc/odoo/odoo.conf', '-d', 'stock'])

# Get registry and environment
registry = odoo.registry('stock')

with registry.cursor() as cr:
    env = api.Environment(cr, odoo.SUPERUSER_ID, {})
    
    print("\n=== Testing Session Deletion Prevention ===\n")
    
    # Test 1: Try to delete a draft session
    print("Test 1: Delete draft session (Session 02)")
    session = env['stock.session'].search([('name', '=', 'Session 02')], limit=1)
    if session:
        print(f"  Found: {session.name}, State: {session.state}")
        try:
            session.unlink()
            print("  ❌ ERROR: Draft session was deleted! This should not happen.")
        except Exception as e:
            print(f"  ✅ SUCCESS: Deletion blocked - {str(e)}")
    else:
        print("  Session 02 not found")
    
    # Test 2: Try to delete a settled session with orders
    print("\nTest 2: Delete settled session with orders")
    session = env['stock.session'].search([('name', '=', 'Demo Trading Session 2025')], limit=1)
    if session:
        orders = env['stock.order'].search([('session_id', '=', session.id)])
        print(f"  Found: {session.name}, State: {session.state}, Orders: {len(orders)}")
        try:
            session.unlink()
            print("  ❌ ERROR: Settled session was deleted! This should not happen.")
        except Exception as e:
            print(f"  ✅ SUCCESS: Deletion blocked - {str(e)}")
    else:
        print("  Demo Trading Session 2025 not found")
    
    # Test 3: Try to delete Session 01 (seed data)
    print("\nTest 3: Delete seed session (Session 01)")
    session = env['stock.session'].search([('name', '=', 'Session 01')], limit=1)
    if session:
        print(f"  Found: {session.name}, State: {session.state}")
        try:
            session.unlink()
            print("  ❌ ERROR: Seed session was deleted! This should not happen.")
        except Exception as e:
            print(f"  ✅ SUCCESS: Deletion blocked - {str(e)}")
    else:
        print("  Session 01 not found")
    
    # Test 4: List all sessions to verify none were deleted
    print("\nTest 4: Current sessions in database")
    sessions = env['stock.session'].search([])
    for s in sessions:
        orders = env['stock.order'].search([('session_id', '=', s.id)])
        trades = env['stock.trade'].search([('session_id', '=', s.id)])
        print(f"  - {s.name}: {s.state}, Orders: {len(orders)}, Trades: {len(trades)}")
    
    print("\n=== All tests completed ===\n")
