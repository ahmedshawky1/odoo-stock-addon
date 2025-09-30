# Stock Market Trading Simulator - Complete Documentation

**Version:** 1.0  
**Odoo Version:** 18.0  
**Status:** Production Ready ✅

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [User Guide](#user-guide)
6. [Technical Reference](#technical-reference)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

---

## Overview

A comprehensive Odoo 18 module providing complete stock market trading simulation with advanced features for order management, settlement, banking, and reporting. Successfully converted from a C# trading system to Python/Odoo.

### Key Highlights
- **Full Trading System** with price-time priority matching engine
- **Multiple Order Types** (Market, Limit, Stop Loss, Stop Limit)
- **Banking Integration** (Deposits, Loans, Margin Calls)
- **Multi-role Support** (Investors, Brokers, Bankers, Administrators)
- **Real-time Portal** with live updates
- **Comprehensive Reporting** suite
- **Risk Management** with circuit breakers

---

## Features

### Trading System
- **Order Types**: Market, Limit, Stop Loss, Stop Limit
- **Time in Force**: Day, GTC, IOC, FOK
- **Matching Engine**: Price-time priority with concurrent handling
- **Settlement**: T+2 configurable settlement period
- **Position Tracking**: Real-time P&L calculations
- **Commission System**: Broker commission tracking

### Banking Features
- **Deposits**: Savings, Fixed Term, Recurring
- **Loans**: Personal, Margin, Secured
- **Interest Calculations**: Automatic daily interest
- **Margin Calls**: Automated collateral liquidation
- **Default Handling**: Penalty calculations and enforcement

### User Roles
1. **Investors**: Trade securities, manage portfolio, banking operations
2. **Brokers**: View client orders, track commissions
3. **Bankers**: Manage deposits and loans
4. **Administrators**: System configuration and management

### Risk Management
- Daily trading limits per user
- Position limits per security
- Margin call automation (70% threshold)
- Circuit breakers on price movements
- Trading halts on excessive volatility

---

## Installation

### Prerequisites
```bash
- Odoo 18.0+
- PostgreSQL 12+
- Python 3.8+
- 4GB RAM minimum
- 10GB disk space
```

### Quick Install

1. **Copy Module to Addons**
```bash
cd /path/to/odoo/addons
git clone <repository-url> stock
# or
cp -r stock /path/to/odoo/addons/
```

2. **Install via Odoo**
```bash
# Update module list
./odoo-bin -u stock -d your_database --stop-after-init

# Or install via UI:
# Apps → Update Apps List → Search "Stock Market Trading Simulator" → Install
```

3. **Verify Installation**
```bash
# Check logs for errors
tail -f /var/log/odoo/odoo.log

# Access portal
http://your-server:8069/my
```

### Demo Data
Module includes comprehensive demo data:
- 4 users (investor, broker, banker, admin)
- 5 securities (AAPL, GOOGL, MSFT, TSLA, Bond)
- Active trading session
- Sample orders and deposits

---

## Configuration

### Initial Setup

#### 1. System Configuration
Navigate to: **Stock Market → Configuration → Configuration**

Key parameters:
```
Margin Call Threshold: 70%
Settlement Days: T+2
Commission Rate: 0.5%
Daily Trading Limit: $500,000
Min Order Value: $100
Max Order Value: $1,000,000
```

#### 2. Create Securities
**Stock Market → Market Data → Securities**

Required fields:
- Symbol (e.g., AAPL)
- Name (e.g., Apple Inc.)
- Type (stock/bond/mf)
- Current Price
- Tick Size (min price increment)
- Lot Size (min quantity)

#### 3. User Setup
**Settings → Users & Companies → Users**

For each user:
1. Set User Type (investor/broker/banker/admin)
2. Assign Security Groups (automatic)
3. For investors: Assign Broker
4. Set Initial Capital

#### 4. Create Trading Session
**Stock Market → Administration → Trading Sessions**

Required:
- Session Name
- Start/End Date & Time
- Price Change Threshold
- Commission Rates
- Trading Limits

---

## User Guide

### For Investors

#### Accessing the Portal
```
URL: http://your-server:8069/my
Login with your credentials
```

#### Dashboard Features
- **Cash Balance**: Available funds
- **Portfolio Value**: Current holdings value
- **Total Assets**: Cash + Portfolio
- **P&L**: Profit/Loss with percentage

#### Placing Orders
1. Navigate to `/my/order/new`
2. Select Security
3. Choose Order Type (Market/Limit/Stop)
4. Enter Quantity and Price
5. Select Time in Force
6. Submit Order

**Order Types:**
- **Market**: Execute immediately at current price
- **Limit**: Execute at specified price or better
- **Stop Loss**: Trigger sell when price reaches stop price
- **Stop Limit**: Convert to limit order when stop price reached

#### Managing Portfolio
**View Positions:** `/my/portfolio`
- Current holdings
- Average cost
- Current value
- P&L per position

#### Banking Operations
**Deposits:** `/my/deposits`
- Apply for new deposits
- Track maturity dates
- View interest earned

**Loans:** `/my/loans`
- Apply for loans
- Make payments
- View outstanding balance

### For Brokers

#### Commission Tracking
**Navigate to:** `/my/commissions`
- Total commissions earned
- Commission by session
- Recent trades with commission details

#### Client Monitoring
- View client orders
- Track trading activity
- Commission reports

### For Bankers

#### Deposit Management
- Approve deposit applications
- Process maturities
- Calculate interest

#### Loan Management
- Approve loan applications
- Monitor overdue payments
- Execute margin calls
- Process defaults

### For Administrators

#### Session Management
**Stock Market → Administration → Trading Sessions**
- Create new sessions
- Open/Close sessions
- Monitor trading activity

#### System Configuration
**Stock Market → Configuration**
- Adjust trading parameters
- Set risk limits
- Configure commission rates

#### Monitoring
- View all orders and trades
- Track user activities
- Generate system reports

---

## Technical Reference

### Architecture

#### Models (11 core models)
```python
stock.session        # Trading sessions
stock.security       # Stocks, bonds, mutual funds
stock.order          # Buy/sell orders
stock.trade          # Executed trades
stock.matching_engine # Order matching logic
stock.position       # User positions
stock.price_history  # Historical prices
stock.deposit        # Banking deposits
stock.loan           # Banking loans
stock.config         # System configuration
res.users (extended) # User extensions
```

#### Key Features

**Order Matching Algorithm:**
```python
# Price-Time Priority
1. Market orders execute first
2. Buy orders: Highest price first
3. Sell orders: Lowest price first
4. Same price: Earlier timestamp wins
```

**Settlement Process:**
```python
# T+2 Settlement
Trade Date → T+0: Order matched
Trade Date + 2 → T+2: Settlement executed
- Shares transferred
- Cash transferred
- Positions updated
```

**Margin Call Logic:**
```python
# Automatic margin calls
If collateral_value / loan_amount < 70%:
  1. Send notification
  2. Grace period: 24 hours
  3. Auto-liquidate collateral
```

### Database Schema

#### Key Relationships
```
res.users (1) ──→ (N) stock.order
res.users (1) ──→ (N) stock.position
stock.session (1) ──→ (N) stock.order
stock.security (1) ──→ (N) stock.order
stock.order (1) ──→ (N) stock.trade
```

#### Important Fields
```python
# Order Status Flow
draft → submitted → open → partial → filled
              ↓         ↓
           rejected  cancelled/expired
```

### Security Model

#### Access Control
```xml
Groups:
- Stock Market / Administrator (full access)
- Stock Market / Investor (own orders/positions)
- Stock Market / Broker (client orders, commissions)
- Stock Market / Banker (deposits, loans)
```

#### Record Rules
- Users can only see their own orders/positions
- Brokers can see their clients' data
- Bankers can see their customers' banking data
- Admins have full access

### Automated Jobs (Cron)

```xml
1. Check Session Times (every 5 minutes)
   - Auto-open sessions
   - Auto-close sessions

2. Check Matured Deposits (daily)
   - Process maturities
   - Credit interest

3. Check Overdue Loans (daily)
   - Apply penalties
   - Mark defaults

4. Expire Orders (hourly)
   - Expire day orders at session end
```

---

## Troubleshooting

### Common Issues

#### 1. Module Installation Fails
**Symptoms:** Error during installation
**Solutions:**
```bash
# Check Python dependencies
pip3 install -r requirements.txt

# Clear cache
rm -rf ~/.local/share/Odoo/filestore/*

# Reinstall
./odoo-bin -u stock -d database --stop-after-init
```

#### 2. Orders Not Matching
**Symptoms:** Orders remain in open status
**Causes & Solutions:**
- **Session not open:** Open the trading session
- **Price mismatch:** Check bid-ask spread
- **Insufficient liquidity:** No matching orders available
```bash
# Force matching (Admin only)
Stock Market → Administration → Run Matching Engine
```

#### 3. Portal Access Issues
**Symptoms:** Users cannot access portal
**Solutions:**
```python
# Check user configuration:
1. User Type field is set (investor/broker/banker)
2. Security groups assigned
3. Portal access enabled
4. Cash balance > 0 for investors
```

#### 4. Margin Call Not Executing
**Symptoms:** Loan marked for margin call but no action
**Solutions:**
```python
# Check configuration:
1. auto_execute_margin_calls = True
2. Collateral security exists
3. Current session is open
4. Sufficient buyer liquidity
```

#### 5. Performance Issues
**Symptoms:** Slow order processing
**Solutions:**
```sql
-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_order_user_session 
  ON stock_order(user_id, session_id);
  
CREATE INDEX IF NOT EXISTS idx_trade_security_date 
  ON stock_trade(security_id, trade_date);

-- Vacuum database
VACUUM ANALYZE;
```

### Error Messages Guide

```python
"Insufficient funds" 
→ User cash balance < order value
→ Solution: Deposit more funds or reduce order size

"Insufficient shares"
→ User doesn't have enough shares to sell
→ Solution: Check position quantity

"Daily trading limit exceeded"
→ User reached daily limit
→ Solution: Wait until next day or contact admin

"Session closed"
→ Trading session not open
→ Solution: Wait for session to open or contact admin

"Security not active"
→ Security trading suspended
→ Solution: Choose different security

"Margin call executed"
→ Collateral liquidated due to loan
→ Action: Review loan status, add collateral
```

### Debug Mode

```bash
# Enable debug mode
./odoo-bin -d database --log-level=debug

# Check specific module logs
grep "stock" /var/log/odoo/odoo.log

# Monitor real-time
tail -f /var/log/odoo/odoo.log | grep -i error
```

---

## API Reference

### REST API Endpoints

#### Market Data API
```javascript
// Get real-time quotes
POST /api/market/quotes
Content-Type: application/json

{
  "symbols": ["AAPL", "GOOGL", "MSFT"]
}

Response:
{
  "success": true,
  "quotes": [
    {
      "symbol": "AAPL",
      "current_price": 175.50,
      "change_percentage": 2.5,
      "last_update": "10:30:00"
    }
  ]
}
```

#### Portfolio API
```javascript
// Get portfolio summary
POST /api/portfolio/summary
Content-Type: application/json

{}

Response:
{
  "success": true,
  "cash_balance": 50000.00,
  "portfolio_value": 75000.00,
  "total_assets": 125000.00,
  "profit_loss": 25000.00,
  "profit_loss_percentage": 25.0,
  "positions_count": 5
}
```

### JavaScript API (Portal)

```javascript
// Refresh portfolio data
window.stockPortal.refreshPortfolioSummary();

// Refresh market quotes
window.stockPortal.refreshMarketQuotes();

// Submit order with validation
window.stockPortal.submitOrder(formData);

// Show notification
window.stockPortal.showNotification('Title', 'Message', 'success');
```

### Python API (Backend)

```python
# Get configuration
config = request.env['stock.config'].get_config()

# Submit order
order = request.env['stock.order'].create({
    'user_id': user.id,
    'security_id': security.id,
    'side': 'buy',
    'quantity': 100,
    'price': 175.50,
    'order_type': 'limit'
})
order.action_submit()

# Run matching engine
engine = request.env['stock.matching.engine']
engine.match_all_securities(session)

# Execute margin call
loan.execute_margin_call()
```

---

## Performance Guidelines

### Best Practices

1. **Order Processing**
   - Use limit orders for better control
   - Avoid very large orders (split into smaller orders)
   - Consider time-in-force options

2. **System Configuration**
   - Adjust matching frequency based on load
   - Set appropriate position limits
   - Enable circuit breakers

3. **Database Maintenance**
   - Regular VACUUM operations
   - Archive old trades (>1 year)
   - Monitor table sizes

4. **Monitoring**
   - Track order queue depth
   - Monitor matching engine performance
   - Alert on failed margin calls

### Capacity Planning

```
Recommended Limits:
- Users: 1,000 concurrent
- Orders/second: 100
- Securities: 500
- Active sessions: 1

Hardware Requirements:
- Small (< 100 users): 2 CPU, 4GB RAM
- Medium (100-500 users): 4 CPU, 8GB RAM
- Large (500-1000 users): 8 CPU, 16GB RAM
```

---

## Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Check cron job execution
- Monitor failed orders
- Review error logs

**Weekly:**
- Archive completed sessions
- Backup database
- Review system performance

**Monthly:**
- Update security prices
- Review user accounts
- Audit trail review

### Getting Help

**Documentation:** See this file and README.md  
**Issues:** Create issue in repository  
**Email:** Contact system administrator

---

## Changelog

### Version 1.0 (Current)
- ✅ Complete trading system implementation
- ✅ Banking integration (deposits, loans)
- ✅ Multi-role support
- ✅ Real-time portal with API
- ✅ Comprehensive reporting
- ✅ Odoo 18 compatibility
- ✅ Demo data included
- ✅ Enhanced error messages
- ✅ Extended configuration options

### Planned Features
- WebSocket for true real-time updates
- Mobile app support
- Advanced charting
- Multi-currency support
- External market data feeds

---

## License

This module is licensed under LGPL-3. See `__manifest__.py` for details.

## Credits

Converted from C# trading system to Odoo 18 by Stock Market Simulator Team.

**Contributors:**
- Core development team
- Testing team
- Documentation team

---

*Last Updated: September 30, 2025*