# Demo Data Summary

## Overview
Enhanced demo data has been added to allow immediate session startup and testing without manual data entry.

## Demo Users

### Investors (4)
1. **John Investor** (investor1@demo.com)
   - Cash: $100,000
   - Broker: Mike Broker
   - Holdings: 50 AAPL, 20 MSFT

2. **Sarah Trader** (investor2@demo.com)
   - Cash: $250,000
   - Broker: Mike Broker
   - Holdings: 100 GOOGL, 30 TSLA

3. **David Chen** (investor3@demo.com)
   - Cash: $150,000
   - Broker: Lisa Martinez
   - Holdings: 40 AMZN, 10 NVDA

4. **Emma Wilson** (investor4@demo.com)
   - Cash: $200,000
   - Broker: Lisa Martinez
   - Holdings: 75 AAPL, 25 MSFT

### Brokers (2)
1. **Mike Broker** (broker1@demo.com)
   - Cash: $50,000
   - Clients: John Investor, Sarah Trader

2. **Lisa Martinez** (broker2@demo.com)
   - Cash: $40,000
   - Clients: David Chen, Emma Wilson

### Banker (1)
**Alice Banker** (banker1@demo.com)
- Cash: $25,000

## Securities (7 stocks + 1 bond)

| Symbol | Name | Type | Price |
|--------|------|------|-------|
| AAPL | Apple Inc. | Stock | $175.50 |
| GOOGL | Alphabet Inc. | Stock | $145.25 |
| MSFT | Microsoft Corporation | Stock | $415.75 |
| TSLA | Tesla Inc. | Stock | $250.00 |
| AMZN | Amazon.com Inc. | Stock | $178.35 |
| NVDA | NVIDIA Corporation | Stock | $875.28 |
| BOND001 | US Treasury Bond 10Y | Bond | $98.50 |

## Active Trading Session

**Demo Trading Session 2025**
- Status: **OPEN** (started 2 hours ago)
- End Date: 6 hours from now
- Price Change Threshold: 15%
- Broker Commission: 0.5%
- Circuit Breakers: ±10%

## Sample Orders
- 4 open limit orders across different securities
- Mix of buy and sell orders at various price levels

## Sample Trades
- 2 completed trades with commission calculations
- Trade history for reference

## Deposits & Loans

### Deposits (2)
1. John Investor: $50,000 savings deposit @ 3.5% (1 year)
2. Sarah Trader: $75,000 fixed deposit @ 4.5% (6 months)

### Loans (1)
1. John Investor: $25,000 margin loan @ 6.5% (active)

## System Configuration
- Demo configuration with all parameters set
- Margin call threshold: 70%
- Settlement days: 2
- Max leverage: 3.0x

## How to Use

### Login Credentials
All demo users have the same password as configured in your system.

### Quick Start
1. **Restart container** (already done):
   ```bash
   sudo docker restart odoo_stock
   ```

2. **Login as any user**:
   - Investor: investor1@demo.com (or 2, 3, 4)
   - Broker: broker1@demo.com or broker2@demo.com
   - Banker: banker1@demo.com

3. **Access Portal**:
   - Go to `/my/stock` to see the trading interface
   - Session is already **OPEN** and ready for trading
   - All users have cash and positions to trade

### Trading Features Available
- ✅ Place orders (limit/market)
- ✅ View positions and holdings
- ✅ Check order book
- ✅ View trade history
- ✅ Manage deposits/loans (banker/investor)
- ✅ Monitor portfolio performance

## Session Status
The demo session is configured to:
- **Auto-start**: Started 2 hours ago
- **Auto-close**: Will close in 6 hours
- **Current state**: OPEN and ready for trading

You can immediately start trading without any setup!
