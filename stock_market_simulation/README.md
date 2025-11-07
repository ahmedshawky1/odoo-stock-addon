# Stock Market Trading Simulator

A comprehensive Odoo 18 module that provides a complete stock market trading simulation platform with advanced features for order management, settlement, banking, and reporting.

## 🎯 Overview

This module converts a sophisticated C# trading system into a fully functional Odoo addon, providing:

- **Complete Trading System** with order matching engine
- **Banking Integration** for deposits and loans
- **Multi-role Support** for investors, brokers, bankers, and administrators
- **Real-time Portfolio Tracking** with P&L calculations
- **Comprehensive Reporting Suite**
- **Risk Management** with margin calls and circuit breakers

## ✨ Key Features

### Trading System
- **Order Types**: Market, Limit, Stop Loss, Stop Limit
- **Time in Force**: Day, Good Till Cancelled (GTC), Immediate or Cancel (IOC), Fill or Kill (FOK)
- **Advanced Matching Engine** with price-time priority
- **Real-time Settlement** (T+2 configurable)
- **Position Tracking** with automatic P&L calculations

### Banking Features
- **Deposit Management**: Savings, Fixed Term, Recurring deposits
- **Loan Management**: Personal, Secured, Margin loans
- **Automatic Interest Calculations**
- **Margin Call Execution** with collateral liquidation
- **Default Handling** with penalties

### User Roles & Security
- **Investors**: Place orders, manage portfolio, banking operations
- **Brokers**: View client orders, track commissions
- **Bankers**: Manage deposits and loans
- **Administrators**: Full system control and configuration

### Portal Interface
- **Investor Dashboard** with portfolio overview
- **Order Placement** and tracking
- **Market Data** with top gainers/losers
- **Banking Operations** interface
- **Real-time Updates** and notifications

## 🚀 Quick Start

### Prerequisites
- Odoo 18.0+
- PostgreSQL database
- Python 3.8+
- Minimum 4GB RAM

### Installation

1. **Clone the module**:
   ```bash
   git clone <repository-url>
   cp -r stock /path/to/odoo/addons/
   ```

2. **Install the module**:
   ```bash
   # Update module list
   ./odoo-bin -u stock -d your_database --stop-after-init
   
   # Or install via Odoo interface
   # Apps → Search "Stock Market Trading Simulator" → Install
   ```

3. **Initial Setup**:
   - Navigate to **Stock Market → Configuration**
   - Create securities (AAPL, GOOGL, etc.)
   - Set up user roles and assign brokers
   - Create and open a trading session

### Demo Data
The module includes comprehensive demo data:
- Sample users for each role
- Popular securities (AAPL, GOOGL, MSFT, TSLA)
- Active trading session
- Sample orders and deposits

## 📊 Module Structure

```
stock/
├── __manifest__.py              # Module configuration
├── controllers/
│   └── portal.py               # Portal controllers for web interface
├── data/
│   ├── stock_data.xml          # Initial data and cron jobs
│   └── ir_sequence_data.xml    # Sequence configurations
├── demo/
│   └── demo.xml                # Demo data for testing
├── models/
│   ├── stock_session.py        # Trading session management
│   ├── stock_security.py       # Securities (stocks, bonds, etc.)
│   ├── stock_order.py          # Order management
│   ├── stock_trade.py          # Trade records
│   ├── stock_matching_engine.py # Order matching logic
│   ├── stock_position.py       # Position tracking
│   ├── stock_deposit.py        # Banking deposits
│   ├── stock_loan.py           # Banking loans
│   ├── stock_config.py         # System configuration
│   └── res_users.py            # User extensions
├── report/                     # Reporting suite
├── security/                   # Access control
├── views/                      # UI definitions
└── docs/                       # Documentation
```

## 🔧 Configuration

### System Parameters
Navigate to **Stock Market → Configuration → Configuration** to set:

- **Margin Call Threshold**: 70% (when to trigger margin calls)
- **Settlement Days**: T+2 (trade settlement period)
- **Commission Rates**: Broker commission percentages
- **Trading Limits**: Daily and position limits
- **Risk Parameters**: Circuit breakers and halt thresholds

### User Setup
1. **Create Users**: Settings → Users & Companies → Users
2. **Set User Types**: investor/broker/banker/admin
3. **Assign Security Groups**: Automatic based on user type
4. **Assign Brokers**: Link investors to brokers

### Securities Setup
1. **Create Securities**: Stock Market → Market Data → Securities
2. **Set Parameters**: Symbol, name, type, pricing rules
3. **Configure Trading**: Tick size, lot size, active status

## 📈 Usage Examples

### For Investors
```
1. Login to portal: /my
2. View dashboard with portfolio summary
3. Place orders: /my/order/new
4. Track positions: /my/portfolio
5. Manage banking: /my/deposits, /my/loans
```

### For Brokers
```
1. View client orders and commissions
2. Track trading activity
3. Generate commission reports
```

### For Administrators
```
1. Manage trading sessions
2. Configure system parameters
3. Monitor system health
4. Generate comprehensive reports
```

## 🛡️ Security Features

- **Role-Based Access Control (RBAC)** with 4 distinct user types
- **Data Isolation**: Users can only access their own data
- **Secure Controllers** with proper authentication
- **Input Validation** at model and controller levels
- **Audit Trail** for all financial transactions

## 📊 Reports Available

1. **Investor Portfolio Report**: Complete portfolio overview with P&L
2. **Broker Commission Report**: Detailed commission tracking
3. **Banker Portfolio Report**: Loan and deposit summaries
4. **Session Summary Report**: Trading session analytics
5. **Trade Blotter Report**: Detailed trade listings

## 🔄 Automated Processes

The module includes several cron jobs for automation:

- **Session Management**: Auto open/close sessions
- **Deposit Maturity**: Check and process matured deposits
- **Loan Monitoring**: Check overdue loans and apply penalties
- **Order Expiry**: Expire day orders at session end

## 🐛 Troubleshooting

### Common Issues

1. **Module Installation Fails**:
   ```bash
   # Check dependencies
   pip install -r requirements.txt
   
   # Clear cache and retry
   ./odoo-bin --addons-path=/path/to/addons -d database -u stock
   ```

2. **Portal Access Issues**:
   - Ensure users have portal access enabled
   - Check security group assignments
   - Verify user_type field is set correctly

3. **Order Matching Not Working**:
   - Verify trading session is open
   - Check order status and validation
   - Review matching engine logs

### Performance Optimization

For large datasets:
```sql
-- Add additional indexes if needed
CREATE INDEX idx_order_user_session ON stock_order(user_id, session_id);
CREATE INDEX idx_trade_security_date ON stock_trade(security_id, trade_date);
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This module is licensed under LGPL-3. See the `__manifest__.py` file for details.

## 📞 Support

For issues, questions, or contributions:
- Create an issue in the repository
- Contact the development team
- Check the documentation in the `/docs` folder

## 🎉 Credits

This module was developed by converting a comprehensive C# trading system to Odoo, maintaining all original functionality while adding Odoo-specific features and improvements.