# IPO Flows Documentation

## Overview

This document outlines all IPO flows based on the C# source code analysis and the implemented Odoo module. Each flow represents a complete business process in the stock market simulation IPO system.

---

## Flow 1: Creating New Stock as IPO

### Business Purpose
Enable administrators to create new securities in IPO status for initial public offering.

### C# Reference
- **Files**: `stocks` table definition, stock creation forms
- **Key Fields**: `Status='ipo'`, `IPOPrice`, `Quantity`

### Odoo Implementation

#### Step 1: Access Stock Creation
**Path**: Stock Market → Configuration → Securities
**User**: Administrator (Stock Manager group)

#### Step 2: Create New Security
```python
# Model: stock.security
security = self.env['stock.security'].create({
    'name': 'Tesla Inc',
    'symbol': 'TSLA',
    'sector': 'Technology',
    'ipo_status': 'ipo',
    'ipo_price': 250.00,
    'current_offering_quantity': 1000000,
    'total_shares': 1000000,
    'price': 250.00,  # Initial price same as IPO price
})
```

#### Step 3: IPO Status Configuration
- **IPO Status**: Set to 'ipo'
- **IPO Price**: Fixed offering price
- **Offering Quantity**: Shares available for IPO
- **System Percentage**: Admin reserved percentage (from GloableVar.System_percentage)

#### Key Validations
1. IPO price must be positive
2. Offering quantity must be > 0
3. System percentage configuration exists
4. Security symbol is unique

### Portal Interface
**URL**: `/stock/portal/securities`
**View**: Only securities with `ipo_status='ipo'` are visible to brokers

---

## Flow 2: Broker IPO Order Placement for Investors

### Business Purpose
Allow brokers to place IPO orders on behalf of their investor clients.

### C# Reference
- **File**: `AddIPOTransaction.cs`
- **Key Logic**: Broker eligibility check via `ipo_Elig` table, order validation

### Odoo Implementation

#### Step 1: Broker Portal Access
**Path**: `/stock/portal/ipo`
**User**: Broker (portal user)

#### Step 2: Select IPO Security
```javascript
// Frontend: Load available IPO securities
fetch('/stock/api/securities/ipo', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {}
    })
}).then(response => response.json())
```

#### Step 3: Place IPO Order
```python
# Controller: /stock/api/orders/ipo/create
order = self.env['stock.order'].sudo().create({
    'broker_id': broker.id,
    'investor_id': investor.id,
    'security_id': security.id,
    'order_type': 'buy',
    'quantity': 1000,
    'price': security.ipo_price,
    'broker_commission': 0.2,  # 0.2%
    'status': 'pending',
    'description': 'IPO',
    'session_id': current_session.id,
})
```

#### Key Validations
1. Security must be in 'ipo' status
2. Broker must have IPO eligibility for this security
3. Investor must have sufficient funds including broker commission
4. Order quantity must be positive
5. Session must be active

#### Fund Calculation (C# Logic)
```python
# From C#: PriceNeeded = ActualQuantity * IPOPrice * (1 + (BrokerPercentage / 100))
total_cost = quantity * ipo_price * (1 + (broker_commission / 100))
required_funds = total_cost
broker_earnings = quantity * ipo_price * (broker_commission / 100)
```

### Portal Interface Elements
- **Security Selector**: Dropdown of eligible IPO securities
- **Investor Selector**: Broker's assigned investors
- **Quantity Input**: Number of shares to order
- **Commission Display**: Auto-calculated broker commission
- **Total Cost**: Live calculation including commission

---

## Flow 3: IPO Order Processing & Proportional Allocation

### Business Purpose
Process all pending IPO orders when security moves from IPO to Trading status.

### C# Reference
- **File**: `Form1.cs`, method `IPO_Calc()`
- **Key Logic**: Proportional allocation with round-down using `int()` conversion

### Odoo Implementation

#### Step 1: Trigger IPO Processing
**Trigger**: Session end wizard with decision "Move to Trading"
**Method**: `stock.matching.engine.process_ipo_orders()`

#### Step 2: Gather IPO Orders
```python
# Get all pending IPO orders for the security
ipo_orders = self.env['stock.order'].search([
    ('security_id', '=', security_id),
    ('status', '=', 'pending'),
    ('description', '=', 'IPO')
], order='create_date asc')
```

#### Step 3: Calculate Allocation (C# Algorithm)
```python
def process_ipo_orders(self, security_id):
    """
    Implements exact C# proportional allocation logic with round-down
    """
    security = self.env['stock.security'].browse(security_id)
    
    # C#: StockExistQun = total quantity
    total_quantity = security.current_offering_quantity
    
    # C#: System_percentage reserved for admin
    system_percentage = self.env['stock.config'].get_system_percentage()
    distributable_quantity = int(total_quantity * (1 - system_percentage / 100))
    
    # C#: Get total demand
    total_demand = sum(order.quantity for order in ipo_orders)
    
    # C#: Check if oversubscribed
    is_oversubscribed = distributable_quantity < total_demand
    
    allocations = []
    for order in ipo_orders:
        if is_oversubscribed:
            # C#: Proportional allocation with round-down
            # ActualQuantity = (RequestedQuantity * DistributableQuantity) / TotalDemand
            allocated_quantity = int((order.quantity * distributable_quantity) / total_demand)
        else:
            # Full allocation
            allocated_quantity = order.quantity
            
        allocations.append({
            'order': order,
            'allocated_quantity': allocated_quantity,
            'total_cost': allocated_quantity * security.ipo_price,
            'broker_commission': allocated_quantity * security.ipo_price * (order.broker_commission / 100)
        })
    
    return allocations
```

#### Step 4: Execute Allocations
```python
def execute_ipo_allocations(self, allocations):
    """
    Execute the IPO allocations - transfer money and shares
    """
    for allocation in allocations:
        order = allocation['order']
        quantity = allocation['allocated_quantity']
        total_cost = allocation['total_cost']
        commission = allocation['broker_commission']
        
        if quantity > 0:
            # Deduct money from investor
            order.investor_id.update_balance(-total_cost)
            
            # Add commission to broker
            order.broker_id.update_balance(commission)
            
            # Give shares to investor
            self.env['stock.position'].create_or_update_position(
                user_id=order.investor_id.id,
                security_id=order.security_id.id,
                quantity=quantity,
                price=order.security_id.ipo_price
            )
            
            # Mark order as completed
            order.write({
                'status': 'filled',
                'filled_quantity': quantity,
                'average_price': order.security_id.ipo_price
            })
            
            # Create trade record
            self.env['stock.trade'].create({
                'buy_order_id': order.id,
                'security_id': order.security_id.id,
                'quantity': quantity,
                'price': order.security_id.ipo_price,
                'buyer_id': order.investor_id.id,
                'seller_id': False,  # IPO has no seller
                'trade_type': 'ipo'
            })
        else:
            # Failed allocation - insufficient funds or oversubscription
            order.write({'status': 'failed'})
```

#### Step 5: Admin Allocation
```python
# C#: Give remaining shares to admin
allocated_total = sum(alloc['allocated_quantity'] for alloc in allocations)
admin_quantity = total_quantity - allocated_total

if admin_quantity > 0:
    admin_user = self.env.ref('stock_market_simulation.admin_user')
    self.env['stock.position'].create_or_update_position(
        user_id=admin_user.id,
        security_id=security.id,
        quantity=admin_quantity,
        price=security.ipo_price
    )
```

---

## Flow 4: Session-End IPO Status Management

### Business Purpose
Allow administrators to decide IPO security fate at session end.

### C# Reference
- **File**: `Form1.cs`, status change logic for IPO securities
- **Statuses**: 'ipo' → 'trade' or continue as 'ipo' or move to 'po'

### Odoo Implementation

#### Step 1: Session End Wizard
**Path**: Stock Market → Sessions → End Session
**Trigger**: When session ends with active IPO securities

#### Step 2: IPO Decision Interface
```xml
<!-- Wizard: session_end_ipo_wizard -->
<record id="view_session_end_ipo_wizard" model="ir.ui.view">
    <field name="name">Session End IPO Decisions</field>
    <field name="model">session.end.ipo.wizard</field>
    <field name="arch" type="xml">
        <form>
            <group>
                <field name="session_id"/>
                <field name="ipo_decisions" widget="one2many_list">
                    <tree editable="bottom">
                        <field name="security_id"/>
                        <field name="current_status"/>
                        <field name="pending_orders"/>
                        <field name="decision"/>
                        <field name="new_quantity" invisible="decision != 'new_po'"/>
                    </tree>
                </field>
            </group>
            <footer>
                <button name="process_decisions" type="object" string="Process Decisions" class="btn-primary"/>
                <button string="Cancel" class="btn-secondary" special="cancel"/>
            </footer>
        </form>
    </field>
</record>
```

#### Step 3: Decision Options
```python
class SessionEndIpoWizard(models.TransientModel):
    _name = 'session.end.ipo.wizard'
    
    decision = fields.Selection([
        ('continue_ipo', 'Continue IPO (next session)'),
        ('move_to_trading', 'Move to Trading (process orders)'),
        ('new_po', 'Start New PO (additional offering)')
    ])
    
    def process_decisions(self):
        for decision in self.ipo_decisions:
            if decision.decision == 'continue_ipo':
                # Keep status as IPO, orders carry over
                pass
            elif decision.decision == 'move_to_trading':
                # Process IPO orders and change status
                self.env['stock.matching.engine'].process_ipo_orders(decision.security_id.id)
                decision.security_id.write({'ipo_status': 'trading'})
            elif decision.decision == 'new_po':
                # Start new offering round
                decision.security_id.start_po_round(decision.new_quantity)
```

---

## Flow 5: PO Re-issuance (Additional Offering Rounds)

### Business Purpose
Allow securities to return to offering status for additional distribution rounds.

### C# Reference
- **Logic**: Securities can move from 'trade' back to 'po' status for additional offerings

### Odoo Implementation

#### Step 1: PO Re-issuance Interface
**Path**: Stock Market → Securities → [Security] → Start New PO

#### Step 2: PO Configuration
```python
def start_po_round(self, additional_quantity):
    """
    Start a new Public Offering round
    """
    self.write({
        'ipo_status': 'po',
        'current_offering_quantity': additional_quantity,
        'offering_round': self.offering_round + 1,
        'offering_history': self.offering_history + f"\nRound {self.offering_round + 1}: {additional_quantity} shares"
    })
    
    # Log the action
    self.env['stock.price.history'].create({
        'security_id': self.id,
        'price': self.price,
        'change_type': 'po_start',
        'session_id': self.env['stock.session'].get_current_session().id
    })
```

#### Step 3: PO Order Processing
- Same as IPO flow but with status 'po'
- Maintains separate offering rounds
- Tracks offering history

---

## Flow 6: IPO Order Carry-Over Logic

### Business Purpose
Ensure IPO orders persist across sessions until security status changes.

### C# Reference
- **Logic**: IPO orders don't expire at session end, only when status changes

### Odoo Implementation

#### Session End Processing
```python
def end_session(self):
    """
    Modified session end to exclude IPO orders from cancellation
    """
    # Cancel regular orders but preserve IPO orders
    regular_orders = self.env['stock.order'].search([
        ('session_id', '=', self.id),
        ('status', '=', 'pending'),
        ('description', '!=', 'IPO')  # Exclude IPO orders
    ])
    regular_orders.write({'status': 'cancelled'})
    
    # IPO orders remain pending for next session
    ipo_orders = self.env['stock.order'].search([
        ('session_id', '=', self.id),
        ('status', '=', 'pending'),
        ('description', '=', 'IPO')
    ])
    # These orders carry over automatically
```

---

## Flow 7: End-to-End IPO Testing Scenarios

### Test Scenario 1: Basic IPO Flow
1. **Create IPO Security**: TSLA, 1000 shares at $250
2. **Broker Places Orders**: 3 orders totaling 800 shares
3. **Session End**: Move to Trading
4. **Result**: All orders filled, 200 shares to admin

### Test Scenario 2: Oversubscribed IPO
1. **Create IPO Security**: AAPL, 500 shares at $180
2. **Broker Places Orders**: 5 orders totaling 800 shares  
3. **System Percentage**: 10% (50 shares reserved)
4. **Available**: 450 shares for distribution
5. **Result**: Proportional allocation with round-down

### Test Scenario 3: Failed Orders (Insufficient Funds)
1. **Investor Balance**: $1000
2. **IPO Order**: 100 shares at $15 with 0.5% commission
3. **Required**: $1507.50
4. **Result**: Order fails, removed from allocation

### Test Scenario 4: Multiple PO Rounds
1. **Initial IPO**: 1000 shares
2. **Move to Trading**: After IPO processing
3. **New PO**: Additional 500 shares
4. **Track**: offering_round = 2, offering_history updated

---

## Technical Implementation Notes

### Database Schema Enhancements
```sql
-- Enhanced stock.security fields
ALTER TABLE stock_security ADD COLUMN ipo_status VARCHAR(20);
ALTER TABLE stock_security ADD COLUMN ipo_price NUMERIC(10,2);
ALTER TABLE stock_security ADD COLUMN current_offering_quantity BIGINT;
ALTER TABLE stock_security ADD COLUMN offering_round INTEGER DEFAULT 1;
ALTER TABLE stock_security ADD COLUMN offering_history TEXT;
```

### Key Configuration
```python
# System percentage for admin allocation
system_percentage = self.env['stock.config'].get_value('system_percentage', 10.0)

# IPO processing trigger
ipo_processing_enabled = self.env['stock.config'].get_value('ipo_processing', True)
```

### Portal Security
```python
# Access control for IPO features
@http.route('/stock/portal/ipo', auth='user', website=True)
def ipo_portal(self):
    if not request.env.user.has_group('stock_market_simulation.group_broker'):
        return request.not_found()
```

This documentation covers all major IPO flows identified in the C# source code and implemented in the Odoo module.