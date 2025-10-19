#!/usr/bin/env python3

import os
import re

# List of XML files that need monetary widget removal
xml_files = [
    'views/stock_security_views.xml',
    'views/stock_deposit_views.xml', 
    'views/stock_trade_views.xml',
    'views/res_users_views.xml',
    'views/stock_order_views.xml',
    'views/stock_position_views.xml',
    'views/stock_loan_views.xml',
    'views/stock_price_history_views.xml',
    'views/stock_session_views.xml',
    'report/investor_report_templates.xml'
]

def remove_monetary_widgets(file_path):
    """Remove monetary widget attributes from XML files"""
    if not os.path.exists(file_path):
        print(f"File {file_path} not found, skipping...")
        return 0
        
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Remove widget="monetary" attributes (with optional parameters)
    content = re.sub(r'\s+widget="monetary"[^>]*?/?>', '>', content)
    
    # Clean up any remaining monetary-related attributes
    content = re.sub(r'\s+widget="monetary"[^"]*"[^>]*', '', content)
    
    # Remove t-options with monetary widget in reports
    content = re.sub(r"\s+t-options='[^']*\"widget\":\s*\"monetary\"[^']*'", '', content)
    content = re.sub(r'\s+t-options="[^"]*\\"widget\\":\s*\\"monetary\\"[^"]*"', '', content)
    
    changes = len(re.findall(r'widget="monetary"', original_content))
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    return changes

# Process all files
total_changes = 0
base_path = '/var/odoo/addons/stock/stock_market_simulation/'

for xml_file in xml_files:
    full_path = os.path.join(base_path, xml_file)
    changes = remove_monetary_widgets(full_path)
    if changes > 0:
        print(f"Removed {changes} monetary widgets from {xml_file}")
    total_changes += changes

print(f"\nTotal monetary widgets removed: {total_changes}")