#!/usr/bin/env python3

import re

file_path = '/var/odoo/addons/stock/stock_market_simulation/views/stock_trade_views.xml'

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Replace all //> with />
content = re.sub(r'//>', '/>', content)

# Write back to file
with open(file_path, 'w') as f:
    f.write(content)

print("Fixed stock_trade_views.xml")