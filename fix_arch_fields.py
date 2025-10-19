#!/usr/bin/env python3

import re
import os
import glob

# Find all XML files in views and wizard directories
xml_files = []
xml_files.extend(glob.glob('/var/odoo/addons/stock/stock_market_simulation/views/*.xml'))
xml_files.extend(glob.glob('/var/odoo/addons/stock/stock_market_simulation/wizard/*.xml'))

for file_path in xml_files:
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if there are any <field name="arch" type="xml"/> patterns followed by content
    if '<field name="arch" type="xml"/>' in content:
        # Replace self-closing arch field tags with opening tags
        content = re.sub(r'<field name="arch" type="xml"/>', '<field name="arch" type="xml">', content)
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Fixed arch fields in {os.path.basename(file_path)}")

print("All arch field XML issues processed")