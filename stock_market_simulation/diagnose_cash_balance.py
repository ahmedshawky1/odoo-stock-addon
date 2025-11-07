#!/usr/bin/env python3
"""
Diagnostic script to check cash balance discrepancy
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnose_cash_balance():
    """Diagnose cash balance issues"""
    print("=== CASH BALANCE DIAGNOSTIC ===")
    
    # This would be run in Odoo environment
    print("To run this diagnostic in Odoo shell:")
    print("""
sudo docker exec -it odoo_stock odoo shell -d stock << 'EOF'
user_a1 = env['res.users'].search([('login', '=', 'A1')], limit=1)
if user_a1:
    print(f"User A1 cash_balance: ${user_a1.cash_balance}")
    
    # Get latest transaction
    latest_txn = env['stock.transaction.log'].search([('user_id', '=', user_a1.id)], order='id desc', limit=1)
    if latest_txn:
        print(f"Latest transaction running_balance: ${latest_txn.running_balance}")
        print(f"Latest transaction: {latest_txn.description}")
        print(f"Transaction date: {latest_txn.transaction_date}")
    
    # Calculate expected balance from all transactions
    all_txns = env['stock.transaction.log'].search([('user_id', '=', user_a1.id)], order='id')
    calculated_balance = 0
    print("\\nAll transactions:")
    for txn in all_txns:
        calculated_balance += txn.cash_impact
        print(f"  {txn.transaction_date}: {txn.description} | Impact: ${txn.cash_impact} | Calculated: ${calculated_balance} | Recorded: ${txn.running_balance}")
    
    print(f"\\nFinal calculated balance: ${calculated_balance}")
    print(f"User's cash_balance field: ${user_a1.cash_balance}")
    print(f"Latest transaction running_balance: ${latest_txn.running_balance if latest_txn else 'N/A'}")
    
    # Check if there are transactions after the last recorded balance update
    if latest_txn and latest_txn.running_balance != user_a1.cash_balance:
        print("\\n*** DISCREPANCY DETECTED ***")
        print("The user's cash_balance field does not match the latest transaction's running_balance")
        print("This suggests either:")
        print("1. The cash_balance was updated outside of the transaction log system")
        print("2. There's a bug in the transaction logging")
        print("3. The user's cash_balance field was manually modified")
else:
    print("User A1 not found")
EOF
    """)

if __name__ == "__main__":
    diagnose_cash_balance()