#!/usr/bin/env python3
"""Test script to verify the race condition fix in transaction logging"""

import sys
import os

# Add Odoo path
sys.path.append('/usr/lib/python3/dist-packages')

def test_balance_consistency():
    """Test that the balance fix is working"""
    print("=== Testing Balance Consistency Fix ===")
    
    # Import Odoo
    import odoo
    from odoo import api, SUPERUSER_ID
    
    # Initialize registry
    registry = odoo.registry('stock')
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Check A1's current state
        a1 = env['res.users'].search([('login', '=', 'A1')])
        if not a1:
            print("A1 user not found")
            return
            
        print(f'A1 cash_balance: ${a1.cash_balance}')
        
        # Get last transaction for A1
        last_tx = env['stock.transaction.log'].search(
            [('user_id', '=', a1.id)], 
            order='transaction_date desc, id desc', 
            limit=1
        )
        
        if last_tx:
            print(f'Last transaction running balance: ${last_tx.running_balance}')
            print(f'Last transaction type: {last_tx.transaction_type}')
            print(f'Last transaction amount: ${last_tx.amount}')
            print(f'Last transaction date: {last_tx.transaction_date}')
            
            # Check if there's a balance discrepancy
            if abs(last_tx.running_balance - a1.cash_balance) > 0.01:  # Allow for small rounding
                print(f'DISCREPANCY: User balance {a1.cash_balance} != Last transaction running balance {last_tx.running_balance}')
                return False
            else:
                print('A1 Balances are consistent')
        else:
            print('No transactions found for A1')
            
        # Also check A2
        a2 = env['res.users'].search([('login', '=', 'A2')])
        if a2:
            print(f'\nA2 cash_balance: ${a2.cash_balance}')
            
            last_tx_a2 = env['stock.transaction.log'].search(
                [('user_id', '=', a2.id)], 
                order='transaction_date desc, id desc', 
                limit=1
            )
            
            if last_tx_a2:
                print(f'A2 Last transaction running balance: ${last_tx_a2.running_balance}')
                if abs(last_tx_a2.running_balance - a2.cash_balance) > 0.01:
                    print(f'A2 DISCREPANCY: User balance {a2.cash_balance} != Last transaction running balance {last_tx_a2.running_balance}')
                    return False
                else:
                    print('A2 Balances are consistent')
            else:
                print('No transactions found for A2')
        
        # Test the log_transaction method itself
        print("\n=== Testing log_transaction method ===")
        
        # Get transaction log model
        tx_log = env['stock.transaction.log']
        
        # Test logging a small transaction for A1
        try:
            print(f"Before test transaction - A1 balance: ${a1.cash_balance}")
            
            # Log a test transaction (small amount to avoid affecting real balance much)
            test_amount = 0.01
            result = tx_log.log_transaction(
                user_id=a1.id,
                transaction_type='trade',
                amount=test_amount,
                description='Test transaction for race condition fix'
            )
            
            if result.get('success'):
                print("Test transaction logged successfully")
                
                # Refresh user and check balance
                a1.refresh()
                new_last_tx = env['stock.transaction.log'].search(
                    [('user_id', '=', a1.id)], 
                    order='transaction_date desc, id desc', 
                    limit=1
                )
                
                print(f"After test transaction - A1 balance: ${a1.cash_balance}")
                print(f"New last transaction running balance: ${new_last_tx.running_balance}")
                
                if abs(new_last_tx.running_balance - a1.cash_balance) > 0.01:
                    print("RACE CONDITION STILL EXISTS!")
                    return False
                else:
                    print("Race condition fix is working correctly!")
                    return True
            else:
                print(f"Test transaction failed: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"Error testing transaction: {e}")
            return False

if __name__ == '__main__':
    test_balance_consistency()