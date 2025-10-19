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
    
    # Check if there are any //> patterns
    if '//>' in content:
        # Replace all //> with />
        content = re.sub(r'//>', '/>', content)
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Fixed {os.path.basename(file_path)}")

print("All XML files processed")