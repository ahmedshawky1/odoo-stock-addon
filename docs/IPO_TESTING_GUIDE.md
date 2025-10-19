# IPO Testing Guide - Step by Step

## Prerequisites

Before testing IPO flows, ensure your Odoo environment is properly set up:

### 1. Database Setup
- Fresh "stock" database with stock_market_simulation module installed
- No cache issues or conflicting data

### 2. User Setup
```python
# Create test users via Odoo interface or data

# Admin User (already exists)
admin = self.env.ref('base.user_admin')

# Broker Users
broker1 = self.env['res.users'].create({
    'name': 'John Broker',
    'login': 'broker1',
    'password': 'broker123',
    'groups_id': [(6, 0, [
        self.env.ref('stock_market_simulation.group_broker').id,
        self.env.ref('base.group_portal').id
    ])]
})

# Investor Users  
investor1 = self.env['res.users'].create({
    'name': 'Alice Investor',
    'login': 'investor1',
    'password': 'investor123',
    'profit': 50000.00,  # $50,000 starting balance
    'groups_id': [(6, 0, [
        self.env.ref('stock_market_simulation.group_investor').id,
        self.env.ref('base.group_portal').id
    ])]
})

investor2 = self.env['res.users'].create({
    'name': 'Bob Investor', 
    'login': 'investor2',
    'password': 'investor123',
    'profit': 25000.00,  # $25,000 starting balance
    'groups_id': [(6, 0, [
        self.env.ref('stock_market_simulation.group_investor').id,
        self.env.ref('base.group_portal').id
    ])]
})
```

### 3. Session Setup
```python
# Create active trading session
session = self.env['stock.session'].create({
    'name': 'IPO Test Session 1',
    'start_time': fields.Datetime.now(),
    'status': 'active'
})
```

---

## Test Flow 1: Creating IPO Stock

### Objective
Test the creation of a new security in IPO status and verify all IPO-specific fields are properly configured.

### Steps

#### Step 1: Login as Admin
1. Navigate to `http://localhost:8069`
2. Login with admin credentials
3. Verify access to Stock Market menu

#### Step 2: Create IPO Security
1. **Navigate**: Stock Market → Configuration → Securities
2. **Click**: Create
3. **Fill Form**:
   ```
   Name: Tesla Inc
   Symbol: TSLA
   Sector: Technology
   IPO Status: IPO
   IPO Price: 250.00
   Current Offering Quantity: 1000
   Total Shares: 1000
   Price: 250.00
   ```
4. **Save** the record

#### Step 3: Verify IPO Configuration
1. **Check Fields**:
   - ✓ `ipo_status` = 'ipo'
   - ✓ `ipo_price` = 250.00
   - ✓ `current_offering_quantity` = 1000
   - ✓ `offering_round` = 1
   - ✓ `can_accept_ipo_orders()` returns True

#### Step 4: Test Portal Visibility
1. **Logout** as admin
2. **Login** as broker1
3. **Navigate** to portal IPO page
4. **Verify**: TSLA appears in available IPO securities list

### Expected Results
- ✅ Security created with IPO status
- ✅ All IPO fields properly configured
- ✅ Security visible to brokers in portal
- ✅ IPO validation methods work correctly

---

## Test Flow 2: Broker IPO Order Placement

### Objective
Test the complete broker order placement flow including validation, fund checking, and order creation.

### Steps

#### Step 1: Setup Broker-Investor Relationship
1. **Login** as admin
2. **Navigate**: Stock Market → Configuration → Broker Assignments
3. **Create Assignment**:
   ```
   Broker: John Broker
   Investor: Alice Investor
   ```

#### Step 2: Broker Portal Order Placement
1. **Login** as broker1 (John Broker)
2. **Navigate**: Portal → IPO Orders
3. **Fill IPO Order Form**:
   ```
   Security: TSLA (Tesla Inc)
   Investor: Alice Investor
   Quantity: 100
   Broker Commission: 0.5%
   ```

#### Step 3: Verify Order Calculations
**Expected Calculations**:
```python
ipo_price = 250.00
quantity = 100
broker_commission = 0.5%

total_cost = 100 * 250.00 * (1 + 0.5/100) = $25,125.00
broker_earnings = 100 * 250.00 * (0.5/100) = $125.00
investor_cost = $25,125.00
```

#### Step 4: Submit Order
1. **Click**: Place Order
2. **Verify**: Success message appears
3. **Check**: Order appears in pending orders list

#### Step 5: Database Verification
```python
# Check order was created correctly
order = self.env['stock.order'].search([
    ('broker_id.login', '=', 'broker1'),
    ('investor_id.login', '=', 'investor1'),
    ('security_id.symbol', '=', 'TSLA')
], limit=1)

assert order.status == 'pending'
assert order.description == 'IPO'
assert order.quantity == 100
assert order.price == 250.00
assert order.broker_commission == 0.5
```

### Expected Results
- ✅ Order form validates inputs correctly
- ✅ Fund calculation matches C# logic
- ✅ Order created with proper status and description
- ✅ Order persists in database with correct values

---

## Test Flow 3: Multiple IPO Orders (Oversubscription)

### Objective
Test the system behavior when total IPO demand exceeds available shares.

### Steps

#### Step 1: Create Multiple Orders
**Order 1** (Broker1 → Investor1):
```
Security: TSLA
Quantity: 400
Commission: 0.5%
Total Cost: 400 * $250 * 1.005 = $100,500
```

**Order 2** (Broker1 → Investor2):
```
Security: TSLA  
Quantity: 500
Commission: 0.3%
Total Cost: 500 * $250 * 1.003 = $125,375
```

**Order 3** (Create another broker/investor):
```
Security: TSLA
Quantity: 300
Commission: 0.2%
Total Cost: 300 * $250 * 1.002 = $75,150
```

#### Step 2: Verify Orders Status
1. **Total Demand**: 400 + 500 + 300 = 1200 shares
2. **Available Supply**: 1000 shares
3. **System Percentage**: 10% (100 shares reserved for admin)
4. **Distributable**: 900 shares
5. **Status**: Oversubscribed (1200 > 900)

#### Step 3: Check Fund Validation
- Investor1 balance: $50,000 ≥ $100,500 ❌ (Should fail)
- Investor2 balance: $25,000 ≥ $125,375 ❌ (Should fail)

**Note**: Adjust investor balances or order quantities for testing.

### Expected Results
- ✅ System detects oversubscription
- ✅ Orders with insufficient funds are filtered out
- ✅ Remaining orders queued for proportional allocation

---

## Test Flow 4: IPO Processing & Allocation

### Objective
Test the core IPO allocation algorithm with proportional distribution and round-down logic.

### Steps

#### Step 1: Setup Test Scenario
**Adjusted Orders** (with sufficient funds):
```
Order 1: 300 shares (Investor with $80,000 balance)
Order 2: 400 shares (Investor with $110,000 balance)  
Order 3: 200 shares (Investor with $60,000 balance)
Total Demand: 900 shares
Available: 900 shares (perfect match)
```

#### Step 2: Trigger IPO Processing
1. **Login** as admin
2. **Navigate**: Stock Market → Sessions → End Session
3. **IPO Decision Wizard** appears
4. **Select**: Move to Trading for TSLA
5. **Click**: Process Decisions

#### Step 3: Verify Allocation Calculations
**Expected Allocation** (no oversubscription):
```python
# Perfect match scenario
allocations = {
    'order_1': 300,  # Full allocation
    'order_2': 400,  # Full allocation  
    'order_3': 200,  # Full allocation
    'admin': 100     # System percentage (10%)
}
```

**Oversubscribed Scenario** (if 1200 demand vs 900 available):
```python
# Proportional with round-down
distributable = 900
total_demand = 1200

allocation_1 = int((300 * 900) / 1200) = int(225.0) = 225
allocation_2 = int((400 * 900) / 1200) = int(300.0) = 300  
allocation_3 = int((200 * 900) / 1200) = int(150.0) = 150

total_allocated = 225 + 300 + 150 = 675
admin_gets = 1000 - 675 = 325 (including system percentage)
```

#### Step 4: Verify Database Updates
```python
# Check trades were created
trades = self.env['stock.trade'].search([
    ('security_id.symbol', '=', 'TSLA'),
    ('trade_type', '=', 'ipo')
])

# Check positions were created
for trade in trades:
    position = self.env['stock.position'].search([
        ('user_id', '=', trade.buyer_id.id),
        ('security_id', '=', trade.security_id.id)
    ])
    assert position.quantity == trade.quantity

# Check money was deducted
# Check broker commissions were paid
# Check security status changed to 'trading'
```

### Expected Results
- ✅ Proportional allocation follows C# int() round-down logic
- ✅ Money transfers execute correctly
- ✅ Broker commissions calculated and paid
- ✅ Stock positions created for investors
- ✅ Admin receives remaining shares
- ✅ Security status changes to 'trading'
- ✅ Orders marked as 'filled'

---

## Test Flow 5: Session-End IPO Decisions

### Objective
Test the three IPO decision options: Continue IPO, Move to Trading, New PO.

### Steps

#### Step 1: Create Multiple IPO Securities
```python
# Security 1: Will continue IPO
tsla = create_ipo_security('TSLA', 1000, 250.00)

# Security 2: Will move to trading  
aapl = create_ipo_security('AAPL', 500, 180.00)

# Security 3: Will start new PO
msft = create_ipo_security('MSFT', 800, 300.00)
```

#### Step 2: Place Orders on Each
- Place some orders on each security
- Leave some with no orders
- Mix of scenarios

#### Step 3: End Session with Decisions
1. **Trigger**: End Session
2. **IPO Wizard** shows all IPO securities
3. **Make Decisions**:
   ```
   TSLA: Continue IPO
   AAPL: Move to Trading  
   MSFT: New PO (additional 200 shares)
   ```

#### Step 4: Verify Outcomes
**TSLA (Continue IPO)**:
- ✓ Status remains 'ipo'
- ✓ Orders remain 'pending'
- ✓ Available in next session

**AAPL (Move to Trading)**:
- ✓ IPO orders processed
- ✓ Status changes to 'trading'
- ✓ Orders marked 'filled' or 'failed'

**MSFT (New PO)**:
- ✓ Status changes to 'po'
- ✓ offering_round incremented
- ✓ current_offering_quantity = 200
- ✓ offering_history updated

### Expected Results
- ✅ Each decision type works correctly
- ✅ Status transitions follow business logic
- ✅ Order processing selective per decision
- ✅ PO rounds tracked properly

---

## Test Flow 6: Order Carry-Over Logic

### Objective
Verify that IPO orders persist across sessions while regular orders are cancelled.

### Steps

#### Step 1: Create Mixed Orders
1. **IPO Orders**: Place IPO orders on securities in 'ipo' status
2. **Regular Orders**: Place buy/sell orders on securities in 'trading' status

#### Step 2: End Session Without IPO Processing
1. **End Session** but choose "Continue IPO" for all IPO securities
2. **Verify**: Regular orders are cancelled
3. **Verify**: IPO orders remain pending

#### Step 3: Start New Session
1. **Create** new session
2. **Check**: IPO orders still visible and pending
3. **Check**: Regular orders are gone

#### Step 4: Test IPO Order Expiration
1. **End Session** and choose "Move to Trading" for IPO security
2. **Verify**: IPO orders get processed (not cancelled)
3. **Verify**: Orders marked as 'filled' or 'failed', not 'cancelled'

### Expected Results
- ✅ IPO orders survive session transitions
- ✅ Regular orders cancelled at session end
- ✅ IPO orders only processed when status changes
- ✅ No IPO orders lost during carry-over

---

## Test Flow 7: PO Re-issuance

### Objective
Test additional offering rounds for securities already in trading.

### Steps

#### Step 1: Complete Initial IPO
1. **Create** IPO security
2. **Process** through to trading status
3. **Verify** security is actively trading

#### Step 2: Initiate New PO
1. **Navigate**: Securities → [Security] → Actions
2. **Select**: Start New PO
3. **Configure**:
   ```
   Additional Quantity: 500
   Keep Current Price: Yes
   ```

#### Step 3: Verify PO Configuration
```python
security = self.env['stock.security'].search([('symbol', '=', 'TSLA')])
assert security.ipo_status == 'po'
assert security.current_offering_quantity == 500
assert security.offering_round == 2
assert 'Round 2' in security.offering_history
```

#### Step 4: Place PO Orders
1. **Portal**: Should now show security as available for PO orders
2. **Place Orders**: Similar to IPO flow
3. **Process**: Through session-end wizard

#### Step 5: Multiple Rounds
1. **Repeat** PO process multiple times
2. **Verify**: offering_round increments correctly
3. **Verify**: offering_history maintains complete record

### Expected Results
- ✅ Trading securities can return to PO status
- ✅ Offering rounds tracked separately
- ✅ Complete offering history maintained
- ✅ Multiple PO rounds supported
- ✅ Each round independent of previous

---

## Comprehensive End-to-End Test

### Objective
Test complete IPO lifecycle from creation to multiple offering rounds.

### Timeline

#### Session 1: IPO Creation & Initial Orders
1. **Admin**: Create TSLA IPO (1000 shares @ $250)
2. **Brokers**: Place various IPO orders
3. **End Session**: Choose "Continue IPO"
4. **Verify**: Orders carry over

#### Session 2: IPO Processing  
1. **Additional Orders**: Place more IPO orders
2. **End Session**: Choose "Move to Trading"
3. **Verify**: Proportional allocation works
4. **Verify**: Security now trading

#### Session 3-5: Regular Trading
1. **Regular Orders**: Normal buy/sell orders
2. **Price Changes**: Security price fluctuates
3. **Trading Activity**: Active market

#### Session 6: First PO Round
1. **Admin**: Start New PO (500 additional shares)
2. **Brokers**: Place PO orders
3. **End Session**: Process PO orders
4. **Verify**: offering_round = 2

#### Session 7-10: More Trading
1. **Continue Trading**: Regular market activity

#### Session 11: Second PO Round
1. **Admin**: Start another PO (300 shares)  
2. **Process**: Complete PO cycle
3. **Verify**: offering_round = 3

### Final Verification
```python
# Check complete lifecycle
security = self.env['stock.security'].search([('symbol', '=', 'TSLA')])

# Should have history of all offering rounds
assert security.offering_round >= 3
assert 'Round 1' in security.offering_history
assert 'Round 2' in security.offering_history  
assert 'Round 3' in security.offering_history

# Should have multiple trade records
trades = self.env['stock.trade'].search([('security_id', '=', security.id)])
ipo_trades = trades.filtered(lambda t: t.trade_type == 'ipo')
po_trades = trades.filtered(lambda t: t.trade_type == 'po')

assert len(ipo_trades) > 0
assert len(po_trades) > 0

# Should have active positions
positions = self.env['stock.position'].search([('security_id', '=', security.id)])
assert len(positions) > 0
```

---

## Common Issues & Troubleshooting

### Issue 1: Orders Not Appearing in Portal
**Cause**: User permissions or security status
**Check**: 
- User has broker group
- Security has ipo_status = 'ipo' or 'po'
- Session is active

### Issue 2: Fund Validation Failing
**Cause**: Insufficient investor balance
**Fix**: Update investor profit field or reduce order quantity

### Issue 3: Allocation Algorithm Incorrect
**Cause**: Floating point precision or wrong int() conversion
**Check**: Ensure using int() for round-down, not round()

### Issue 4: Orders Not Carrying Over
**Cause**: Session end logic cancelling IPO orders
**Check**: Filter logic excludes description='IPO'

### Issue 5: PO Not Starting
**Cause**: Security status or permissions
**Check**: Security is in 'trading' status and user has admin rights

This testing guide ensures comprehensive validation of all IPO flows against the C# reference implementation.