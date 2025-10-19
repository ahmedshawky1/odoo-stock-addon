#!/usr/bin/env python3

import os
import re

def clean_report_templates():
    """Clean monetary widgets from report templates"""
    file_path = '/var/odoo/addons/stock/stock_market_simulation/report/investor_report_templates.xml'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove t-options with monetary widget
    original_count = len(re.findall(r't-options=\'[^\']*"widget":\s*"monetary"[^\']*\'', content))
    content = re.sub(r"\s+t-options='[^']*\"widget\":\s*\"monetary\"[^']*'", '', content)
    
    # Also handle double quotes version
    original_count += len(re.findall(r't-options="[^"]*\\"widget\\":\s*\\"monetary\\"[^"]*"', content))
    content = re.sub(r'\s+t-options="[^"]*\\"widget\\":\s*\\"monetary\\"[^"]*"', '', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Removed {original_count} monetary widgets from report templates")
    return original_count

# Clean report templates
total_removed = clean_report_templates()

print(f"\nTotal monetary references removed: {total_removed}")