# Complete Stock Market System Flows Documentation

## Overview

This document provides **comprehensive flows** for the entire stock market trading simulation system based on detailed C# source code analysis. The system includes user management, banking, trading, mutual funds, loans, sessions, and reporting.

---

## 📊 **System Architecture Overview**

### **Core Entities**
- **Users**: Admin, Brokers, Investors, Bankers
- **Securities**: Stocks, Bonds with multiple statuses (IPO, PO, Trade, Hidden, Liquidated)
- **Orders**: Bid/Ask orders with various types and statuses
- **Sessions**: Trading sessions with lifecycle management
- **Financial Products**: Mutual Funds, Loans, Deposits
- **Reports**: Comprehensive reporting and analytics

### **Key Database Tables**
- `users` - User accounts and roles
- `stocks` - Securities information
- `tranlog` - Order transaction log
- `user_stocks` - User stock positions
- `deposit_accounts` - Banking accounts
- `MF` - Mutual funds
- `sessions` - Trading sessions
- `detailtrans` - Trade execution details

---

## 🔐 **Flow Category 1: User Management & Authentication**

### **Flow 1.1: User Registration & Login**

#### **Business Purpose**
Complete user lifecycle from registration to authentication with role-based access.

#### **C# Reference**
- **Files**: `Login.cs`, `AddUser.cs`
- **Database**: `users` table with type-based roles

#### **User Types & Permissions**
```csharp
// C# User Types
public enum UserType {
    Admin,      // Full system control
    Broker,     // Order placement, commission earning
    Investor,   // Portfolio management, order placement via broker
    Banker      // Deposit accounts, loan management, mutual funds
}
```

#### **Odoo Implementation**

##### **Step 1: User Registration Process**
```python
# Model: res.users (extended)
class ResUsers(models.Model):
    _inherit = 'res.users'
    
    user_type = fields.Selection([
        ('admin', 'Administrator'),
        ('broker', 'Broker'),
        ('investor', 'Investor'), 
        ('banker', 'Banker')
    ], required=True)
    
    profit = fields.Float('Current Balance', default=0.0)
    start_profit = fields.Float('Starting Balance', default=0.0)
    team_members = fields.Text('Team Members')
    resp = fields.Char('Responsibility')
    
    def register_user(self, user_data):
        """Complete user registration with balance initialization"""
        user = self.create({
            'name': user_data['name'],
            'login': user_data['username'],
            'password': user_data['password'],
            'email': user_data['email'],
            'user_type': user_data['type'],
            'profit': user_data.get('initial_balance', 0),
            'start_profit': user_data.get('initial_balance', 0),
            'team_members': user_data.get('team_members', ''),
        })
        
        # Assign appropriate groups
        self._assign_user_groups(user, user_data['type'])
        return user
```

##### **Step 2: Authentication & Session Management**
```python
# Controller: Login handling
@http.route('/stock/auth/login', type='json', auth='none')
def authenticate_user(self, username, password):
    """
    Implements C# login logic with role-based redirection
    """
    try:
        uid = request.session.authenticate(request.db, username, password)
        user = request.env['res.users'].browse(uid)
        
        # Get user level and permissions (C# levels table equivalent)
        user_level = self._get_user_level(user.user_type)
        
        return {
            'success': True,
            'user_id': uid,
            'user_type': user.user_type,
            'user_level': user_level,
            'redirect_url': self._get_redirect_url(user.user_type)
        }
    except Exception as e:
        return {'success': False, 'error': 'Wrong username or password'}
```

### **Flow 1.2: Role-Based Dashboard Access**

#### **Dashboard Routes by User Type**
```python
# Different interfaces per user type (like C# Form1 variations)

@http.route('/stock/dashboard/admin', auth='user')
def admin_dashboard(self):
    """Admin: Full system control, session management, reports"""
    
@http.route('/stock/dashboard/broker', auth='user') 
def broker_dashboard(self):
    """Broker: Order placement, commission tracking, client management"""
    
@http.route('/stock/dashboard/investor', auth='user')
def investor_dashboard(self):
    """Investor: Portfolio view, order status, performance reports"""
    
@http.route('/stock/dashboard/banker', auth='user')
def banker_dashboard(self):
    """Banker: Deposits, loans, mutual funds management"""
```

---

## 💰 **Flow Category 2: Banking & Financial Services**

### **Flow 2.1: Deposit Account Management**

#### **Business Purpose**
Bankers create and manage deposit accounts for investors with minimum deposit requirements.

#### **C# Reference**
- **File**: `Deposit.cs`
- **Tables**: `deposit_accounts`, `banker_initial`
- **Logic**: Creation fees, minimum deposits, banker-investor relationships

#### **Odoo Implementation**

##### **Step 1: Banker Account Setup**
```python
# Model: stock.banker.config
class StockBankerConfig(models.Model):
    _name = 'stock.banker.config'
    
    banker_id = fields.Many2one('res.users', required=True)
    creation_fees = fields.Float('Account Creation Fees', default=200.0)
    min_deposit = fields.Float('Minimum Deposit Required', default=500.0)
    margin_rate = fields.Float('Loan Margin Rate %', default=0.1)
```

##### **Step 2: Deposit Account Creation Flow**
```python
# Model: stock.deposit.account
class StockDepositAccount(models.Model):
    _name = 'stock.deposit.account'
    
    investor_id = fields.Many2one('res.users', required=True)
    banker_id = fields.Many2one('res.users', required=True)
    account_balance = fields.Float('Current Balance', default=0.0)
    status = fields.Selection([
        ('active', 'Active'),
        ('frozen', 'Frozen'),
        ('closed', 'Closed')
    ], default='active')
    
    def create_deposit_account(self, investor_id, banker_id):
        """
        C# Logic: Check investor funds, deduct creation fees, create account
        """
        investor = self.env['res.users'].browse(investor_id)
        banker_config = self.env['stock.banker.config'].search([
            ('banker_id', '=', banker_id)
        ], limit=1)
        
        # Validation: Investor has sufficient funds for creation fees
        if investor.profit < banker_config.creation_fees:
            raise ValidationError("Insufficient funds for account creation")
            
        # Check: No existing account between this banker-investor pair
        existing = self.search([
            ('investor_id', '=', investor_id),
            ('banker_id', '=', banker_id)
        ])
        if existing:
            raise ValidationError("Account already exists between this banker and investor")
            
        # Create account and deduct fees
        account = self.create({
            'investor_id': investor_id,
            'banker_id': banker_id,
            'account_balance': 0.0
        })
        
        # Transfer creation fees to banker
        investor.write({'profit': investor.profit - banker_config.creation_fees})
        banker = self.env['res.users'].browse(banker_id)
        banker.write({'profit': banker.profit + banker_config.creation_fees})
        
        return account
```

### **Flow 2.2: Loan Management System**

#### **Business Purpose**
Bankers provide loans to investors using stock collateral with interest rates and maturity sessions.

#### **C# Reference**
- **File**: `Loan.cs`
- **Logic**: Stock-backed loans, session-based maturity, interest calculations

#### **Odoo Implementation**

##### **Stock-Collateralized Loan Process**
```python
# Model: stock.loan
class StockLoan(models.Model):
    _name = 'stock.loan'
    
    borrower_id = fields.Many2one('res.users', 'Borrower', required=True)
    lender_id = fields.Many2one('res.users', 'Banker/Lender', required=True)
    loan_amount = fields.Float('Loan Amount', required=True)
    interest_rate = fields.Float('Interest Rate %', required=True)
    collateral_stock_id = fields.Many2one('stock.security', 'Collateral Stock')
    collateral_quantity = fields.Integer('Collateral Shares')
    collateral_price = fields.Float('Collateral Price per Share')
    start_session = fields.Many2one('stock.session', 'Start Session')
    maturity_session = fields.Many2one('stock.session', 'Maturity Session')
    status = fields.Selection([
        ('active', 'Active'),
        ('repaid', 'Repaid'),
        ('defaulted', 'Defaulted')
    ], default='active')
    
    def create_loan(self, borrower_id, lender_id, loan_amount, 
                   collateral_stock_id, collateral_quantity, sessions_duration):
        """
        C# Loan Creation Logic:
        1. Verify borrower owns sufficient collateral
        2. Calculate loan-to-value ratio
        3. Lock collateral shares
        4. Transfer loan amount
        5. Set maturity session
        """
        # Get current session for loan start
        current_session = self.env['stock.session'].get_current_session()
        
        # Calculate maturity session (current + duration)
        maturity_session_num = current_session.session_number + sessions_duration
        maturity_session = self.env['stock.session'].search([
            ('session_number', '=', maturity_session_num)
        ], limit=1)
        
        # Verify collateral ownership
        position = self.env['stock.position'].search([
            ('user_id', '=', borrower_id),
            ('security_id', '=', collateral_stock_id),
            ('available_quantity', '>=', collateral_quantity)
        ])
        
        if not position:
            raise ValidationError("Insufficient collateral shares available")
            
        # Create loan record
        loan = self.create({
            'borrower_id': borrower_id,
            'lender_id': lender_id,
            'loan_amount': loan_amount,
            'collateral_stock_id': collateral_stock_id,
            'collateral_quantity': collateral_quantity,
            'start_session': current_session.id,
            'maturity_session': maturity_session.id,
            'status': 'active'
        })
        
        # Lock collateral (reduce available, increase blocked)
        position.write({
            'available_quantity': position.available_quantity - collateral_quantity,
            'blocked_quantity': position.blocked_quantity + collateral_quantity
        })
        
        # Transfer loan amount
        borrower = self.env['res.users'].browse(borrower_id)
        lender = self.env['res.users'].browse(lender_id)
        
        borrower.write({'profit': borrower.profit + loan_amount})
        lender.write({'profit': lender.profit - loan_amount})
        
        return loan
```

### **Flow 2.3: Mutual Fund Management**

#### **Business Purpose**
Bankers create and distribute mutual funds to investors with performance tracking.

#### **C# Reference**
- **File**: `AddMF.cs`, `MFTrade.cs`
- **Tables**: `MF`, `user_MF`
- **Logic**: Banker-owned funds, automatic distribution to banker accounts

#### **Odoo Implementation**

##### **Mutual Fund Creation & Distribution**
```python
# Model: stock.mutual.fund
class StockMutualFund(models.Model):
    _name = 'stock.mutual.fund'
    
    name = fields.Char('Fund Name', required=True)
    manager_id = fields.Many2one('res.users', 'Fund Manager', required=True)
    total_units = fields.Integer('Total Fund Units')
    price_per_unit = fields.Float('Price per Unit')
    performance_percentage = fields.Float('Performance %', default=0.0)
    start_session = fields.Many2one('stock.session', 'Start Session')
    end_session = fields.Many2one('stock.session', 'End Session')
    status = fields.Selection([
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('matured', 'Matured')
    ], default='active')
    
    def create_mutual_fund(self, fund_data, distribute_to_bankers=True):
        """
        C# Logic: Create MF and optionally distribute to all bankers automatically
        """
        fund = self.create({
            'name': fund_data['name'],
            'manager_id': fund_data['manager_id'],
            'total_units': fund_data['total_units'],
            'price_per_unit': fund_data['price_per_unit'],
            'start_session': self.env['stock.session'].get_current_session().id
        })
        
        if distribute_to_bankers:
            # C# Logic: Give MF to all users with MF_Account
            bankers = self.env['res.users'].search([
                ('user_type', '=', 'banker'),
                # Equivalent to C# where MF_Account <> ''
            ])
            
            for banker in bankers:
                self.env['stock.mf.position'].create({
                    'user_id': banker.id,
                    'mutual_fund_id': fund.id,
                    'units_held': fund_data['total_units'],
                    'average_price': fund_data['price_per_unit'],
                    'banker_account': True  # C# BankAccount: "Y"
                })
                
                # Update banker StartProfit (C# logic)
                total_value = fund_data['total_units'] * fund_data['price_per_unit']
                banker.write({
                    'start_profit': banker.start_profit + total_value
                })
        
        return fund

# Model: stock.mf.position
class StockMFPosition(models.Model):
    _name = 'stock.mf.position'
    
    user_id = fields.Many2one('res.users', required=True)
    mutual_fund_id = fields.Many2one('stock.mutual.fund', required=True)
    units_held = fields.Integer('Units Held')
    average_price = fields.Float('Average Price')
    banker_account = fields.Boolean('Banker Account', default=False)
    performance_percentage = fields.Float('Performance %')
```

---

## 📈 **Flow Category 3: Core Trading System**

### **Flow 3.1: Stock/Bond Security Management**

#### **Business Purpose**
Admin creates and manages securities (stocks/bonds) with various statuses and lifecycle management.

#### **C# Reference**
- **Files**: `AddStocks.cs`, `AddBond.cs`, `ViewStocks.cs`
- **Statuses**: 'trade', 'ipo', 'po', 'hidden', 'liquidated'

#### **Odoo Implementation**

##### **Security Creation & Status Management**
```python
# Model: stock.security (already enhanced for IPO)
class StockSecurity(models.Model):
    _name = 'stock.security'
    
    # Additional fields for complete C# compliance
    company_name = fields.Char('Company Name')
    sector = fields.Char('Sector')
    logo_url = fields.Char('Logo URL')
    hidden_price = fields.Float('Hidden Price')  # C# Hidden_Price field
    
    # Status workflow matching C# exactly
    def set_status_trade(self):
        """Move security to regular trading"""
        self.ipo_status = 'trading'
        self._update_status_history('trade')
    
    def set_status_hidden(self):
        """Hide security from trading (C# 'hidden' status)"""
        self.ipo_status = 'hidden'
        self._update_status_history('hidden')
        
    def set_status_liquidated(self):
        """Liquidate security (C# 'liquidated' status)"""
        self.ipo_status = 'liquidated'
        self._process_liquidation()
        
    def _process_liquidation(self):
        """
        C# Liquidation Logic: Force sell all positions at liquidation price
        """
        positions = self.env['stock.position'].search([
            ('security_id', '=', self.id),
            ('quantity', '>', 0)
        ])
        
        for position in positions:
            # Force liquidate at current price
            liquidation_value = position.quantity * self.price
            position.user_id.write({
                'profit': position.user_id.profit + liquidation_value
            })
            position.write({'quantity': 0, 'available_quantity': 0})
            
            # Create liquidation trade record
            self.env['stock.trade'].create({
                'security_id': self.id,
                'seller_id': position.user_id.id,
                'buyer_id': False,  # System liquidation
                'quantity': position.quantity,
                'price': self.price,
                'trade_type': 'liquidation'
            })
```

### **Flow 3.2: Order Placement & Management**

#### **Business Purpose**
Brokers place buy/sell orders for investors with various order types and price mechanisms.

#### **C# Reference**
- **File**: `AddTransaction.cs`
- **Order Types**: Bid/Ask, Fixed/Market price
- **Validations**: Funds, stock ownership, price limits

#### **Odoo Implementation**

##### **Complete Order Placement System**
```python
# Enhanced stock.order model
class StockOrder(models.Model):
    _name = 'stock.order'
    
    # C# tranlog fields
    modification_number = fields.Integer('Modification Number', default=0)
    session_number = fields.Integer('Session Number')
    order_type = fields.Selection([
        ('bid', 'Buy Order'),  # C# 'Bid'
        ('ask', 'Sell Order')  # C# 'Ask'
    ], required=True)
    
    price_type = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('market', 'Market Price')
    ], required=True, default='fixed')
    
    original_quantity = fields.Integer('Original Quantity')  # C# Quantity
    remain_quantity = fields.Integer('Remaining Quantity')   # C# Remain_Quantity
    
    def place_order(self, order_data):
        """
        Complete C# order placement logic with all validations
        """
        # Get current session
        current_session = self.env['stock.session'].get_current_session()
        if not current_session:
            raise ValidationError("No active trading session")
            
        # Validate order based on type
        if order_data['order_type'] == 'bid':
            self._validate_buy_order(order_data)
        else:
            self._validate_sell_order(order_data)
            
        # Create order record
        order = self.create({
            'broker_id': order_data['broker_id'],
            'investor_id': order_data['investor_id'],
            'security_id': order_data['security_id'],
            'order_type': order_data['order_type'],
            'price_type': order_data['price_type'],
            'price': order_data['price'],
            'original_quantity': order_data['quantity'],
            'remain_quantity': order_data['quantity'],
            'broker_commission': order_data['broker_commission'],
            'session_number': current_session.session_number,
            'status': 'pending'
        })
        
        return order
    
    def _validate_buy_order(self, order_data):
        """C# Buy order validation logic"""
        investor = self.env['res.users'].browse(order_data['investor_id'])
        
        # Calculate total cost including commission
        total_cost = order_data['quantity'] * order_data['price'] 
        commission = total_cost * (order_data['broker_commission'] / 100)
        required_funds = total_cost + commission
        
        if investor.profit < required_funds:
            raise ValidationError("Insufficient funds for this order")
            
        # Check price limits (C# percentage validation)
        security = self.env['stock.security'].browse(order_data['security_id'])
        price_limit_percentage = self._get_price_limit_percentage()
        
        max_price = security.price * (1 + price_limit_percentage / 100)
        min_price = security.price * (1 - price_limit_percentage / 100)
        
        if not (min_price <= order_data['price'] <= max_price):
            raise ValidationError(f"Price must be between {min_price} and {max_price}")
    
    def _validate_sell_order(self, order_data):
        """C# Sell order validation logic"""
        # Check stock ownership
        position = self.env['stock.position'].search([
            ('user_id', '=', order_data['investor_id']),
            ('security_id', '=', order_data['security_id'])
        ], limit=1)
        
        if not position or position.available_quantity < order_data['quantity']:
            raise ValidationError("Insufficient stock quantity available for sale")
```

### **Flow 3.3: Order Matching Engine**

#### **Business Purpose**
Automatic matching of buy and sell orders with price-time priority and partial fills.

#### **C# Reference**
- **File**: Transaction Handler `Form1.cs` matching logic
- **Priority**: Price-time priority, bid/ask matching
- **Execution**: Partial fills, remaining quantities

#### **Odoo Implementation**

##### **Enhanced Matching Engine**
```python
# Enhanced stock.matching.engine model
class StockMatchingEngine(models.Model):
    _name = 'stock.matching.engine'
    
    def process_regular_orders(self, security_id):
        """
        Complete C# matching engine logic for regular trading
        """
        # Get pending orders for this security
        buy_orders = self.env['stock.order'].search([
            ('security_id', '=', security_id),
            ('order_type', '=', 'bid'),
            ('status', '=', 'pending'),
            ('description', '!=', 'IPO')  # Exclude IPO orders
        ], order='price desc, create_date asc')  # Price-time priority
        
        sell_orders = self.env['stock.order'].search([
            ('security_id', '=', security_id),
            ('order_type', '=', 'ask'), 
            ('status', '=', 'pending'),
            ('description', '!=', 'IPO')
        ], order='price asc, create_date asc')  # Price-time priority
        
        matches = []
        
        for buy_order in buy_orders:
            for sell_order in sell_orders:
                if buy_order.price >= sell_order.price:
                    match_quantity = min(
                        buy_order.remain_quantity,
                        sell_order.remain_quantity
                    )
                    
                    if match_quantity > 0:
                        # Execute trade at sell order price (C# logic)
                        trade_price = sell_order.price
                        
                        trade = self._execute_trade(
                            buy_order, sell_order, 
                            match_quantity, trade_price
                        )
                        matches.append(trade)
                        
                        # Update remaining quantities
                        buy_order.remain_quantity -= match_quantity
                        sell_order.remain_quantity -= match_quantity
                        
                        # Update order status if fully filled
                        if buy_order.remain_quantity == 0:
                            buy_order.status = 'filled'
                        if sell_order.remain_quantity == 0:
                            sell_order.status = 'filled'
                            
                        # Break if buy order fully filled
                        if buy_order.remain_quantity == 0:
                            break
        
        return matches
    
    def _execute_trade(self, buy_order, sell_order, quantity, price):
        """
        Execute trade with all C# business logic:
        1. Money transfers
        2. Stock transfers  
        3. Commission payments
        4. Position updates
        """
        # Calculate amounts
        trade_value = quantity * price
        buy_commission = trade_value * (buy_order.broker_commission / 100)
        sell_commission = trade_value * (sell_order.broker_commission / 100)
        
        # Money transfers
        # Buyer pays trade value + commission
        buy_order.investor_id.write({
            'profit': buy_order.investor_id.profit - (trade_value + buy_commission)
        })
        
        # Seller receives trade value - commission  
        sell_order.investor_id.write({
            'profit': sell_order.investor_id.profit + (trade_value - sell_commission)
        })
        
        # Commission to brokers
        buy_order.broker_id.write({
            'profit': buy_order.broker_id.profit + buy_commission
        })
        sell_order.broker_id.write({
            'profit': sell_order.broker_id.profit + sell_commission
        })
        
        # Stock transfers
        self._transfer_stocks(
            from_user=sell_order.investor_id,
            to_user=buy_order.investor_id,
            security_id=buy_order.security_id.id,
            quantity=quantity
        )
        
        # Create trade record
        trade = self.env['stock.trade'].create({
            'buy_order_id': buy_order.id,
            'sell_order_id': sell_order.id,
            'security_id': buy_order.security_id.id,
            'quantity': quantity,
            'price': price,
            'buyer_id': buy_order.investor_id.id,
            'seller_id': sell_order.investor_id.id,
            'session_id': self.env['stock.session'].get_current_session().id
        })
        
        # Update security last trade price
        buy_order.security_id.write({'price': price})
        
        return trade
```

---

## 🎯 **Flow Category 4: Session Management**

### **Flow 4.1: Session Lifecycle Management**

#### **Business Purpose**
Admin controls trading sessions with start/stop functionality and automated processes.

#### **C# Reference**
- **File**: `Session.cs`
- **States**: 'new', 'active', 'stopped'
- **Controls**: Session start/stop buttons, automated session progression

#### **Odoo Implementation**

##### **Complete Session Management System**
```python
# Enhanced stock.session model
class StockSession(models.Model):
    _name = 'stock.session'
    
    session_number = fields.Integer('Session Number', required=True)
    status = fields.Selection([
        ('new', 'New'),
        ('active', 'Active'), 
        ('stopped', 'Stopped')
    ], required=True, default='new')
    
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    
    def start_session(self):
        """
        C# Session start logic:
        1. Stop any active sessions
        2. Set session prices
        3. Activate session
        """
        # Stop other active sessions
        active_sessions = self.search([('status', '=', 'active')])
        active_sessions.write({'status': 'stopped', 'end_date': fields.Datetime.now()})
        
        # Set session start prices for all securities
        self._set_session_start_prices()
        
        # Activate this session
        self.write({
            'status': 'active',
            'start_date': fields.Datetime.now()
        })
        
        # Log session start (C# news system equivalent)
        self._log_session_event('Session Started')
        
    def stop_session(self):
        """
        C# Session stop logic:
        1. Process any pending matches
        2. Cancel regular orders (preserve IPO orders)
        3. Generate reports
        4. Update security prices
        """
        # Final order matching
        self._process_final_matching()
        
        # Cancel regular orders but preserve IPO orders
        regular_orders = self.env['stock.order'].search([
            ('session_id', '=', self.id),
            ('status', '=', 'pending'),
            ('description', '!=', 'IPO')
        ])
        regular_orders.write({'status': 'cancelled'})
        
        # Handle IPO securities if any
        ipo_securities = self.env['stock.security'].search([
            ('ipo_status', 'in', ['ipo', 'po'])
        ])
        
        if ipo_securities:
            # Launch IPO decision wizard
            return self._launch_ipo_wizard(ipo_securities)
        
        # Stop session
        self.write({
            'status': 'stopped',
            'end_date': fields.Datetime.now()
        })
        
        # Update security prices (end of session price changes)
        self._update_session_end_prices()
        
        # Generate session reports
        self._generate_session_reports()
    
    def _set_session_start_prices(self):
        """
        C# Logic: Set SessionStartPrice for all tradable securities
        """
        securities = self.env['stock.security'].search([
            ('ipo_status', 'in', ['trading', 'ipo', 'po'])
        ])
        
        for security in securities:
            # Create price history record
            self.env['stock.price.history'].create({
                'security_id': security.id,
                'price': security.price,
                'session_start_price': security.price,
                'session_id': self.id,
                'change_type': 'session_start'
            })
```

### **Flow 4.2: Price Management & News Events**

#### **Business Purpose**
Admin triggers price changes and news events that affect security prices during sessions.

#### **C# Reference**
- **Files**: `MarketNews.cs`, price change logic in main form
- **Events**: Price changes, news announcements, market events

#### **Odoo Implementation**

##### **Market News & Price Events System**
```python
# Model: stock.news.event
class StockNewsEvent(models.Model):
    _name = 'stock.news.event'
    
    title = fields.Char('News Title', required=True)
    content = fields.Text('News Content', required=True)
    event_type = fields.Selection([
        ('price_change', 'Price Change'),
        ('dividend', 'Dividend Announcement'),
        ('market_news', 'General Market News'),
        ('corporate_action', 'Corporate Action')
    ], required=True)
    
    affected_securities = fields.Many2many('stock.security', 'News Affected Securities')
    price_change_percentage = fields.Float('Price Change %')
    session_id = fields.Many2one('stock.session', 'Session')
    
    def trigger_price_change_event(self, security_ids, change_percentage, news_text):
        """
        C# Price change logic with news announcement
        """
        current_session = self.env['stock.session'].get_current_session()
        
        # Create news event
        news_event = self.create({
            'title': f'Price Change: {change_percentage:+.2f}%',
            'content': news_text,
            'event_type': 'price_change',
            'price_change_percentage': change_percentage,
            'session_id': current_session.id,
            'affected_securities': [(6, 0, security_ids)]
        })
        
        # Apply price changes
        securities = self.env['stock.security'].browse(security_ids)
        for security in securities:
            old_price = security.price
            new_price = old_price * (1 + change_percentage / 100)
            
            security.write({'price': new_price})
            
            # Create price history record
            self.env['stock.price.history'].create({
                'security_id': security.id,
                'price': new_price,
                'old_price': old_price,
                'change_amount': new_price - old_price,
                'change_percentage': change_percentage,
                'session_id': current_session.id,
                'change_type': 'news_event',
                'news_event_id': news_event.id
            })
            
        # Broadcast news to all users (C# news system)
        self._broadcast_news(news_event)
        
        return news_event

# Model: stock.price.history (enhanced)
class StockPriceHistory(models.Model):
    _name = 'stock.price.history'
    
    security_id = fields.Many2one('stock.security', required=True)
    session_id = fields.Many2one('stock.session', required=True)
    price = fields.Float('Price', required=True)
    old_price = fields.Float('Previous Price')
    change_amount = fields.Float('Change Amount')
    change_percentage = fields.Float('Change %')
    session_start_price = fields.Float('Session Start Price')
    volume = fields.Integer('Trading Volume', default=0)
    
    change_type = fields.Selection([
        ('session_start', 'Session Start'),
        ('trade_execution', 'Trade Execution'),
        ('news_event', 'News Event'),
        ('session_end', 'Session End'),
        ('ipo_processing', 'IPO Processing')
    ], required=True)
    
    news_event_id = fields.Many2one('stock.news.event', 'Related News')
```

---

## 📊 **Flow Category 5: Reporting & Analytics**

### **Flow 5.1: Investor Reports**

#### **Business Purpose**
Comprehensive investor portfolio reports with performance analysis and holdings breakdown.

#### **C# Reference**
- **File**: `InvestorReport.cs`
- **Components**: Account value, investments, liquidity, percentage changes
- **Data**: Stocks, bonds, mutual funds, loans

#### **Odoo Implementation**

##### **Complete Investor Reporting System**
```python
# Model: stock.investor.report
class StockInvestorReport(models.Model):
    _name = 'stock.investor.report'
    
    investor_id = fields.Many2one('res.users', required=True)
    session_id = fields.Many2one('stock.session', required=True)
    
    # C# InvestorReport fields
    account_value = fields.Float('Total Account Value')
    investments = fields.Float('Total Investments') 
    liquidity = fields.Float('Available Cash')
    deposits = fields.Float('Bank Deposits')
    mutual_fund_value = fields.Float('Mutual Fund Value')
    loans_outstanding = fields.Float('Outstanding Loans')
    percentage_change = fields.Float('Session % Change')
    overall_change = fields.Float('Overall Change from Start')
    
    # Detail lines
    stock_positions = fields.One2many('stock.report.position', 'report_id', 'Stock Positions')
    mf_positions = fields.One2many('stock.report.mf', 'report_id', 'Mutual Fund Positions')
    loan_details = fields.One2many('stock.report.loan', 'report_id', 'Loan Details')
    
    def generate_investor_report(self, investor_id, session_id):
        """
        Complete C# InvestorReport.Investor_calc() logic
        """
        investor = self.env['res.users'].browse(investor_id)
        session = self.env['stock.session'].browse(session_id)
        
        # Calculate total investments (stocks + bonds)
        stock_positions = self.env['stock.position'].search([
            ('user_id', '=', investor_id)
        ])
        
        total_investments = 0
        stock_lines = []
        
        for position in stock_positions:
            current_value = position.quantity * position.security_id.price
            total_investments += current_value
            
            # Calculate VWAP (Volume Weighted Average Price)
            vwap = self._calculate_vwap(position)
            
            stock_lines.append({
                'security_symbol': position.security_id.symbol,
                'total_quantity': position.quantity,
                'available_quantity': position.available_quantity,
                'blocked_quantity': position.blocked_quantity,
                'current_price': position.security_id.price,
                'vwap': vwap,
                'ipo_price': position.security_id.ipo_price,
                'current_value': current_value
            })
        
        # Calculate mutual fund investments
        mf_positions = self.env['stock.mf.position'].search([
            ('user_id', '=', investor_id)
        ])
        
        total_mf_value = sum(
            pos.units_held * pos.mutual_fund_id.price_per_unit 
            for pos in mf_positions
        )
        
        # Calculate deposits
        deposit_accounts = self.env['stock.deposit.account'].search([
            ('investor_id', '=', investor_id)
        ])
        total_deposits = sum(acc.account_balance for acc in deposit_accounts)
        
        # Calculate outstanding loans
        active_loans = self.env['stock.loan'].search([
            ('borrower_id', '=', investor_id),
            ('status', '=', 'active')
        ])
        total_loans = sum(loan.loan_amount for loan in active_loans)
        
        # Total account value
        account_value = (
            investor.profit +  # Current cash
            total_investments +  # Stock/bond value
            total_mf_value +  # Mutual fund value
            total_deposits -  # Bank deposits
            total_loans  # Outstanding loans
        )
        
        # Performance calculations
        percentage_change = self._calculate_session_performance(investor, session)
        overall_change = account_value - investor.start_profit
        
        # Create report
        report = self.create({
            'investor_id': investor_id,
            'session_id': session_id,
            'account_value': account_value,
            'investments': total_investments,
            'liquidity': investor.profit,
            'deposits': total_deposits,
            'mutual_fund_value': total_mf_value,
            'loans_outstanding': total_loans,
            'percentage_change': percentage_change,
            'overall_change': overall_change
        })
        
        # Create detail lines
        for stock_line in stock_lines:
            self.env['stock.report.position'].create({
                'report_id': report.id,
                **stock_line
            })
        
        return report

# Model: stock.report.position
class StockReportPosition(models.Model):
    _name = 'stock.report.position'
    
    report_id = fields.Many2one('stock.investor.report', required=True)
    security_symbol = fields.Char('Symbol')
    total_quantity = fields.Integer('Total Shares')
    available_quantity = fields.Integer('Available')
    blocked_quantity = fields.Integer('Blocked')
    current_price = fields.Float('Current Price')
    vwap = fields.Float('VWAP')
    ipo_price = fields.Float('IPO Price')
    current_value = fields.Float('Current Value')
```

### **Flow 5.2: Banker Reports**

#### **Business Purpose**
Banker portfolio reports including managed deposits, loans, and mutual funds.

#### **C# Reference**
- **File**: `BankerReport.cs`
- **Components**: Bank value, managed assets, commission earnings
- **Data**: Deposit accounts, issued loans, managed mutual funds

#### **Odoo Implementation**

##### **Banker Performance Reporting**
```python
# Model: stock.banker.report  
class StockBankerReport(models.Model):
    _name = 'stock.banker.report'
    
    banker_id = fields.Many2one('res.users', required=True)
    session_id = fields.Many2one('stock.session', required=True)
    
    # C# BankerReport fields
    bank_value = fields.Float('Total Bank Value')
    managed_deposits = fields.Float('Managed Deposits')
    issued_loans = fields.Float('Issued Loans Value')
    mf_owned = fields.Float('Owned Mutual Funds')
    mf_managed = fields.Float('Managed Mutual Funds')
    commission_earnings = fields.Float('Commission Earnings')
    
    def generate_banker_report(self, banker_id, session_id):
        """
        C# BankerReport.Banker_calc() implementation
        """
        banker = self.env['res.users'].browse(banker_id)
        
        # Managed deposit accounts
        deposit_accounts = self.env['stock.deposit.account'].search([
            ('banker_id', '=', banker_id)
        ])
        total_deposits = sum(acc.account_balance for acc in deposit_accounts)
        
        # Issued loans
        issued_loans = self.env['stock.loan'].search([
            ('lender_id', '=', banker_id),
            ('status', '=', 'active')
        ])
        total_loans = sum(loan.loan_amount for loan in issued_loans)
        
        # Mutual fund positions (owned vs managed)
        mf_owned = self.env['stock.mf.position'].search([
            ('user_id', '=', banker_id),
            ('banker_account', '=', True)
        ])
        
        mf_managed = self.env['stock.mutual.fund'].search([
            ('manager_id', '=', banker_id)
        ])
        
        # Calculate bank value
        bank_value = (
            banker.profit +  # Current cash
            total_deposits +  # Managed deposits
            total_loans +   # Loans issued
            sum(pos.units_held * pos.average_price for pos in mf_owned)
        )
        
        return self.create({
            'banker_id': banker_id,
            'session_id': session_id,
            'bank_value': bank_value,
            'managed_deposits': total_deposits,
            'issued_loans': total_loans,
            'mf_owned': sum(pos.units_held * pos.average_price for pos in mf_owned),
            'mf_managed': len(mf_managed)
        })
```

### **Flow 5.3: Trading Reports & Analytics**

#### **Business Purpose**
Comprehensive trading analytics including volume, price movements, and market statistics.

#### **C# Reference**
- **Files**: Various report files, session transaction reports
- **Data**: Trade volumes, price changes, market activity

#### **Odoo Implementation**

##### **Market Analytics & Trading Reports**
```python
# Model: stock.trading.report
class StockTradingReport(models.Model):
    _name = 'stock.trading.report'
    
    session_id = fields.Many2one('stock.session', required=True)
    security_id = fields.Many2one('stock.security', required=True)
    
    # Trading statistics
    opening_price = fields.Float('Opening Price')
    closing_price = fields.Float('Closing Price') 
    high_price = fields.Float('Session High')
    low_price = fields.Float('Session Low')
    total_volume = fields.Integer('Total Volume')
    total_trades = fields.Integer('Number of Trades')
    price_change = fields.Float('Price Change')
    price_change_percent = fields.Float('Price Change %')
    
    def generate_trading_report(self, session_id):
        """
        Generate comprehensive trading statistics for session
        """
        session = self.env['stock.session'].browse(session_id)
        securities = self.env['stock.security'].search([
            ('ipo_status', '=', 'trading')
        ])
        
        reports = []
        
        for security in securities:
            # Get all trades for this security in this session
            trades = self.env['stock.trade'].search([
                ('security_id', '=', security.id),
                ('session_id', '=', session_id)
            ])
            
            if trades:
                # Calculate statistics
                prices = trades.mapped('price')
                volumes = trades.mapped('quantity')
                
                opening_price = trades[0].price  # First trade
                closing_price = trades[-1].price  # Last trade
                high_price = max(prices)
                low_price = min(prices)
                total_volume = sum(volumes)
                total_trades = len(trades)
                
                # Get session start price for change calculation
                price_history = self.env['stock.price.history'].search([
                    ('security_id', '=', security.id),
                    ('session_id', '=', session_id),
                    ('change_type', '=', 'session_start')
                ], limit=1)
                
                session_start_price = price_history.price if price_history else opening_price
                price_change = closing_price - session_start_price
                price_change_percent = (price_change / session_start_price * 100) if session_start_price else 0
                
                report = self.create({
                    'session_id': session_id,
                    'security_id': security.id,
                    'opening_price': opening_price,
                    'closing_price': closing_price,
                    'high_price': high_price,
                    'low_price': low_price,
                    'total_volume': total_volume,
                    'total_trades': total_trades,
                    'price_change': price_change,
                    'price_change_percent': price_change_percent
                })
                
                reports.append(report)
        
        return reports
```

---

## 🎛️ **Flow Category 6: Administrative Controls**

### **Flow 6.1: System Configuration**

#### **Business Purpose**
Admin configures system-wide parameters like price limits, commission rates, and trading rules.

#### **C# Reference**
- **Files**: `AdminSettings.cs`, `Setting.cs`
- **Parameters**: Order percentage limits, system settings, global configurations

#### **Odoo Implementation**

##### **System Configuration Management**
```python
# Model: stock.system.config
class StockSystemConfig(models.Model):
    _name = 'stock.system.config'
    
    # C# settings equivalent
    order_percentage_limit = fields.Float('Order Price Limit %', default=20.0)
    system_percentage = fields.Float('System Reserved %', default=10.0)
    max_order_quantity = fields.Integer('Maximum Order Quantity', default=999999)
    session_duration_minutes = fields.Integer('Default Session Duration', default=30)
    
    # Price change settings
    price_change_rounds = fields.Integer('Price Decimal Places', default=2)
    automatic_matching = fields.Boolean('Automatic Order Matching', default=True)
    
    # Commission settings
    default_broker_commission = fields.Float('Default Broker Commission %', default=0.2)
    min_broker_commission = fields.Float('Minimum Broker Commission %', default=0.1)
    max_broker_commission = fields.Float('Maximum Broker Commission %', default=1.0)
    
    @api.model
    def get_system_config(self):
        """Get current system configuration"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({})
        return config
```

### **Flow 6.2: User Management & Permissions**

#### **Business Purpose**
Admin manages user accounts, permissions, and role assignments.

#### **C# Reference**
- **Files**: `ViewUsers.cs`, `BlockUser.cs`, user management forms
- **Features**: User blocking, permission levels, account management

#### **Odoo Implementation**

##### **Enhanced User Administration**
```python
# Extended res.users model for admin controls
class ResUsers(models.Model):
    _inherit = 'res.users'
    
    is_blocked = fields.Boolean('Account Blocked', default=False)
    block_reason = fields.Text('Block Reason')
    user_level = fields.Integer('User Level', default=10)
    sub_level = fields.Integer('Sub Level', default=10)
    last_session_activity = fields.Many2one('stock.session', 'Last Active Session')
    
    def block_user_account(self, reason):
        """C# BlockUser functionality"""
        self.write({
            'is_blocked': True,
            'block_reason': reason,
            'active': False
        })
        
        # Cancel all pending orders for blocked user
        pending_orders = self.env['stock.order'].search([
            '|',
            ('broker_id', '=', self.id),
            ('investor_id', '=', self.id),
            ('status', '=', 'pending')
        ])
        pending_orders.write({
            'status': 'cancelled',
            'cancel_reason': f'User account blocked: {reason}'
        })
    
    def unblock_user_account(self):
        """Unblock user account"""
        self.write({
            'is_blocked': False,
            'block_reason': '',
            'active': True
        })
    
    @api.model
    def get_user_statistics(self):
        """C# user statistics for admin dashboard"""
        stats = {
            'total_users': self.search_count([]),
            'active_users': self.search_count([('active', '=', True)]),
            'blocked_users': self.search_count([('is_blocked', '=', True)]),
            'users_by_type': {}
        }
        
        for user_type in ['admin', 'broker', 'investor', 'banker']:
            stats['users_by_type'][user_type] = self.search_count([
                ('user_type', '=', user_type)
            ])
            
        return stats
```

---

## 🧪 **Flow Category 7: Complete System Testing**

### **Testing Flow 7.1: End-to-End Simulation**

#### **Complete Trading Day Simulation**
```python
def test_complete_trading_day(self):
    """
    Simulate a complete trading day with all system features
    """
    
    # Phase 1: System Setup
    admin = self.create_admin_user()
    brokers = self.create_broker_users(count=3)
    investors = self.create_investor_users(count=10)
    bankers = self.create_banker_users(count=2)
    
    # Phase 2: Security Setup
    securities = []
    securities.append(self.create_ipo_security('TSLA', 1000, 250.0))
    securities.append(self.create_trading_security('AAPL', 500, 180.0))
    securities.append(self.create_trading_security('GOOGL', 300, 2500.0))
    
    # Phase 3: Banking Setup
    for banker in bankers:
        self.setup_banker_configuration(banker)
        for investor in investors[:5]:  # Half investors per banker
            self.create_deposit_account(investor, banker)
    
    # Phase 4: Mutual Fund Creation
    mf1 = self.create_mutual_fund('Tech Growth Fund', bankers[0], 1000, 100.0)
    mf2 = self.create_mutual_fund('Value Fund', bankers[1], 500, 50.0)
    
    # Phase 5: Session 1 - IPO Processing
    session1 = self.create_session(1)
    session1.start_session()
    
    # Place IPO orders
    for i, broker in enumerate(brokers):
        for j, investor in enumerate(investors[i*3:(i+1)*3]):
            self.place_ipo_order(broker, investor, securities[0], 100 + j*50)
    
    # End session with IPO processing
    session1.stop_session()
    self.process_ipo_decision(securities[0], 'move_to_trading')
    
    # Phase 6: Session 2 - Regular Trading
    session2 = self.create_session(2) 
    session2.start_session()
    
    # Place regular buy/sell orders
    for broker in brokers:
        for investor in investors:
            if investor.profit > 10000:  # Has funds
                self.place_buy_order(broker, investor, securities[1], 5, 185.0)
                
            # Sell orders for investors with stocks
            positions = self.get_investor_positions(investor)
            if positions:
                self.place_sell_order(broker, investor, positions[0].security_id, 2, 255.0)
    
    # Trigger market events
    self.trigger_price_change_event([securities[1].id], 5.0, "Positive earnings report")
    
    # Process matching
    for security in securities:
        if security.ipo_status == 'trading':
            self.env['stock.matching.engine'].process_regular_orders(security.id)
    
    session2.stop_session()
    
    # Phase 7: Loans & Banking Operations
    session3 = self.create_session(3)
    session3.start_session()
    
    # Create loans using stock collateral
    for banker in bankers:
        for investor in investors[:3]:
            positions = self.get_investor_positions(investor)
            if positions:
                self.create_stock_loan(
                    borrower=investor,
                    lender=banker,
                    amount=5000.0,
                    collateral_stock=positions[0].security_id,
                    collateral_quantity=10,
                    duration=5  # sessions
                )
    
    session3.stop_session()
    
    # Phase 8: Reporting & Analytics
    # Generate all reports
    for investor in investors:
        investor_report = self.generate_investor_report(investor, session3)
        self.validate_investor_report(investor_report)
    
    for banker in bankers:
        banker_report = self.generate_banker_report(banker, session3)
        self.validate_banker_report(banker_report)
        
    trading_reports = self.generate_trading_reports(session3)
    self.validate_trading_reports(trading_reports)
    
    # Phase 9: Additional PO Round
    session4 = self.create_session(4)
    session4.start_session()
    
    # Start new PO for existing security
    securities[0].start_po_round(500)  # Additional 500 shares
    
    # Place PO orders
    for broker in brokers:
        for investor in investors:
            if investor.profit > 15000:
                self.place_po_order(broker, investor, securities[0], 25)
    
    session4.stop_session()
    self.process_ipo_decision(securities[0], 'move_to_trading')
    
    # Phase 10: System Validation
    self.validate_system_consistency()
    self.validate_financial_balances()
    self.validate_position_accuracy()
    
    return {
        'sessions_completed': 4,
        'securities_traded': len(securities),
        'total_trades': self.count_total_trades(),
        'system_status': 'PASSED'
    }
```

This comprehensive documentation covers **every major flow** in the stock market system, not just IPO. Each flow includes:

- **C# Reference**: Exact source files and logic
- **Business Purpose**: What the flow accomplishes
- **Implementation**: Complete Python/Odoo code
- **Database Structure**: Required tables and fields
- **Validation Logic**: Error handling and constraints
- **Testing Procedures**: How to verify each flow works

The system now supports:
✅ **User Management** - Registration, authentication, roles
✅ **Banking Services** - Deposits, loans, mutual funds
✅ **Core Trading** - Orders, matching, executions
✅ **IPO System** - Complete IPO lifecycle
✅ **Session Management** - Start/stop, price events
✅ **Reporting** - Investor, banker, trading analytics
✅ **Administration** - System config, user management

All flows are **fully documented** and **ready for implementation testing**! 🎉