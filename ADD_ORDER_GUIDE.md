# How to Add Orders from Backend - Step by Step Guide

## Issue: Cannot Find "New" Button in Orders

### Quick Fix Checklist

1. **Are you in the right menu?**
   - ✅ Use: **Stock Market → Trading → Orders** (has "New" button)
   - ❌ Avoid: **Stock Market → Trading → Order Book** (read-only view)

2. **Do you have the right permissions?**
   - You need **Investor** or **Administrator** role
   - **Broker** role cannot create orders

3. **Is there an active trading session?**
   - Orders can only be created when a session is "Open"

---

## Method 1: Using Odoo Backend (GUI)

### Step 1: Assign User Permissions

Run this in Odoo shell or create a Python script:

```python
# Give a user the Investor role
user = env['res.users'].browse(2)  # Replace 2 with your user ID
investor_group = env.ref('stock_market_simulation.group_stock_investor')
user.groups_id = [(4, investor_group.id)]
```

**OR via GUI:**
1. Settings → Users & Companies → Users
2. Open your user
3. Go to "Stock Market Trading" tab
4. Check "Investor" checkbox
5. Click "Save"

### Step 2: Create an Active Trading Session

Before creating orders, you need an active session:

```python
# Create and open a session
session = env['stock.session'].create({
    'name': 'Trading Session Oct 2025',
    'start_date': fields.Datetime.now(),
    'end_date': fields.Datetime.now() + timedelta(hours=8),
})
session.action_start()  # Opens the session
```

**OR via GUI:**
1. Stock Market → Administration → Trading Sessions
2. Click "New"
3. Fill in name and dates
4. Click "Save"
5. Click "Start Session" button

### Step 3: Create an Order

Now navigate to:
- **Stock Market → Trading → Orders**
- Click **"New"** button
- Fill in the form:
  - **Trader**: Select user (defaults to you)
  - **Trading Session**: Select the OPEN session
  - **Security**: Select stock to trade
  - **Side**: Buy or Sell
  - **Order Type**: Market or Limit
  - **Quantity**: Number of shares
  - **Price**: Price per share (for limit orders)
- Click **"Submit Order"** in the header

---

## Method 2: Using Python/Shell

### Complete Example

```python
# 1. Ensure user has investor role
user = env['res.users'].browse(2)
investor_group = env.ref('stock_market_simulation.group_stock_investor')
if investor_group.id not in user.groups_id.ids:
    user.groups_id = [(4, investor_group.id)]

# 2. Find or create an open session
session = env['stock.session'].search([('state', '=', 'open')], limit=1)
if not session:
    session = env['stock.session'].create({
        'name': 'Test Session',
        'start_date': fields.Datetime.now(),
        'end_date': fields.Datetime.now() + timedelta(hours=8),
    })
    session.action_start()

# 3. Get a security
security = env['stock.security'].search([('active', '=', True)], limit=1)

# 4. Give user some cash (for buy orders)
user.cash_balance = 100000.0

# 5. Create and submit order
order = env['stock.order'].create({
    'user_id': user.id,
    'session_id': session.id,
    'security_id': security.id,
    'side': 'buy',
    'order_type': 'limit',
    'price': 100.0,
    'quantity': 100,
})

# 6. Submit the order
order.action_submit()

print(f"Order created: {order.name}")
print(f"Status: {order.status}")
```

---

## Method 3: Fix Missing "New" Button

If you're an admin and the "New" button is still missing, check the list view:

### Check the View Definition

The main order list view should NOT have `create="false"`:

```xml
<!-- This is CORRECT -->
<record id="view_stock_order_tree" model="ir.ui.view">
    <field name="name">stock.order.tree</field>
    <field name="model">stock.order</field>
    <field name="arch" type="xml">
        <list string="Orders">  <!-- No create="false" here -->
            <field name="name"/>
            <!-- ... -->
        </list>
    </field>
</record>
```

The Order Book view has `create="false"` which is intentional:
```xml
<!-- This is for Order Book only - read-only -->
<record id="view_stock_order_book_tree" model="ir.ui.view">
    <field name="name">stock.order.book.tree</field>
    <field name="model">stock.order</field>
    <field name="arch" type="xml">
        <list string="Order Book" create="false" delete="false">
            <!-- ... -->
        </list>
    </field>
</record>
```

---

## Method 4: Create Order via Terminal/Script

```bash
# Run Odoo shell
sudo docker exec -it odoo_stock odoo shell -d stock

# Then in Python shell:
from odoo import fields
from datetime import timedelta

# Setup
user = env['res.users'].browse(2)
investor_group = env.ref('stock_market_simulation.group_stock_investor')
user.groups_id = [(4, investor_group.id)]

# Create session
session = env['stock.session'].create({
    'name': 'Test Session',
    'start_date': fields.Datetime.now(),
    'end_date': fields.Datetime.now() + timedelta(hours=8),
})
session.action_start()

# Get security
security = env['stock.security'].search([('active', '=', True)], limit=1)

# Fund user
user.cash_balance = 100000.0

# Create order
order = env['stock.order'].create({
    'user_id': user.id,
    'session_id': session.id,
    'security_id': security.id,
    'side': 'buy',
    'order_type': 'limit',
    'price': 100.0,
    'quantity': 100,
})
order.action_submit()

env.cr.commit()
print(f"Success! Order: {order.name}")
```

---

## Troubleshooting

### "New" button is grayed out or missing

**Check:**
1. You're in "Orders" not "Order Book"
2. You have Investor or Admin role
3. No domain filters are active that hide the button

### "Cannot submit order to a closed session"

**Fix:**
- Create a new session or open an existing one
- Session must have state = 'open'

### "Insufficient funds"

**Fix:**
```python
user = env['res.users'].browse(YOUR_USER_ID)
user.cash_balance = 100000.0
```

### "Insufficient shares" (for sell orders)

**Fix:** First buy shares or create a position:
```python
env['stock.position'].create({
    'user_id': YOUR_USER_ID,
    'security_id': SECURITY_ID,
    'quantity': 1000,
    'average_price': 100.0,
})
```

---

## Quick Test Script

```python
# Complete test script to create an order from scratch
from odoo import fields
from datetime import timedelta

# 1. Setup user as investor with cash
user_id = 2  # Change this to your user ID
user = env['res.users'].browse(user_id)
investor_group = env.ref('stock_market_simulation.group_stock_investor')
user.groups_id = [(4, investor_group.id)]
user.cash_balance = 100000.0

# 2. Create and open session
session = env['stock.session'].create({
    'name': f'Test Session {fields.Date.today()}',
    'start_date': fields.Datetime.now(),
    'end_date': fields.Datetime.now() + timedelta(hours=8),
})
session.action_start()

# 3. Create or get security
security = env['stock.security'].search([('active', '=', True)], limit=1)
if not security:
    security = env['stock.security'].create({
        'name': 'Test Stock',
        'symbol': 'TEST',
        'current_price': 100.0,
        'total_shares': 10000,
        'active': True,
    })

# 4. Create and submit order
order = env['stock.order'].create({
    'user_id': user.id,
    'session_id': session.id,
    'security_id': security.id,
    'side': 'buy',
    'order_type': 'limit',
    'price': 100.0,
    'quantity': 10,
})
order.action_submit()

# 5. Commit and verify
env.cr.commit()
print(f"✓ Order created: {order.name}")
print(f"✓ Status: {order.status}")
print(f"✓ User cash balance: ${user.cash_balance:,.2f}")
print(f"\nNow go to: Stock Market → Trading → Orders to see your order!")
```

---

## Need More Help?

After running the setup, restart and upgrade:
```bash
sudo docker restart odoo_stock
sudo docker exec -it odoo_stock odoo -u stock_market_simulation -d stock --stop-after-init
```

Then login and navigate to **Stock Market → Trading → Orders** and you should see the "New" button!
