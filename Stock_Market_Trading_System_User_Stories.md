# Stock Market Trading System - Detailed User Stories

## Table of Contents
- [System Overview](#system-overview)
- [User Roles & Hierarchy](#user-roles--hierarchy)
- [Core Business Areas](#core-business-areas)
- [Detailed User Stories](#detailed-user-stories)
  - [Authentication & User Management](#-authentication--user-management)
  - [Session Management](#-session-management)
  - [Stock Trading System](#-stock-trading-system)
  - [Bonds Trading](#-bonds-trading)
  - [Banking Operations](#-banking-operations)
  - [Mutual Funds](#-mutual-funds)
  - [News & Market Events](#-news--market-events)
  - [Rankings & Performance](#-rankings--performance)
  - [Reporting & Analytics](#-reporting--analytics)
  - [System Administration](#-system-administration)
  - [Market Validation & Controls](#-market-validation--controls)
- [Technical Architecture](#technical-architecture)
- [Implementation Roadmap](#implementation-roadmap)
- [Business Rules](#business-rules)

---

## System Overview

The **Stock Market Trading System** is a comprehensive financial simulation platform designed to replicate real-world trading environments. The system supports multiple asset classes, user roles, and complex financial operations including stocks, bonds, mutual funds, banking services, and portfolio management.

### Key Features
- **Multi-Asset Trading**: Stocks, Bonds, IPOs, Mutual Funds
- **Banking Integration**: Deposits, Loans, Certificates of Deposit
- **Real-time Matching**: Automatic bid/ask order matching engine
- **Portfolio Management**: Comprehensive tracking and analytics
- **Session-based Trading**: Controlled market hours and operations
- **Role-based Access**: Five-tier user hierarchy with specific permissions
- **Comprehensive Reporting**: Performance analytics and compliance reports

---

## User Roles & Hierarchy

### Level 1: Super Admin
- **Full System Access**: Complete control over all system functions
- **User Management**: Create, modify, block/unblock all user types
- **Market Control**: Manage stocks, bonds, pricing, sessions
- **System Configuration**: Set parameters, rules, penalties/bonuses
- **Data Management**: Database backup/restore, system reset

### Level 2: Admin
- **Administrative Functions**: Limited administrative capabilities
- **User Support**: Assist users with account issues
- **Report Generation**: Access to system-wide reports
- **Content Management**: Manage news, announcements

### Level 3.1: Banker
- **Banking Operations**: Manage deposits, loans, CDs
- **Mutual Fund Management**: Create and manage MF products
- **Interest Calculations**: Set rates, calculate payments
- **Risk Management**: Monitor loan collateral, bank capital
- **Client Relationship**: Serve investors with banking products

### Level 3.2: Broker
- **Transaction Facilitation**: Create buy/sell orders for clients
- **Commission Management**: Earn fees from trading activities
- **Market Making**: Provide liquidity through trading
- **Client Advisory**: Assist investors with trading decisions
- **Order Management**: Monitor and execute client orders

### Level 3.3: Investor
- **Portfolio Management**: Buy/sell stocks, bonds, MF shares
- **Banking Services**: Use deposit accounts, apply for loans
- **Performance Tracking**: Monitor investments and returns
- **Trading Execution**: Place orders through brokers
- **Research Tools**: Access market data and news

---

## Core Business Areas

1. **Trading Engine**: Order matching, execution, settlement
2. **Asset Management**: Stocks, bonds, mutual funds lifecycle
3. **Banking Services**: Deposits, loans, interest management
4. **Portfolio Analytics**: Performance tracking, reporting
5. **Market Data**: Pricing, news, market events
6. **Risk Management**: Validation, controls, monitoring
7. **User Experience**: Dashboards, notifications, alerts
8. **Compliance**: Audit trails, regulatory reporting

---

## Detailed User Stories

### 🔐 Authentication & User Management

#### Story: Secure User Login
**As a System User**, I want to securely log into the platform so that I can access my role-specific features.

**Acceptance Criteria:**
- **AC1**: Login with username/password credentials
- **AC2**: System validates credentials against encrypted user database
- **AC3**: Display role-appropriate interface elements based on user level
  - Level 1 (SuperAdmin): All menu items visible
  - Level 2 (Admin): Administrative functions only
  - Level 3.1 (Banker): Banking and MF operations
  - Level 3.2 (Broker): Trading facilitation tools
  - Level 3.3 (Investor): Portfolio and trading views
- **AC4**: Show current user profit/balance in header
- **AC5**: Track user session with login/logout timestamps
- **AC6**: Automatic session timeout after inactivity
- **AC7**: Multi-language support (if configured)

**Business Rules:**
- Password must be encrypted in database
- Failed login attempts should be logged
- User blocking should prevent login
- Session should persist user context

---

#### Story: Comprehensive User Management
**As a Super Admin**, I want to manage all user accounts so that I can control system access and maintain platform integrity.

**Acceptance Criteria:**
- **AC1**: Create new users with required fields:
  - Name (display name)
  - Username (unique login identifier)
  - Password (encrypted storage)
  - Email (communication)
  - User Type (SuperAdmin, Admin, Banker, Broker, Investor)
  - Initial Profit/Capital amount
  - Team Members (for group accounts)
  - Responsibility/Department assignment
- **AC2**: Validate user data before creation:
  - Username uniqueness check
  - Email format validation
  - Initial capital must be numeric
  - Required fields must be filled
- **AC3**: User modification capabilities:
  - Update all user fields except username
  - Change user type (with appropriate warnings)
  - Adjust profit/capital balances
  - Modify team assignments
- **AC4**: User blocking/unblocking system:
  - Time-based blocks (specific duration in minutes)
  - Session-based blocks (until specific session ends)
  - Block reasons (predefined list)
  - Block status tracking (Active/Inactive)
  - Automatic block expiration
- **AC5**: User listing and filtering:
  - Search by name, username, type
  - Filter by status (Active, Blocked)
  - Sort by various fields
  - Export user lists
- **AC6**: User activity monitoring:
  - Last login tracking
  - Activity logs
  - Login attempt history
  - Transaction summaries

**Business Rules:**
- Duplicate usernames not allowed
- SuperAdmin users cannot be blocked by other users
- User type changes may affect existing data relationships
- Team member changes should validate team existence

---

#### Story: Password Management
**As any System User**, I want to change my password so that I can maintain account security.

**Acceptance Criteria:**
- **AC1**: Current password verification required
- **AC2**: New password strength validation
- **AC3**: Password confirmation matching
- **AC4**: Successful change confirmation
- **AC5**: Password history to prevent reuse (optional)
- **AC6**: Encrypted storage of new password
- **AC7**: Force logout after password change

---

#### Story: User Blocking System
**As a Super Admin**, I want to block users for violations so that I can maintain platform discipline.

**Acceptance Criteria:**
- **AC1**: Block user with selectable reasons:
  - Violation of trading rules
  - Suspicious activity
  - Non-payment of obligations
  - System abuse
  - Administrative purposes
- **AC2**: Choose block type:
  - Time-based: Specific duration in minutes/hours/days
  - Session-based: Until specific session number
- **AC3**: Block status management:
  - Active blocks prevent login
  - Expired blocks automatically lift
  - Manual unblock capability
  - Block history maintenance
- **AC4**: Blocked user notification:
  - Clear message on login attempt
  - Remaining time/sessions display
  - Contact information for appeals
- **AC5**: Block reporting:
  - List of currently blocked users
  - Block history reports
  - Block expiration alerts

---

### 📊 Session Management

#### Story: Market Session Control
**As a Super Admin**, I want to control market sessions so that trading happens at designated times and market operations are properly managed.

**Acceptance Criteria:**
- **AC1**: Create new trading sessions:
  - Automatic session numbering
  - Default status: "NEW"
  - Session creation timestamp
  - Unique session identification
- **AC2**: Session lifecycle management:
  - Start session: Change status from "NEW" to "ACTIVE"
  - Stop session: Change status from "ACTIVE" to "STOPPED"
  - Record start/end timestamps
  - Only one session can be "ACTIVE" at a time
- **AC3**: Session validation:
  - Cannot start session if another is active
  - Cannot restart stopped sessions
  - Cannot delete sessions with existing data
- **AC4**: Session monitoring:
  - Display active session information
  - Show session duration elapsed
  - Track session participation
  - Monitor trading activity levels
- **AC5**: Automatic session processes:
  - End-of-session report generation
  - Portfolio valuation snapshots
  - Performance calculation triggers
  - Data archival processes
- **AC6**: Session history:
  - Complete session listing
  - Session statistics
  - Performance summaries
  - Activity logs

**Business Rules:**
- Sessions must be sequential
- Active session required for trading
- Session data cannot be modified after creation
- End-of-session reports are immutable

---

#### Story: Session Information Display
**As any User**, I want to see current session information so that I know market status and timing.

**Acceptance Criteria:**
- **AC1**: Header display elements:
  - Current session number (or "No Active Session")
  - Session start time and date
  - Elapsed time since session start
  - Real-time timer updates
- **AC2**: Session status indicators:
  - Green indicator for active session
  - Red indicator for closed market
  - Yellow indicator for session transitions
- **AC3**: Market hours information:
  - Expected session duration (if configured)
  - Time remaining estimate
  - Next session schedule (if available)
- **AC4**: Trading status:
  - "Markets Open" or "Markets Closed"
  - Trading permissions based on session
  - Order acceptance status

---

### 💰 Stock Trading System

#### Story: Stock Management
**As a Super Admin**, I want to manage stocks so that users can trade them and the market functions properly.

**Acceptance Criteria:**
- **AC1**: Add new stocks with comprehensive details:
  - **Basic Information:**
    - ReuterCode (unique stock identifier)
    - Company Name (full company name)
    - Sector (from predefined list: Energy, Financials, Health Care, etc.)
    - Logo/Image (company logo file)
  - **Trading Information:**
    - IPO Price (initial public offering price)
    - Current Price (market price)
    - Available Quantity (shares available for trading)
    - Hidden Price (internal pricing)
    - Session Start Price (price at session beginning)
  - **Status Management:**
    - IPO (Initial Public Offering)
    - PO (Public Offering)
    - Trade (Normal trading)
    - Hidden (Not visible to users)
    - Hold 10 min (Trading suspended for 10 minutes)
    - Hold 1 Session (Trading suspended for one session)
- **AC2**: Stock validation:
  - ReuterCode uniqueness check
  - Company name uniqueness
  - Price must be positive number
  - Quantity must be positive integer
  - Sector must be from predefined list
- **AC3**: Price management:
  - Manual price updates
  - Price change percentage controls
  - Price history tracking
  - Automatic price change logging
- **AC4**: Broker assignment:
  - Assign exclusive brokers for IPO/PO stocks
  - Multiple broker selection
  - Default: all brokers have access
  - Broker eligibility validation
- **AC5**: Stock status changes:
  - Status transition tracking
  - Status change history
  - Automatic order handling on status change
  - User notifications for status changes

**Business Rules:**
- Stock prices cannot be negative
- Quantity changes must be validated against outstanding orders
- Status changes may affect pending transactions
- Price changes should update related calculations

---

#### Story: Stock Price Updates
**As a Super Admin**, I want to update stock prices so that market values reflect current conditions.

**Acceptance Criteria:**
- **AC1**: Manual price update:
  - Select stock from list
  - Enter new price
  - Validate price within reasonable range
  - Confirm price change
- **AC2**: Price change validation:
  - New price must be positive
  - Price change percentage limits (if configured)
  - Confirmation for large price changes
- **AC3**: Automatic effects:
  - Update all displays immediately
  - Cancel conflicting pending orders
  - Recalculate portfolio values
  - Trigger price change alerts
- **AC4**: Price history:
  - Record old and new prices
  - Timestamp of change
  - User who made change
  - Reason for change (optional)
- **AC5**: Impact analysis:
  - Show affected pending orders
  - Calculate portfolio impact
  - List affected users
  - Generate price change reports

---

#### Story: Trading Order Creation
**As a Broker**, I want to create trading orders for clients so that they can buy and sell stocks according to their investment strategies.

**Acceptance Criteria:**
- **AC1**: Order type selection:
  - **BID Orders (Buy requests):**
    - Client wants to purchase stocks
    - Must specify maximum price willing to pay
    - Requires sufficient cash in client account
  - **ASK Orders (Sell requests):**
    - Client wants to sell stocks
    - Must specify minimum price willing to accept
    - Requires sufficient stock ownership
- **AC2**: Order details specification:
  - **Stock Selection:**
    - Choose from stocks with "Trade" status
    - Display current market price
    - Show available quantity
  - **Client Selection:**
    - Choose from investor/banker clients
    - Display client cash balance
    - Show client stock holdings
  - **Quantity:**
    - Positive integer only
    - Cannot exceed available stock (for ASK)
    - Validate against client holdings
  - **Price:**
    - Market Order: Use current market price
    - Limit Order: Specify exact price
    - Price validation within ±20% of market (configurable)
  - **Broker Fee:**
    - Percentage of trade value (0.1% - 0.5%)
    - Fee applies to both BID and ASK
    - Fee split between buyer and seller brokers
- **AC3**: Order validation:
  - **BID Order Validation:**
    - Client cash ≥ (Quantity × Price × (1 + Broker Fee))
    - Stock must be available for trading
    - Price within allowed range
  - **ASK Order Validation:**
    - Client stock ownership ≥ Quantity
    - Stock must be tradeable
    - Price within allowed range
- **AC4**: Order submission:
  - Generate unique order ID
  - Set status to "Pending"
  - Record all order details
  - Reserve client resources (cash/stocks)
  - Add to order book
- **AC5**: Order tracking:
  - Real-time order status updates
  - Partial fill notifications
  - Completion alerts
  - Failed order reasons

**Business Rules:**
- Orders can only be placed during active sessions
- Price limits prevent market manipulation
- Broker fees are mandatory and configurable
- Client resources must be sufficient before order acceptance

---

#### Story: Real-time Order Book
**As a Broker or Investor**, I want to view the order book so that I can understand market depth and make informed trading decisions.

**Acceptance Criteria:**
- **AC1**: Order book display:
  - **ASK Orders (Sell orders):**
    - Sorted by price (lowest first)
    - Show quantity and price
    - Total quantity at each price level
    - No broker or client identification
  - **BID Orders (Buy orders):**
    - Sorted by price (highest first)
    - Show quantity and price
    - Total quantity at each price level
    - Anonymous display for market integrity
- **AC2**: Market depth information:
  - Best bid price (highest buy price)
  - Best ask price (lowest sell price)
  - Bid-ask spread calculation
  - Total volume at each price level
- **AC3**: Real-time updates:
  - Automatic refresh every few seconds
  - Immediate updates on order changes
  - New order additions
  - Order cancellations and fills
- **AC4**: Market statistics:
  - Total pending buy volume
  - Total pending sell volume
  - Last traded price
  - Price change from session start
- **AC5**: Filtering options:
  - Show only my orders (for brokers)
  - Filter by price range
  - Filter by quantity size
  - Show/hide completed orders

---

#### Story: Automatic Trade Matching
**As the Trading System**, I want to automatically match compatible orders so that trades execute efficiently and fairly.

**Acceptance Criteria:**
- **AC1**: Order matching logic:
  - Continuously scan pending BID and ASK orders
  - Match when BID price ≥ ASK price for same stock
  - Execute at minimum price (better for buyer)
  - Process orders by timestamp (FIFO - First In, First Out)
- **AC2**: Execution validation:
  - Verify buyer has sufficient funds
  - Verify seller has sufficient stocks
  - Confirm both parties can complete transaction
  - Check for self-trading prevention
- **AC3**: Trade execution process:
  - **Calculate trade details:**
    - Execution price = MIN(BID price, ASK price)
    - Trade quantity = MIN(BID quantity, ASK quantity)
    - Buyer total cost = Price × Quantity × (1 + Buyer Broker Fee)
    - Seller proceeds = Price × Quantity × (1 - Seller Broker Fee)
  - **Update balances:**
    - Deduct cash from buyer
    - Add cash to seller (minus broker fee)
    - Transfer stocks from seller to buyer
    - Pay broker fees to respective brokers
  - **Update orders:**
    - Reduce remaining quantities
    - Mark completed orders as "Done"
    - Keep partially filled orders as "Pending"
- **AC4**: Transaction recording:
  - Create detailed transaction record
  - Link to original BID and ASK orders
  - Record execution price and quantity
  - Timestamp of execution
  - Store in transaction history
- **AC5**: Error handling:
  - Handle insufficient funds gracefully
  - Manage stock shortage situations
  - Log failed execution attempts
  - Maintain order integrity
  - Notify relevant parties of failures

**Business Rules:**
- Trades execute at best price for buyer
- Partial fills are allowed and tracked
- Same team cannot trade with itself
- All transactions must be auditable
- Broker fees are always collected

---

#### Story: Portfolio Management
**As an Investor**, I want to view and manage my stock portfolio so that I can track my investments and make informed decisions.

**Acceptance Criteria:**
- **AC1**: Portfolio overview:
  - **Current Holdings:**
    - Stock name and ticker symbol
    - Total quantity owned
    - Available quantity (not in pending orders)
    - Blocked quantity (in pending sell orders)
    - Current market price per share
    - Total current value
  - **Performance Metrics:**
    - VWAP (Volume Weighted Average Price) - my average purchase price
    - Unrealized gain/loss per stock
    - Percentage gain/loss per stock
    - Total portfolio value
    - Overall portfolio performance
- **AC2**: Historical information:
  - IPO price vs. current price
  - Price change since session start
  - My trading history for each stock
  - Dividend payments received (if applicable)
- **AC3**: Portfolio analytics:
  - Sector diversification breakdown
  - Largest holdings by value
  - Best/worst performing stocks
  - Total invested amount vs. current value
- **AC4**: Action capabilities:
  - Quick links to place sell orders
  - View pending orders related to each stock
  - Access detailed stock information
  - Generate portfolio reports
- **AC5**: Real-time updates:
  - Live price updates
  - Automatic value recalculation
  - Order status changes
  - Trade execution notifications

**Business Rules:**
- Available quantity = Total quantity - Pending sell orders
- VWAP calculations include all purchase transactions
- Portfolio value uses current market prices
- Performance calculations exclude unrealized positions

---

### 🏦 Bonds Trading

#### Story: Bond Management
**As a Super Admin**, I want to manage bonds so that users can invest in fixed-income securities with various characteristics.

**Acceptance Criteria:**
- **AC1**: Bond creation with comprehensive details:
  - **Basic Information:**
    - ReuterCode (unique bond identifier)
    - Company/Issuer Name
    - Sector classification
    - Bond status (IPO, Trade, Hidden, etc.)
  - **Financial Terms:**
    - IPO Price (initial offering price)
    - Face Value/Par Value
    - Current Market Price
    - Available Quantity
  - **Time Parameters:**
    - Start Session (when bond becomes available)
    - End Session (maturity session)
    - First Payment Session
  - **Bond Characteristics:**
    - Bond Type: Conventional Bond, Amortizing Bond
    - Rate Type: Fixed, Variable, Zero Coupon, Step-up, Deferred, Advanced
    - Return Price (maturity value)
    - Percentage per Session (coupon rate)
    - Compensation Rate
    - Step Percentage (for step-up bonds)
- **AC2**: Bond validation:
  - Unique ReuterCode and Company Name
  - Start Session ≤ End Session
  - Positive prices and quantities
  - Valid rate type selection
  - Reasonable coupon rates
- **AC3**: Time-based pricing:
  - Bond value calculation based on time to maturity
  - Different pricing for different bond types
  - Automatic price adjustments over time
  - Yield-to-maturity calculations
- **AC4**: Bond lifecycle management:
  - Activation at Start Session
  - Coupon payment calculations
  - Maturity processing at End Session
  - Principal repayment handling

**Business Rules:**
- Bonds cannot trade before Start Session or after End Session
- Pricing depends on time remaining to maturity
- Coupon payments follow specified schedule
- Zero coupon bonds trade at discount to face value

---

#### Story: Bond Trading Orders
**As a Broker**, I want to create bond trading orders so that clients can invest in fixed-income securities.

**Acceptance Criteria:**
- **AC1**: Bond order types:
  - **Bond BID Orders:**
    - Client wants to purchase bonds
    - Specify desired yield or price
    - Consider time to maturity in pricing
  - **Bond ASK Orders:**
    - Client wants to sell owned bonds
    - Consider accrued interest
    - Calculate current market value
- **AC2**: Bond-specific validations:
  - Check bond availability window (Start/End Session)
  - Validate client eligibility for bond type
  - Calculate time-adjusted pricing
  - Verify bond quantity availability
- **AC3**: Pricing calculations:
  - Time-based bond valuation
  - Accrued interest calculations
  - Yield-to-maturity considerations
  - Clean price vs. dirty price handling
- **AC4**: Settlement considerations:
  - Bond settlement date calculations
  - Interest payment schedules
  - Maturity date tracking
  - Coupon payment rights

---

#### Story: Bond Portfolio Tracking
**As an Investor**, I want to track my bond investments so that I can monitor my fixed-income portfolio performance.

**Acceptance Criteria:**
- **AC1**: Bond holdings display:
  - Bond name and details
  - Quantity owned
  - Purchase price vs. current value
  - Accrued interest
  - Time to maturity
- **AC2**: Income tracking:
  - Coupon payments received
  - Payment schedule for owned bonds
  - Yield calculations
  - Total interest income
- **AC3**: Performance analysis:
  - Current value vs. purchase price
  - Yield-to-maturity on holdings
  - Duration and modified duration
  - Interest rate sensitivity
- **AC4**: Maturity management:
  - Bonds approaching maturity
  - Expected principal repayments
  - Reinvestment opportunities
  - Portfolio maturity ladder

---

### 🏛️ Banking Operations

#### Story: Deposit Account Management
**As a Banker**, I want to offer deposit accounts so that investors can earn interest on their idle cash.

**Acceptance Criteria:**
- **AC1**: Deposit account creation:
  - Create accounts for investor clients
  - Set account terms and conditions
  - Define minimum deposit requirements
  - Establish interest rate and payment frequency
- **AC2**: Deposit account configuration:
  - **Account Parameters:**
    - Minimum deposit amount (default: 500 EGP)
    - Interest rate (annual or per session)
    - Payment frequency (per session or at end)
    - Account fees (creation, maintenance)
    - Withdrawal restrictions
  - **Risk Management:**
    - Bank capital requirements
    - Deposit safety margin (default: 50%)
    - Maximum deposit limits per client
    - Reserve requirements
- **AC3**: Deposit operations:
  - **Accept Deposits:**
    - Verify client has sufficient cash
    - Transfer funds from client to bank
    - Update account balance
    - Generate deposit confirmation
  - **Process Withdrawals:**
    - Validate withdrawal amount
    - Check account balance
    - Verify bank liquidity
    - Transfer funds to client
  - **Interest Calculations:**
    - Calculate periodic interest
    - Add interest to account balance
    - Track interest payments
    - Generate interest statements
- **AC4**: Account monitoring:
  - Track all deposit accounts
  - Monitor bank's total deposit liability
  - Calculate bank's capital adequacy
  - Generate deposit portfolio reports
- **AC5**: Account status management:
  - Active accounts earn interest
  - Closed accounts stop interest accrual
  - Suspended accounts restrict operations
  - Account closure procedures

**Business Rules:**
- Bank must maintain sufficient capital to cover deposits
- Interest rates must be competitive with market
- Safety margins protect against bank insolvency
- All transactions must be properly documented

---

#### Story: Loan Management System
**As a Banker**, I want to provide loans so that investors can leverage their investments and access additional capital.

**Acceptance Criteria:**
- **AC1**: Loan application processing:
  - **Application Requirements:**
    - Loan amount requested
    - Purpose of loan
    - Proposed collateral (stocks/bonds)
    - Desired loan term
    - Client financial information
  - **Eligibility Assessment:**
    - Client creditworthiness review
    - Collateral valuation
    - Loan-to-value ratio calculation
    - Bank capital availability check
- **AC2**: Collateral management:
  - **Accepted Collateral Types:**
    - Listed stocks at market value
    - Bonds at current market value
    - Mutual fund shares
    - Cash deposits (if applicable)
  - **Collateral Requirements:**
    - Minimum collateral value > loan amount
    - Safety margin (default: 50% buffer)
    - Marketable securities only
    - Collateral value monitoring
- **AC3**: Loan terms configuration:
  - Interest rate setting (risk-based pricing)
  - Loan duration (sessions or time-based)
  - Payment schedule (interest only, principal + interest)
  - Default terms and conditions
  - Early repayment options
- **AC4**: Loan lifecycle management:
  - **Loan Origination:**
    - Approve loan application
    - Execute loan agreement
    - Disburse loan proceeds
    - Register collateral lien
  - **Ongoing Monitoring:**
    - Track collateral values daily
    - Calculate margin calls if needed
    - Monitor payment schedule
    - Interest accrual and capitalization
  - **Collection and Default:**
    - Payment reminders
    - Default notice procedures
    - Collateral liquidation rights
    - Loss recovery processes
- **AC5**: Risk management:
  - Portfolio concentration limits
  - Maximum loan-to-value ratios
  - Regular collateral revaluation
  - Margin call procedures
  - Stress testing scenarios

**Business Rules:**
- Collateral value must exceed loan amount by safety margin
- Interest rates reflect risk profile
- Margin calls triggered when collateral falls below threshold
- Bank reserves right to liquidate collateral for defaults

---

#### Story: Certificate of Deposit Products
**As a Banker**, I want to offer CDs so that clients have fixed-term investment options with guaranteed returns.

**Acceptance Criteria:**
- **AC1**: CD product configuration:
  - **Term Options:**
    - Short-term (1-5 sessions)
    - Medium-term (6-15 sessions)
    - Long-term (16+ sessions)
  - **Rate Structure:**
    - Fixed interest rates by term
    - Higher rates for longer terms
    - Promotional rate offers
    - Minimum deposit requirements
- **AC2**: CD creation process:
  - Client selects CD product
  - Confirms investment amount
  - Locks in interest rate
  - Sets maturity date
  - Transfers funds from client account
- **AC3**: CD management:
  - Interest calculation and accrual
  - Maturity date tracking
  - Automatic renewal options
  - Early withdrawal penalties
  - CD portfolio monitoring
- **AC4**: Maturity processing:
  - Automatic principal + interest payout
  - Renewal notifications
  - Reinvestment options
  - Tax reporting (if applicable)

---

#### Story: Banking Portfolio Dashboard
**As an Investor**, I want to manage my banking relationships so that I can optimize my cash management and access credit when needed.

**Acceptance Criteria:**
- **AC1**: Banking relationship overview:
  - List of all deposit accounts by bank
  - Current balances and interest rates
  - Outstanding loans and credit lines
  - Available credit capacity
  - Overall banking portfolio value
- **AC2**: Account management:
  - Open new deposit accounts
  - Request loans with collateral
  - Transfer funds between accounts
  - View transaction histories
  - Generate statements
- **AC3**: Performance tracking:
  - Interest income from deposits
  - Interest expense from loans
  - Net interest income/expense
  - Return on banking relationships
  - Cash flow analysis
- **AC4**: Planning tools:
  - Cash flow projections
  - Optimal deposit allocation
  - Credit utilization planning
  - Interest rate comparisons
  - Banking fee analysis

---

### 📈 Mutual Funds

#### Story: Mutual Fund Product Management
**As a Super Admin**, I want to manage mutual funds so that the system offers diversified investment products to users.

**Acceptance Criteria:**
- **AC1**: MF product creation:
  - **Fund Details:**
    - Fund name and identifier
    - Investment objective
    - Fund manager assignment
    - Minimum investment amount
    - Management fee structure
  - **Operational Parameters:**
    - Start session (fund launch)
    - End session (fund closure)
    - NAV calculation frequency
    - Subscription/redemption rules
    - Performance benchmark
- **AC2**: Fund structure setup:
  - Initial fund capital allocation
  - Seed money requirements
  - Share class definitions
  - Pricing methodology
  - Distribution policies
- **AC3**: Fund lifecycle management:
  - Fund activation procedures
  - NAV calculation triggers
  - Performance monitoring
  - Fund closure processes
  - Liquidation procedures

---

#### Story: Mutual Fund Operations
**As a Banker**, I want to manage mutual funds so that I can offer diversified investment products to clients.

**Acceptance Criteria:**
- **AC1**: Fund management responsibilities:
  - Receive initial MF allocation from system
  - Manage fund's investment portfolio
  - Execute fund's investment strategy
  - Monitor fund performance vs. benchmark
- **AC2**: NAV calculation and pricing:
  - Calculate Net Asset Value daily/per session
  - Price new subscriptions at current NAV
  - Process redemptions at current NAV
  - Handle fund distributions
  - Maintain pricing accuracy
- **AC3**: Client services:
  - Process subscription requests
  - Handle redemption requests
  - Provide fund performance reports
  - Send periodic statements
  - Answer client inquiries
- **AC4**: Investment management:
  - Make investment decisions for fund
  - Buy/sell securities for fund account
  - Manage cash flows
  - Rebalance portfolio
  - Risk management

**Business Rules:**
- NAV calculations must be accurate and timely
- All clients treated fairly in pricing
- Fund objectives must be followed
- Proper documentation for all transactions

---

#### Story: Mutual Fund Investment
**As an Investor**, I want to invest in mutual funds so that I can access professional management and diversification.

**Acceptance Criteria:**
- **AC1**: Fund research and selection:
  - View available mutual funds
  - Compare fund performance
  - Review fund objectives and strategies
  - Analyze fee structures
  - Read fund documentation
- **AC2**: Subscription process:
  - Select desired fund
  - Specify investment amount
  - Review pricing and fees
  - Confirm subscription order
  - Transfer payment
- **AC3**: Portfolio tracking:
  - View MF holdings by fund
  - Track investment value changes
  - Monitor fund performance
  - Receive periodic statements
  - Access transaction history
- **AC4**: Redemption options:
  - Request partial or full redemption
  - Choose redemption timing
  - Receive proceeds in cash account
  - Tax reporting (if applicable)

---

### 📰 News & Market Events

#### Story: Market News Management
**As a Super Admin**, I want to publish market news so that I can simulate realistic market conditions and inform users.

**Acceptance Criteria:**
- **AC1**: News creation and management:
  - **News Content:**
    - Headline/title (required)
    - Full news article content
    - News category (Market, Company, Economic, etc.)
    - Priority level (High, Medium, Low)
  - **Timing Control:**
    - Start session (when news becomes visible)
    - Start minute (specific time within session)
    - End session (when news expires)
    - End minute (specific end time)
  - **Targeting:**
    - Associated stock ticker (optional)
    - Sector relevance
    - User type targeting
    - Geographic relevance
- **AC2**: News scheduling and delivery:
  - Automated news release based on timing
  - Real-time news feed updates
  - Push notifications for important news
  - News archival after expiration
- **AC3**: News impact simulation:
  - Link news to stock price changes
  - Market reaction modeling
  - Trading volume impact
  - Sector-wide effects
- **AC4**: News analytics:
  - Track news views and engagement
  - Monitor market reaction to news
  - Measure news effectiveness
  - User feedback collection

---

#### Story: News Consumption
**As any User**, I want to access market news so that I can make informed investment decisions.

**Acceptance Criteria:**
- **AC1**: News feed access:
  - Real-time news updates
  - Chronological news display
  - News filtering by category
  - Search functionality
- **AC2**: Personalized news:
  - News relevant to my holdings
  - Sector-specific news
  - Priority news highlighting
  - News alerts and notifications
- **AC3**: News interaction:
  - Mark news as read/unread
  - Save important news
  - Share news with team members
  - Comment on news (if enabled)
- **AC4**: News integration:
  - Link news to related stocks
  - View price impact of news
  - Access historical news
  - Export news for analysis

---

### 🏆 Rankings & Performance

#### Story: Performance Rankings System
**As any User**, I want to see performance rankings so that I can compare my performance with others and track progress.

**Acceptance Criteria:**
- **AC1**: Investor rankings:
  - **Ranking Criteria:**
    - Total portfolio value
    - Percentage return from starting capital
    - Absolute profit/loss
    - Risk-adjusted returns
    - Trading volume
  - **Display Options:**
    - Current session rankings
    - Overall competition rankings
    - Historical ranking trends
    - Peer group comparisons
- **AC2**: Broker rankings:
  - **Performance Metrics:**
    - Total commission earned
    - Trading volume facilitated
    - Number of clients served
    - Market share by volume
    - Market share by value
    - Client satisfaction ratings
  - **Time Periods:**
    - Current session performance
    - Monthly/quarterly results
    - Annual performance
    - Career statistics
- **AC3**: Banker rankings:
  - **Banking Metrics:**
    - Assets under management
    - Total deposits attracted
    - Loan portfolio size
    - Net interest income
    - Customer acquisition
  - **MF Management:**
    - Mutual fund performance
    - Fund size growth
    - Investment returns
    - Risk management
- **AC4**: Team/Virtual rankings:
  - Team-based competitions
  - Virtual trading competitions
  - Challenge-specific rankings
  - Group performance metrics

**Business Rules:**
- Rankings updated in real-time
- Fair comparison using percentage returns
- Risk-adjusted metrics for sophisticated analysis
- Historical ranking preservation

---

#### Story: Performance Analytics
**As an Investor**, I want detailed performance analytics so that I can understand my investment results and improve my strategy.

**Acceptance Criteria:**
- **AC1**: Portfolio performance metrics:
  - Total return (absolute and percentage)
  - Risk-adjusted returns (Sharpe ratio, etc.)
  - Benchmark comparisons
  - Volatility measurements
  - Maximum drawdown analysis
- **AC2**: Performance attribution:
  - Returns by asset class
  - Returns by sector
  - Individual security contribution
  - Trading vs. buy-and-hold performance
  - Timing impact analysis
- **AC3**: Risk analysis:
  - Portfolio beta and correlation
  - Value at Risk (VaR) calculations
  - Concentration risk metrics
  - Liquidity risk assessment
  - Market risk exposure
- **AC4**: Trading analysis:
  - Win/loss ratios
  - Average trade size and duration
  - Trading frequency impact
  - Commission and fee analysis
  - Trading efficiency metrics

---

### 📊 Reporting & Analytics

#### Story: Comprehensive Portfolio Reports
**As an Investor**, I want detailed portfolio reports so that I can analyze my investment performance and make strategic decisions.

**Acceptance Criteria:**
- **AC1**: Portfolio statement components:
  - **Account Summary:**
    - Total account value (current market value)
    - Cash balance (available and blocked)
    - Investment holdings value
    - Deposit account balances
    - Outstanding loan balances
    - Net worth calculation
  - **Holdings Detail:**
    - Stock positions with quantities and values
    - Bond holdings with accrued interest
    - Mutual fund shares and NAV
    - Average cost basis (VWAP) for each position
    - Unrealized gains/losses
    - Current yield and income projections
- **AC2**: Performance analysis:
  - **Return Calculations:**
    - Total return (absolute amount)
    - Percentage return from starting capital
    - Session-to-date performance
    - Inception-to-date performance
    - Annualized returns (if applicable)
  - **Benchmark Comparisons:**
    - Performance vs. market indices
    - Performance vs. peer group
    - Risk-adjusted performance metrics
    - Ranking within user group
- **AC3**: Transaction history:
  - Chronological list of all transactions
  - Buy/sell details with prices and dates
  - Dividend and interest payments
  - Fees and commissions paid
  - Banking transactions
  - Transfer and deposit records
- **AC4**: Report customization:
  - Date range selection
  - Asset class filtering
  - Export formats (PDF, Excel, CSV)
  - Email delivery options
  - Automated report scheduling

---

#### Story: Banking Business Reports
**As a Banker**, I want comprehensive banking reports so that I can manage my banking business effectively.

**Acceptance Criteria:**
- **AC1**: Balance sheet reporting:
  - **Assets:**
    - Cash and cash equivalents
    - Loans outstanding by category
    - Investment securities
    - Fixed assets
    - Total assets
  - **Liabilities:**
    - Customer deposits by type
    - Borrowed funds
    - Accrued expenses
    - Total liabilities
  - **Equity:**
    - Paid-in capital
    - Retained earnings
    - Current period profit/loss
- **AC2**: Income statement:
  - **Interest Income:**
    - Interest on loans
    - Interest on investments
    - Fee income
  - **Interest Expense:**
    - Interest on deposits
    - Interest on borrowed funds
  - **Net Interest Income:**
    - Net interest margin analysis
    - Yield curve impact
- **AC3**: Risk management reports:
  - **Credit Risk:**
    - Loan portfolio analysis
    - Collateral coverage ratios
    - Past due loan report
    - Credit loss provisions
  - **Liquidity Risk:**
    - Cash flow projections
    - Deposit maturity analysis
    - Liquidity ratios
  - **Market Risk:**
    - Interest rate sensitivity
    - Investment portfolio risk
- **AC4**: Customer analytics:
  - Customer profitability analysis
  - Deposit growth trends
  - Loan demand analysis
  - Cross-selling opportunities
  - Customer retention metrics

---

#### Story: Broker Performance Reports
**As a Broker**, I want trading performance reports so that I can track my business success and optimize my services.

**Acceptance Criteria:**
- **AC1**: Trading volume analysis:
  - Total volume facilitated (shares and value)
  - Trading activity by stock/sector
  - Market share calculations
  - Volume trends over time
  - Peak trading periods
- **AC2**: Commission analysis:
  - **Revenue Breakdown:**
    - Total commission income
    - Commission by client
    - Commission by stock/asset type
    - Average commission per trade
    - Commission margin analysis
  - **Client Analysis:**
    - Most profitable clients
    - Client activity levels
    - New client acquisition
    - Client retention rates
- **AC3**: Market participation:
  - Percentage of total market volume
  - Competitive position analysis
  - Market making activities
  - Order execution quality
  - Client satisfaction metrics
- **AC4**: Business development:
  - New client onboarding
  - Revenue growth trends
  - Service expansion opportunities
  - Market penetration analysis
  - Strategic planning metrics

---

#### Story: System-wide Analytics
**As a Super Admin**, I want comprehensive system reports so that I can monitor platform performance and make strategic decisions.

**Acceptance Criteria:**
- **AC1**: Platform usage statistics:
  - **User Activity:**
    - Total registered users
    - Active users per session
    - User engagement metrics
    - Login frequency analysis
    - Feature utilization rates
  - **Trading Activity:**
    - Total trades executed
    - Trading volume and value
    - Market liquidity metrics
    - Price volatility measures
    - Order book depth analysis
- **AC2**: Financial system health:
  - **Market Metrics:**
    - Total market capitalization
    - Trading turnover ratios
    - Bid-ask spreads
    - Market efficiency indicators
  - **Banking System:**
    - Total deposits in system
    - Total loans outstanding
    - System-wide liquidity
    - Credit risk indicators
- **AC3**: Performance analytics:
  - Session-by-session comparisons
  - Growth trend analysis
  - User satisfaction surveys
  - System stability metrics
  - Error rate monitoring
- **AC4**: Compliance and audit:
  - Regulatory reporting requirements
  - Audit trail completeness
  - Risk management compliance
  - Data integrity checks
  - Security incident reports

---

### ⚙️ System Administration

#### Story: System Configuration Management
**As a Super Admin**, I want to configure system parameters so that the trading simulation operates according to desired rules and constraints.

**Acceptance Criteria:**
- **AC1**: Trading parameter configuration:
  - **Price Controls:**
    - Maximum price change percentage (default: 20%)
    - Price update frequency limits
    - Circuit breaker thresholds
    - Minimum tick sizes
  - **Order Controls:**
    - Maximum order size limits
    - Price deviation limits from market
    - Order expiration rules
    - Maximum quantity percentage per stock
  - **Broker Settings:**
    - Maximum broker fee percentage (default: 0.3%)
    - Minimum broker fee requirements
    - Broker eligibility rules
    - Commission calculation methods
- **AC2**: Banking configuration:
  - **Interest Rate Settings:**
    - Deposit interest rate ranges
    - Loan interest rate formulas
    - CD rate structures
    - Rate change approval processes
  - **Risk Parameters:**
    - Loan-to-value ratio limits
    - Deposit safety margins (default: 50%)
    - Bank capital requirements
    - Collateral haircut percentages
  - **Fee Structures:**
    - Account opening fees
    - Transaction fees
    - Maintenance fees
    - Penalty fee schedules
- **AC3**: Session management:
  - Default session duration
  - Session transition rules
  - Automatic report generation triggers
  - Session data archival policies
- **AC4**: User interface settings:
  - Background images and themes
  - News display configuration
  - Notification settings
  - Language and localization options
- **AC5**: System maintenance:
  - Database optimization schedules
  - Backup procedures
  - Log retention policies
  - Performance monitoring thresholds

**Business Rules:**
- Parameter changes take effect immediately unless scheduled
- All configuration changes are logged with user and timestamp
- Critical parameters require confirmation before changes
- Some parameters may require system restart

---

#### Story: Penalty and Bonus System
**As a Super Admin**, I want to manage penalties and bonuses so that I can enforce rules and incentivize desired behaviors.

**Acceptance Criteria:**
- **AC1**: Penalty management:
  - **Penalty Types:**
    - Rule violation penalties
    - Late payment penalties
    - Market manipulation penalties
    - System abuse penalties
    - Custom penalty reasons
  - **Penalty Application:**
    - Manual penalty assignment
    - Automatic penalty triggers
    - Penalty amount calculation
    - Penalty effective date
    - Payment collection methods
- **AC2**: Bonus system:
  - **Bonus Categories:**
    - Performance bonuses
    - Participation bonuses
    - Achievement bonuses
    - Referral bonuses
    - Competition prizes
  - **Bonus Distribution:**
    - Automatic bonus calculation
    - Manual bonus awards
    - Bonus payment methods
    - Tax implications (if applicable)
- **AC3**: Tracking and reporting:
  - Penalty and bonus history
  - User-specific P&B statements
  - System-wide P&B analytics
  - Appeal process management
  - Audit trail maintenance

---

#### Story: Database Management
**As a Super Admin**, I want to manage the database so that I can maintain system integrity and performance.

**Acceptance Criteria:**
- **AC1**: Backup and restore:
  - **Automated Backups:**
    - Daily database backups
    - Incremental backup options
    - Backup verification procedures
    - Remote backup storage
  - **Manual Backup:**
    - On-demand backup creation
    - Custom backup naming
    - Backup compression options
    - Export to external storage
  - **Restore Operations:**
    - Point-in-time recovery
    - Full system restore
    - Selective data restore
    - Pre-restore validation
- **AC2**: System reset capabilities:
  - **Complete Reset:**
    - Clear all transactional data
    - Preserve system configuration
    - Reset user accounts to initial state
    - Maintain system structure
  - **Partial Reset:**
    - Reset specific modules
    - Clear session data only
    - Reset user balances
    - Selective table cleanup
- **AC3**: Database maintenance:
  - Performance optimization
  - Index maintenance
  - Data integrity checks
  - Storage space monitoring
  - Query performance analysis

---

### 🔍 Market Validation & Controls

#### Story: Trade Validation System
**As the Trading System**, I want to validate all trading activities so that market integrity is maintained and users are protected.

**Acceptance Criteria:**
- **AC1**: Pre-trade validation:
  - **Order Price Validation:**
    - Check price within allowed deviation from market (±20%)
    - Validate against last two sessions' price range (±5%)
    - Ensure minimum tick size compliance
    - Block unreasonable price orders
  - **Quantity Validation:**
    - Verify quantity is positive integer
    - Check against maximum order size limits
    - Validate against available stock/cash
    - Prevent excessive market impact orders
  - **Account Validation:**
    - Confirm sufficient account balance
    - Verify stock ownership for sell orders
    - Check account status and restrictions
    - Validate user permissions
- **AC2**: Real-time monitoring:
  - **Trading Pattern Analysis:**
    - Monitor for wash trading
    - Detect circular trading patterns
    - Identify excessive concentration
    - Flag unusual trading volumes
  - **Market Manipulation Detection:**
    - Price manipulation attempts
    - Coordinated trading activities
    - Artificial liquidity creation
    - Cross-account trading patterns
- **AC3**: Automatic controls:
  - **Circuit Breakers:**
    - Halt trading on extreme price moves
    - Temporary trading suspensions
    - Automatic order cancellation
    - Market-wide circuit breakers
  - **Position Limits:**
    - Maximum position size per user
    - Concentration limits by stock
    - Sector exposure limits
    - Total portfolio limits
- **AC4**: Exception handling:
  - Failed trade logging
  - Error notification system
  - Manual intervention capabilities
  - Investigation workflow
  - Resolution tracking

**Business Rules:**
- All trades must pass validation before execution
- Suspicious activities trigger automatic investigations
- System administrators can override controls in emergencies
- All validation failures are logged for audit

---

#### Story: Market Control Tools
**As a Super Admin**, I want market control tools so that I can manage exceptional situations and maintain orderly markets.

**Acceptance Criteria:**
- **AC1**: Trading halt controls:
  - **Stock-Specific Halts:**
    - Halt individual stock trading
    - Set halt duration
    - Specify halt reason
    - Communicate halt to users
  - **Market-Wide Halts:**
    - Suspend all trading activity
    - Emergency market closure
    - Coordinated halt procedures
    - System-wide notifications
- **AC2**: Price intervention:
  - Manual price adjustments
  - Price correction procedures
  - Reference price setting
  - Market maker intervention
- **AC3**: Position management:
  - Force position liquidation
  - Emergency position transfers
  - Collateral enforcement
  - Margin call automation
- **AC4**: Crisis management:
  - Emergency procedures activation
  - Stakeholder communication
  - Recovery planning
  - Post-incident analysis

---

## Technical Architecture

### Database Design
- **Primary Database**: MySQL (database name: "borsa")
- **Connection Details**: 
  - Server IP: 192.168.1.73 (configurable)
  - Database: "borsa"
  - Username: "newuser1"
  - Password: "1234"
  - Character set: UTF8 with zero datetime conversion

### Detailed Database Schema

#### Core Tables with Complete Field Specifications

```sql
-- Users table - Complete schema
CREATE TABLE `users` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `UserName` VARCHAR(100) UNIQUE NOT NULL,
  `Name` VARCHAR(200) NOT NULL,
  `Password` VARCHAR(255) NOT NULL, -- Encrypted
  `Email` VARCHAR(200),
  `Type` ENUM('SuperAdmin', 'Admin', 'Banker', 'Broker', 'Investor') NOT NULL,
  `TeamMembers` TEXT,
  `Profit` DECIMAL(15,2) DEFAULT 0.00,
  `StartProfit` DECIMAL(15,2) DEFAULT 0.00,
  `Resp` VARCHAR(100), -- Responsibility/Department
  `MF_Account` VARCHAR(50), -- Reference to MF account for bankers
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_username` (`UserName`),
  INDEX `idx_type` (`Type`),
  INDEX `idx_created_by` (`Created_By`)
);

-- Levels table - User permission hierarchy
CREATE TABLE `levels` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `Type` ENUM('SuperAdmin', 'Admin', 'Banker', 'Broker', 'Investor') NOT NULL,
  `Level` INT NOT NULL, -- 1=SuperAdmin, 2=Admin, 3=Others
  `SubLevel` INT NOT NULL, -- 1=Banker, 2=Broker, 3=Investor
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_type_level` (`Type`, `Level`, `SubLevel`)
);

-- Stocks table - Complete schema
CREATE TABLE `stocks` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `ReuterCode` VARCHAR(20) UNIQUE NOT NULL,
  `CompanyName` VARCHAR(200) NOT NULL,
  `Sector` ENUM('Energy', 'Financials', 'Health Care', 'Industrials', 
                'Information Technology', 'Materials', 'Telecommunication Services', 
                'Utilities', 'Tourism', 'Chemical', 'Food and beverage', 
                'Medical Industry', 'Real Estate', 'Media', 'Construction', 
                'Fin. Services', 'banking', 'transportation') NOT NULL,
  `Logo` VARCHAR(500), -- Logo file path
  `Status` ENUM('IPO', 'PO', 'Trade', 'Hidden', 'Hold 10 min', 'Hold 1 Session') NOT NULL,
  `Price` DECIMAL(10,3) NOT NULL,
  `IPOPrice` DECIMAL(10,3) NOT NULL,
  `Hidden_Price` DECIMAL(10,3),
  `PriceToCompareWith` DECIMAL(10,3),
  `SessionStartPrice` DECIMAL(10,3),
  `Quantity` BIGINT NOT NULL,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_reuters` (`ReuterCode`),
  INDEX `idx_status` (`Status`),
  INDEX `idx_sector` (`Sector`),
  INDEX `idx_company` (`CompanyName`)
);

-- Trading orders table - Complete schema
CREATE TABLE `tranlog` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `SessionNo` INT NOT NULL,
  `Broker_ID` VARCHAR(50) NOT NULL,
  `Type` ENUM('Bid', 'Ask') NOT NULL,
  `Price` DECIMAL(10,3) NOT NULL,
  `Quantity` BIGINT NOT NULL,
  `Remain_Quantity` BIGINT NOT NULL,
  `Stock_ID` VARCHAR(50) NOT NULL,
  `Team_ID` VARCHAR(50) NOT NULL, -- Client ID
  `Status` ENUM('Pending', 'Done', 'Failed', 'Cancelled') DEFAULT 'Pending',
  `Broker_Percentage` DECIMAL(5,3) NOT NULL, -- 0.001 = 0.1%
  `Description` TEXT,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`Broker_ID`) REFERENCES `users`(`Row_ID`),
  FOREIGN KEY (`Stock_ID`) REFERENCES `stocks`(`Row_ID`),
  FOREIGN KEY (`Team_ID`) REFERENCES `users`(`Row_ID`),
  INDEX `idx_session_status` (`SessionNo`, `Status`),
  INDEX `idx_stock_type_status` (`Stock_ID`, `Type`, `Status`),
  INDEX `idx_team_broker` (`Team_ID`, `Broker_ID`),
  INDEX `idx_created_date` (`Created_Date`)
);

-- Executed trades table
CREATE TABLE `detailtrans` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `Ask_Row_ID` VARCHAR(50) NOT NULL,
  `Bid_Row_ID` VARCHAR(50) NOT NULL,
  `Quantity` BIGINT NOT NULL,
  `Price` DECIMAL(10,3) NOT NULL,
  `Active` ENUM('Y', 'N') DEFAULT 'Y',
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`Ask_Row_ID`) REFERENCES `tranlog`(`Row_ID`),
  FOREIGN KEY (`Bid_Row_ID`) REFERENCES `tranlog`(`Row_ID`),
  INDEX `idx_ask_bid` (`Ask_Row_ID`, `Bid_Row_ID`),
  INDEX `idx_execution_date` (`Created_Date`),
  INDEX `idx_active` (`Active`)
);

-- User stock holdings
CREATE TABLE `user_stocks` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `User_ID` VARCHAR(50) NOT NULL,
  `Stock_ID` VARCHAR(50) NOT NULL,
  `Quantity` BIGINT NOT NULL DEFAULT 0,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`User_ID`) REFERENCES `users`(`Row_ID`),
  FOREIGN KEY (`Stock_ID`) REFERENCES `stocks`(`Row_ID`),
  UNIQUE KEY `uk_user_stock` (`User_ID`, `Stock_ID`),
  INDEX `idx_user` (`User_ID`),
  INDEX `idx_stock` (`Stock_ID`)
);

-- Sessions table
CREATE TABLE `sessions` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `SessionNum` INT AUTO_INCREMENT UNIQUE,
  `Status` ENUM('NEW', 'ACTIVE', 'STOPPED') NOT NULL DEFAULT 'NEW',
  `StartDate` DATETIME,
  `EndDate` DATETIME,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_session_status` (`SessionNum`, `Status`),
  INDEX `idx_status` (`Status`)
);

-- Price change tracking
CREATE TABLE `stockpricechange` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `StockID` VARCHAR(50) NOT NULL,
  `Price` DECIMAL(10,3) NOT NULL,
  `OldPrice` DECIMAL(10,3) NOT NULL,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`StockID`) REFERENCES `stocks`(`Row_ID`),
  INDEX `idx_stock_date` (`StockID`, `Created_Date`)
);

-- System configuration
CREATE TABLE `others` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `Type` VARCHAR(100) NOT NULL,
  `A1` VARCHAR(500), -- Config value 1
  `A2` VARCHAR(500), -- Config key
  `A3` VARCHAR(500), -- Config value 2
  `A4` VARCHAR(500), -- Config value 3
  `A5` VARCHAR(500), -- Config value 4
  `A6` VARCHAR(500), -- Config value 5
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_type_key` (`Type`, `A2`)
);

-- User blocking system
CREATE TABLE `blocked_user` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `User_ID` VARCHAR(50) NOT NULL,
  `Type` ENUM('time', 'session') NOT NULL,
  `Blocked_From_Date` DATETIME NOT NULL,
  `Blocked_to_date` INT, -- Minutes for time-based, NULL for session-based
  `Blocked_to_session` INT, -- Session number for session-based
  `Status` ENUM('Active', 'Inactive') DEFAULT 'Active',
  `Reason` TEXT,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`User_ID`) REFERENCES `users`(`Row_ID`),
  INDEX `idx_user_status` (`User_ID`, `Status`),
  INDEX `idx_expiry_check` (`Blocked_From_Date`, `Blocked_to_date`, `Type`)
);
```

### Additional Database Tables (Extended Schema)

```sql
-- Bonds table - Complete schema
CREATE TABLE `bonds` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `ReuterCode` VARCHAR(20) UNIQUE NOT NULL,
  `CompanyName` VARCHAR(200) NOT NULL,
  `Sector` VARCHAR(100) NOT NULL,
  `Status` ENUM('IPO', 'PO', 'Trade', 'Hidden') NOT NULL,
  `IPOPrice` DECIMAL(10,3) NOT NULL,
  `Price` DECIMAL(10,3) NOT NULL,
  `Hidden_Price` DECIMAL(10,3),
  `PriceToCompareWith` DECIMAL(10,3),
  `SessionStartPrice` DECIMAL(10,3),
  `Quantity` BIGINT NOT NULL,
  `StartSession` INT NOT NULL,
  `EndSession` INT NOT NULL,
  `BondType` ENUM('conventional bond', 'amortizing bond') NOT NULL,
  `RateType` ENUM('conventional bond', 'zero coupon bond (discount)', 'accrual bond', 
                  'deferred coupon bond', 'step-up coupon bond', 'advanced coupon bond') NOT NULL,
  `ReturnPrice` DECIMAL(10,3) NOT NULL,
  `PercentageRateSession` DECIMAL(5,3) NOT NULL,
  `FirstPaySession` INT NOT NULL,
  `CompensationRate` DECIMAL(5,3) NOT NULL,
  `FinalRateSession` INT NOT NULL,
  `StepPercentage` DECIMAL(5,3) NOT NULL,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_bonds_reuters` (`ReuterCode`),
  INDEX `idx_bonds_status` (`Status`),
  INDEX `idx_bonds_sessions` (`StartSession`, `EndSession`)
);

-- Bond trading orders
CREATE TABLE `bonds_tranlog` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `SessionNo` INT NOT NULL,
  `Broker_ID` VARCHAR(50) NOT NULL,
  `Type` ENUM('Bid', 'Ask') NOT NULL,
  `Price` DECIMAL(10,3) NOT NULL,
  `Quantity` BIGINT NOT NULL,
  `Remain_Quantity` BIGINT NOT NULL,
  `Bond_ID` VARCHAR(50) NOT NULL,
  `Team_ID` VARCHAR(50) NOT NULL,
  `Status` ENUM('Pending', 'Done', 'Failed', 'Cancelled') DEFAULT 'Pending',
  `Broker_Percentage` DECIMAL(5,3) NOT NULL,
  `Description` TEXT,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`Bond_ID`) REFERENCES `bonds`(`Row_ID`),
  INDEX `idx_bonds_session_status` (`SessionNo`, `Status`),
  INDEX `idx_bonds_type_status` (`Bond_ID`, `Type`, `Status`)
);

-- User bond holdings
CREATE TABLE `user_bonds` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `User_ID` VARCHAR(50) NOT NULL,
  `Bond_ID` VARCHAR(50) NOT NULL,
  `Quantity` BIGINT NOT NULL DEFAULT 0,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`User_ID`) REFERENCES `users`(`Row_ID`),
  FOREIGN KEY (`Bond_ID`) REFERENCES `bonds`(`Row_ID`),
  UNIQUE KEY `uk_user_bond` (`User_ID`, `Bond_ID`)
);

-- Mutual Funds table
CREATE TABLE `mf` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `Name` VARCHAR(200) NOT NULL,
  `Price` DECIMAL(10,3) NOT NULL,
  `Quantity` BIGINT NOT NULL,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP
);

-- User MF holdings
CREATE TABLE `user_mf` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `User_ID` VARCHAR(50) NOT NULL,
  `Banker_ID` VARCHAR(50),
  `MF_ID` VARCHAR(50) NOT NULL,
  `Quantity` DECIMAL(15,3) NOT NULL,
  `Price` DECIMAL(10,3),
  `Percentage` DECIMAL(5,3),
  `BankCapital` DECIMAL(15,2),
  `StartSession` INT,
  `EndSession` INT,
  `BankAccount` ENUM('Y', 'N') DEFAULT 'N',
  `IsDone` ENUM('Y', 'N') DEFAULT 'N',
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`User_ID`) REFERENCES `users`(`Row_ID`),
  FOREIGN KEY (`MF_ID`) REFERENCES `mf`(`Row_ID`)
);

-- Deposit accounts
CREATE TABLE `deposit_accounts` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `UserID` VARCHAR(50) NOT NULL,
  `BankerID` VARCHAR(50) NOT NULL,
  `Profit` DECIMAL(15,2) DEFAULT 0.00,
  `Status` ENUM('Active', 'Closed', 'Suspended') DEFAULT 'Active',
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`UserID`) REFERENCES `users`(`Row_ID`),
  FOREIGN KEY (`BankerID`) REFERENCES `users`(`Row_ID`),
  INDEX `idx_deposit_user_banker` (`UserID`, `BankerID`),
  INDEX `idx_deposit_status` (`Status`)
);

-- Enhanced deposit accounts
CREATE TABLE `deposit_accounts_xm` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `UserID` VARCHAR(50) NOT NULL,
  `Value` DECIMAL(15,2) NOT NULL,
  `Status` ENUM('Active', 'Closed') DEFAULT 'Active',
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`UserID`) REFERENCES `users`(`Row_ID`)
);

-- Banker initial settings
CREATE TABLE `banker_initial` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `BankerID` VARCHAR(50) NOT NULL,
  `CreationFees` DECIMAL(10,2) DEFAULT 0.00,
  `MinDeposit` DECIMAL(10,2) DEFAULT 500.00,
  `Margin` DECIMAL(5,3) DEFAULT 0.1,
  `MarginAtEnd` DECIMAL(5,3) DEFAULT 0.1,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`BankerID`) REFERENCES `users`(`Row_ID`),
  UNIQUE KEY `uk_banker` (`BankerID`)
);

-- News table
CREATE TABLE `news` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `Headline` TEXT NOT NULL,
  `StartSession` INT NOT NULL,
  `StartMinute` INT NOT NULL,
  `EndMinute` INT,
  `EndSession` INT,
  `Status` VARCHAR(50) DEFAULT 'Active',
  `StockID` VARCHAR(50),
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`StockID`) REFERENCES `stocks`(`Row_ID`),
  INDEX `idx_news_sessions` (`StartSession`, `EndSession`),
  INDEX `idx_news_status` (`Status`)
);

-- Alerts system
CREATE TABLE `alerts` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `SessionNo` INT,
  `UserID` VARCHAR(50),
  `Type` VARCHAR(50) DEFAULT 'admin',
  `Headline` TEXT NOT NULL,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`UserID`) REFERENCES `users`(`Row_ID`),
  INDEX `idx_alerts_user` (`UserID`),
  INDEX `idx_alerts_session` (`SessionNo`)
);

-- Cash pending operations
CREATE TABLE `pending_cash` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `UserID` VARCHAR(50) NOT NULL,
  `Value` DECIMAL(15,2) NOT NULL,
  `SessionNo` INT NOT NULL,
  `Comment` TEXT,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`UserID`) REFERENCES `users`(`Row_ID`)
);

-- IPO eligibility
CREATE TABLE `ipo_elig` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `UserID` VARCHAR(50) NOT NULL,
  `StockID` VARCHAR(50) NOT NULL,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`UserID`) REFERENCES `users`(`Row_ID`),
  FOREIGN KEY (`StockID`) REFERENCES `stocks`(`Row_ID`),
  UNIQUE KEY `uk_user_stock_ipo` (`UserID`, `StockID`)
);

-- Stock status change tracking
CREATE TABLE `stock_change_status` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `StockID` VARCHAR(50) NOT NULL,
  `OldStatus` VARCHAR(50) NOT NULL,
  `NewStatus` VARCHAR(50) NOT NULL,
  `IsDone` ENUM('Y', 'N') DEFAULT 'N',
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`StockID`) REFERENCES `stocks`(`Row_ID`)
);

-- Bond status change tracking
CREATE TABLE `bond_change_status` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `BondID` VARCHAR(50) NOT NULL,
  `OldStatus` VARCHAR(50) NOT NULL,
  `NewStatus` VARCHAR(50) NOT NULL,
  `IsDone` ENUM('Y', 'N') DEFAULT 'N',
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`BondID`) REFERENCES `bonds`(`Row_ID`)
);

-- Bond price changes
CREATE TABLE `bondpricechange` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `BondID` VARCHAR(50) NOT NULL,
  `Price` DECIMAL(10,3) NOT NULL,
  `OldPrice` DECIMAL(10,3) NOT NULL,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`BondID`) REFERENCES `bonds`(`Row_ID`)
);

-- Bond executed trades
CREATE TABLE `bonds_detailtrans` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `Ask_Row_ID` VARCHAR(50) NOT NULL,
  `Bid_Row_ID` VARCHAR(50) NOT NULL,
  `Quantity` BIGINT NOT NULL,
  `Price` DECIMAL(10,3) NOT NULL,
  `Active` ENUM('Y', 'N') DEFAULT 'Y',
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`Ask_Row_ID`) REFERENCES `bonds_tranlog`(`Row_ID`),
  FOREIGN KEY (`Bid_Row_ID`) REFERENCES `bonds_tranlog`(`Row_ID`)
);

-- Reporting tables
CREATE TABLE `report_main` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `UserID` VARCHAR(50) NOT NULL,
  `UserType` ENUM('investor', 'banker', 'broker') NOT NULL,
  `SessionNo` INT NOT NULL,
  `AccountValue` DECIMAL(15,2),
  `Investments` DECIMAL(15,2),
  `Bonds_Investments` DECIMAL(15,2),
  `Liquidity` DECIMAL(15,2),
  `Deposits` DECIMAL(15,2),
  `Loans` DECIMAL(15,2),
  `PercentageChange` DECIMAL(8,3),
  `OverallChange` DECIMAL(15,2),
  `SessionProfit` DECIMAL(15,2),
  `MarketShareByVolume` DECIMAL(5,3),
  `MarketShareByValue` DECIMAL(5,3),
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`UserID`) REFERENCES `users`(`Row_ID`),
  UNIQUE KEY `uk_user_session_report` (`UserID`, `SessionNo`)
);

CREATE TABLE `report_stocks` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `par_Row_ID` VARCHAR(50) NOT NULL, -- Links to report_main
  `ReuterCode` VARCHAR(20) NOT NULL,
  `Total` BIGINT,
  `Available` BIGINT,
  `Blocked` BIGINT,
  `Price` DECIMAL(10,3),
  `VWAP` DECIMAL(10,3),
  `IPOPrice` DECIMAL(10,3),
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`par_Row_ID`) REFERENCES `report_main`(`Row_ID`)
);

CREATE TABLE `report_loans` (
  `Row_ID` VARCHAR(50) PRIMARY KEY,
  `ModfNum` INT DEFAULT 0,
  `par_Row_ID` VARCHAR(50) NOT NULL,
  `Investor` VARCHAR(200),
  `Amount` DECIMAL(15,2),
  `Interest` DECIMAL(8,3),
  `ReuterCode` VARCHAR(20),
  `Quantity` BIGINT,
  `Price` DECIMAL(10,3),
  `MaturitySession` INT,
  `Created_By` VARCHAR(50) NOT NULL,
  `Created_Date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `Modified_By` VARCHAR(50),
  `Modified_Date` DATETIME ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`par_Row_ID`) REFERENCES `report_main`(`Row_ID`)
);

-- Row ID generation table
CREATE TABLE `rid` (
  `RID` VARCHAR(10) PRIMARY KEY,
  `Value` BIGINT NOT NULL DEFAULT 1
);

-- Insert initial RID
INSERT INTO `rid` (`RID`, `Value`) VALUES ('RID', 1);
```

### API Specifications and Endpoints

#### Authentication API
```python
# Login endpoint
@http.route('/api/auth/login', type='json', auth='none', methods=['POST'], csrf=False)
def api_login(self, **kw):
    """
    Login user and establish session
    Expected payload: {
        'username': 'string',
        'password': 'string'
    }
    Returns: {
        'success': boolean,
        'data': {
            'user_id': 'string',
            'username': 'string', 
            'name': 'string',
            'type': 'string',
            'level': 'int',
            'sublevel': 'int',
            'profit': 'decimal',
            'session_token': 'string'
        } | None,
        'error': 'string' | None
    }
    """

# Check user block status
@http.route('/api/auth/check-blocked', type='json', auth='user', methods=['GET'])
def check_user_blocked(self, **kw):
    """
    Check if current user is blocked
    Returns: {
        'success': boolean,
        'data': {
            'is_blocked': boolean,
            'block_type': 'time' | 'session' | None,
            'block_reason': 'string' | None,
            'block_expires': 'datetime' | 'session_number' | None
        },
        'error': 'string' | None
    }
    """
```

#### Trading API
```python
# Get order book for stock
@http.route('/api/trading/orderbook/<string:stock_id>', type='json', auth='user', methods=['GET'])
def get_order_book(self, stock_id, **kw):
    """
    Get current order book for a stock
    Returns: {
        'success': boolean,
        'data': {
            'stock_info': {
                'id': 'string',
                'reuters_code': 'string',
                'company_name': 'string',
                'current_price': 'decimal',
                'status': 'string'
            },
            'bids': [
                {
                    'price': 'decimal',
                    'quantity': 'integer',
                    'order_count': 'integer'
                }
            ],
            'asks': [
                {
                    'price': 'decimal', 
                    'quantity': 'integer',
                    'order_count': 'integer'
                }
            ],
            'spread': 'decimal',
            'last_trade_price': 'decimal'
        } | None,
        'error': 'string' | None
    }
    """

# Place trading order
@http.route('/api/trading/place-order', type='json', auth='user', methods=['POST'])
def place_trading_order(self, **kw):
    """
    Place a new trading order
    Expected payload: {
        'stock_id': 'string',
        'client_id': 'string', -- Team/Client ID
        'type': 'Bid' | 'Ask',
        'price': 'decimal',
        'quantity': 'integer',
        'broker_percentage': 'decimal', -- 0.001 = 0.1%
        'description': 'string' (optional)
    }
    Returns: {
        'success': boolean,
        'data': {
            'order_id': 'string',
            'status': 'Pending',
            'estimated_cost': 'decimal', -- For Bid orders
            'estimated_proceeds': 'decimal' -- For Ask orders
        } | None,
        'error': 'string' | None
    }
    """

# Get user portfolio
@http.route('/api/portfolio/holdings', type='json', auth='user', methods=['GET'])
def get_portfolio_holdings(self, **kw):
    """
    Get current user's portfolio holdings
    Returns: {
        'success': boolean,
        'data': {
            'cash_balance': 'decimal',
            'total_portfolio_value': 'decimal',
            'stocks': [
                {
                    'stock_id': 'string',
                    'reuters_code': 'string',
                    'company_name': 'string',
                    'quantity_total': 'integer',
                    'quantity_available': 'integer',
                    'quantity_blocked': 'integer',
                    'current_price': 'decimal',
                    'current_value': 'decimal',
                    'average_cost': 'decimal', -- VWAP
                    'unrealized_pnl': 'decimal',
                    'unrealized_pnl_pct': 'decimal'
                }
            ],
            'bonds': [...], -- Similar structure for bonds
            'mutual_funds': [...] -- Similar structure for MFs
        } | None,
        'error': 'string' | None
    }
    """
```

#### Session Management API
```python
# Get current session info
@http.route('/api/session/current', type='json', auth='user', methods=['GET'])
def get_current_session(self, **kw):
    """
    Get current active session information
    Returns: {
        'success': boolean,
        'data': {
            'session_number': 'integer' | None,
            'status': 'NEW' | 'ACTIVE' | 'STOPPED',
            'start_date': 'datetime' | None,
            'elapsed_time': 'string', -- Human readable format
            'is_trading_allowed': boolean
        },
        'error': 'string' | None
    }
    """

# Start session (Super Admin only)
@http.route('/api/session/start', type='json', auth='user', methods=['POST'])
def start_session(self, **kw):
    """
    Start a new trading session
    Expected payload: {
        'session_id': 'string' (optional, if restarting existing)
    }
    Returns: {
        'success': boolean,
        'data': {
            'session_number': 'integer',
            'start_date': 'datetime'
        } | None,
        'error': 'string' | None
    }
    """

# Stop session (Super Admin only)  
@http.route('/api/session/stop', type='json', auth='user', methods=['POST'])
def stop_session(self, **kw):
    """
    Stop the current active session
    Returns: {
        'success': boolean,
        'data': {
            'session_number': 'integer',
            'end_date': 'datetime',
            'report_generation_started': boolean
        } | None,
        'error': 'string' | None
    }
    """
```

### Core Business Logic Algorithms

#### 1. Trade Matching Algorithm
```python
def match_pending_orders():
    """
    Continuously match BID and ASK orders for execution
    This is the core trading engine algorithm from the C# system
    """
    # Get all pending orders sorted by creation date (FIFO)
    ask_orders = get_pending_orders('Ask')  # Sell orders
    bid_orders = get_pending_orders('Bid')  # Buy orders
    
    for bid_order in bid_orders:
        if bid_order['remain_quantity'] == 0:
            continue
            
        for ask_order in ask_orders:
            if ask_order['remain_quantity'] == 0:
                continue
                
            # Check if orders can be matched
            if (bid_order['stock_id'] == ask_order['stock_id'] and
                bid_order['price'] >= ask_order['price'] and
                bid_order['team_id'] != ask_order['team_id']):  # No self-trading
                
                # Validate execution prerequisites
                if not validate_trade_execution(bid_order, ask_order):
                    continue
                    
                # Calculate trade details
                execution_price = min(bid_order['price'], ask_order['price'])
                trade_quantity = min(bid_order['remain_quantity'], ask_order['remain_quantity'])
                
                # Execute the trade
                execute_trade(bid_order, ask_order, execution_price, trade_quantity)
                
                # Break and restart matching after each execution
                return True  # Indicates orders were modified, restart matching
    
    return False  # No matches found

def validate_trade_execution(bid_order, ask_order):
    """
    Validate that trade can be executed
    """
    # Check seller has sufficient stock
    seller_stock_qty = get_user_stock_quantity(ask_order['team_id'], ask_order['stock_id'])
    if seller_stock_qty < min(bid_order['remain_quantity'], ask_order['remain_quantity']):
        mark_order_failed(ask_order['row_id'], "Not Enough Stocks for Asker")
        return False
    
    # Check buyer has sufficient funds
    trade_qty = min(bid_order['remain_quantity'], ask_order['remain_quantity'])
    execution_price = min(bid_order['price'], ask_order['price'])
    required_funds = trade_qty * execution_price * (1 + bid_order['broker_percentage'])
    
    buyer_balance = get_user_balance(bid_order['team_id'])
    if buyer_balance < required_funds:
        mark_order_failed(bid_order['row_id'], "Not Enough Money for Bider")
        return False
        
    return True

def execute_trade(bid_order, ask_order, execution_price, trade_quantity):
    """
    Execute a matched trade with all financial transfers
    """
    # Calculate financial flows
    buyer_cost = trade_quantity * execution_price * (1 + bid_order['broker_percentage'])
    seller_proceeds = trade_quantity * execution_price * (1 - ask_order['broker_percentage'])
    bid_broker_commission = trade_quantity * execution_price * bid_order['broker_percentage']
    ask_broker_commission = trade_quantity * execution_price * ask_order['broker_percentage']
    
    # Update user balances
    update_user_balance(bid_order['team_id'], -buyer_cost)  # Buyer pays
    update_user_balance(ask_order['team_id'], seller_proceeds)  # Seller receives
    update_user_balance(bid_order['broker_id'], bid_broker_commission)  # Bid broker commission
    update_user_balance(ask_order['broker_id'], ask_broker_commission)  # Ask broker commission
    
    # Transfer stocks
    update_user_stock(ask_order['team_id'], ask_order['stock_id'], -trade_quantity)  # Remove from seller
    add_user_stock(bid_order['team_id'], bid_order['stock_id'], trade_quantity)  # Add to buyer
    
    # Update order quantities
    update_order_quantity(bid_order['row_id'], bid_order['remain_quantity'] - trade_quantity)
    update_order_quantity(ask_order['row_id'], ask_order['remain_quantity'] - trade_quantity)
    
    # Mark completed orders
    if bid_order['remain_quantity'] - trade_quantity == 0:
        mark_order_complete(bid_order['row_id'], "bider found his stocks successfully")
    if ask_order['remain_quantity'] - trade_quantity == 0:
        mark_order_complete(ask_order['row_id'], "Asker Sold all his stocks successfully")
    
    # Record trade details
    create_trade_record(bid_order['row_id'], ask_order['row_id'], execution_price, trade_quantity)
```

#### 2. Order Validation Algorithm
```python
def validate_trading_order(order_data):
    """
    Comprehensive order validation before acceptance
    """
    errors = []
    
    # Basic data validation
    if not order_data.get('stock_id'):
        errors.append("Stock ID is required")
    if not order_data.get('client_id'):
        errors.append("Client ID is required")
    if order_data.get('type') not in ['Bid', 'Ask']:
        errors.append("Order type must be 'Bid' or 'Ask'")
    if not order_data.get('quantity') or order_data['quantity'] <= 0:
        errors.append("Quantity must be positive")
    if not order_data.get('price') or order_data['price'] <= 0:
        errors.append("Price must be positive")
    
    # Session validation
    current_session = get_current_session()
    if not current_session or current_session['status'] != 'ACTIVE':
        errors.append("Trading session is not active")
    
    # Stock status validation
    stock = get_stock_by_id(order_data['stock_id'])
    if not stock:
        errors.append("Stock not found")
    elif stock['status'] not in ['Trade', 'IPO', 'PO']:
        errors.append(f"Stock is not available for trading (status: {stock['status']})")
    
    # Price range validation
    current_price = stock['price']
    price_deviation_limit = get_system_config('OrderPercentage', 20)  # Default 20%
    max_price = current_price * (1 + price_deviation_limit / 100)
    min_price = current_price * (1 - price_deviation_limit / 100)
    
    if order_data['price'] > max_price or order_data['price'] < min_price:
        errors.append(f"Price must be within {price_deviation_limit}% of current price ({current_price})")
    
    # Quantity validation
    max_quantity_pct = get_system_config('MaxQuantityPrec', 50)  # Default 50%
    max_allowed_quantity = stock['quantity'] * max_quantity_pct / 100
    if order_data['quantity'] > max_allowed_quantity:
        errors.append(f"Quantity cannot exceed {max_quantity_pct}% of available stock")
    
    # Order-specific validation
    if order_data['type'] == 'Ask':
        # Validate seller has sufficient stock
        user_stock_qty = get_user_stock_quantity(order_data['client_id'], order_data['stock_id'])
        if user_stock_qty < order_data['quantity']:
            errors.append("Insufficient stock quantity for sell order")
    
    elif order_data['type'] == 'Bid':
        # Validate buyer has sufficient funds
        required_funds = order_data['quantity'] * order_data['price'] * (1 + order_data['broker_percentage'])
        user_balance = get_user_balance(order_data['client_id'])
        if user_balance < required_funds:
            errors.append("Insufficient funds for buy order")
    
    # Broker validation
    if order_data['broker_percentage'] > get_system_config('Broker', 0.3):  # Max 30%
        errors.append("Broker percentage exceeds maximum allowed")
    
    return errors

def validate_user_permissions(user_id, action, resource_id=None):
    """
    Validate user permissions for specific actions
    """
    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found"
    
    # Check if user is blocked
    if is_user_blocked(user_id):
        return False, "User is currently blocked"
    
    # Check user level permissions
    user_level = get_user_level(user['type'])
    
    permission_matrix = {
        'create_user': [1, 2],  # SuperAdmin, Admin
        'manage_stocks': [1],   # SuperAdmin only
        'manage_sessions': [1], # SuperAdmin only
        'place_order': [1, 2, 3], # All except blocked
        'view_reports': [1, 2, 3],
        'manage_banking': [1, 3], # SuperAdmin, Bankers
        'system_config': [1],   # SuperAdmin only
    }
    
    if action in permission_matrix:
        if user_level['level'] not in permission_matrix[action]:
            return False, f"User type '{user['type']}' not authorized for action '{action}'"
    
    return True, "Authorized"
```

#### 3. Bond Pricing Algorithm
```python
def calculate_bond_price(bond, current_session):
    """
    Calculate time-adjusted bond pricing based on bond type and time to maturity
    """
    if bond['bond_type'] == 'conventional bond':
        # Conventional bonds maintain face value
        return bond['return_price']
    
    elif bond['bond_type'] == 'amortizing bond':
        # Calculate present value based on remaining sessions
        total_sessions = bond['end_session'] - bond['start_session'] + 1
        remaining_sessions = bond['end_session'] - current_session + 1
        
        if remaining_sessions <= 0:
            return 0  # Bond has matured
        
        # Time-based pricing calculation
        time_factor = remaining_sessions / total_sessions
        return bond['return_price'] * time_factor
    
    # For other bond types, implement specific pricing logic
    return bond['price']

def calculate_bond_interest_payment(bond, session_number):
    """
    Calculate interest payment for bonds based on type and schedule
    """
    if session_number < bond['first_pay_session']:
        return 0
    
    if bond['rate_type'] == 'zero coupon bond (discount)':
        return 0  # No periodic payments
    
    elif bond['rate_type'] == 'conventional bond':
        return bond['return_price'] * bond['percentage_rate_session'] / 100
    
    elif bond['rate_type'] == 'step-up coupon bond':
        # Increasing coupon rate over time
        sessions_elapsed = session_number - bond['start_session']
        step_increases = sessions_elapsed // bond['step_sessions']  # Assuming step_sessions defined
        current_rate = bond['percentage_rate_session'] + (step_increases * bond['step_percentage'])
        return bond['return_price'] * current_rate / 100
    
    return 0
```

#### 4. Portfolio Valuation Algorithm
```python
def calculate_portfolio_value(user_id, session_number=None):
    """
    Calculate comprehensive portfolio valuation
    """
    if session_number is None:
        session_number = get_current_session_number()
    
    portfolio = {
        'cash_balance': 0,
        'stock_investments': 0,
        'bond_investments': 0,
        'mf_investments': 0,
        'deposit_accounts': 0,
        'loan_liabilities': 0,
        'total_assets': 0,
        'total_liabilities': 0,
        'net_worth': 0,
        'details': {
            'stocks': [],
            'bonds': [],
            'mutual_funds': [],
            'deposits': [],
            'loans': []
        }
    }
    
    # Get user cash balance
    user = get_user_by_id(user_id)
    portfolio['cash_balance'] = user['profit']
    
    # Calculate stock investments
    user_stocks = get_user_stocks(user_id)
    for stock_holding in user_stocks:
        stock = get_stock_by_id(stock_holding['stock_id'])
        current_value = stock_holding['quantity'] * stock['price']
        
        # Calculate VWAP (Volume Weighted Average Price)
        vwap = calculate_user_stock_vwap(user_id, stock_holding['stock_id'])
        cost_basis = stock_holding['quantity'] * vwap
        unrealized_pnl = current_value - cost_basis
        
        stock_detail = {
            'stock_id': stock_holding['stock_id'],
            'reuters_code': stock['reuters_code'],
            'company_name': stock['company_name'],
            'quantity': stock_holding['quantity'],
            'current_price': stock['price'],
            'current_value': current_value,
            'average_cost': vwap,
            'cost_basis': cost_basis,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_pct': (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
        }
        
        portfolio['details']['stocks'].append(stock_detail)
        portfolio['stock_investments'] += current_value
    
    # Calculate bond investments with time-based pricing
    user_bonds = get_user_bonds(user_id)
    for bond_holding in user_bonds:
        bond = get_bond_by_id(bond_holding['bond_id'])
        
        # Time-adjusted bond pricing
        if bond['bond_type'] == 'conventional bond':
            bond_price = bond['price']
        else:
            # Amortizing bonds - time-based valuation
            time_factor = (bond['end_session'] - session_number + 1) / (bond['end_session'] - bond['start_session'] + 1)
            bond_price = bond['return_price'] * max(0, time_factor)
        
        current_value = bond_holding['quantity'] * bond_price
        
        bond_detail = {
            'bond_id': bond_holding['bond_id'],
            'reuters_code': bond['reuters_code'],
            'company_name': bond['company_name'],
            'quantity': bond_holding['quantity'],
            'current_price': bond_price,
            'current_value': current_value,
            'maturity_session': bond['end_session'],
            'bond_type': bond['bond_type'],
            'rate_type': bond['rate_type']
        }
        
        portfolio['details']['bonds'].append(bond_detail)
        portfolio['bond_investments'] += current_value
    
    # Calculate mutual fund investments
    user_mfs = get_user_mutual_funds(user_id)
    for mf_holding in user_mfs:
        if mf_holding['is_done'] == 'Y':
            continue  # Skip completed/closed positions
            
        mf = get_mutual_fund_by_id(mf_holding['mf_id'])
        current_value = mf_holding['quantity'] * mf['price']
        
        mf_detail = {
            'mf_id': mf_holding['mf_id'],
            'name': mf['name'],
            'quantity': mf_holding['quantity'],
            'current_price': mf['price'],
            'current_value': current_value,
            'banker_id': mf_holding['banker_id']
        }
        
        portfolio['details']['mutual_funds'].append(mf_detail)
        portfolio['mf_investments'] += current_value
    
    # Calculate deposit accounts (assets)
    user_deposits = get_user_deposit_accounts(user_id)
    for deposit in user_deposits:
        if deposit['status'] != 'Active':
            continue
            
        deposit_detail = {
            'account_id': deposit['row_id'],
            'banker_name': get_user_name(deposit['banker_id']),
            'balance': deposit['profit'],
            'status': deposit['status']
        }
        
        portfolio['details']['deposits'].append(deposit_detail)
        portfolio['deposit_accounts'] += deposit['profit']
    
    # Calculate loan liabilities
    # Note: Loan system would need to be implemented based on collateral requirements
    
    # Calculate totals
    portfolio['total_assets'] = (portfolio['cash_balance'] + 
                               portfolio['stock_investments'] + 
                               portfolio['bond_investments'] + 
                               portfolio['mf_investments'] + 
                               portfolio['deposit_accounts'])
    
    portfolio['total_liabilities'] = portfolio['loan_liabilities']
    portfolio['net_worth'] = portfolio['total_assets'] - portfolio['total_liabilities']
    
    return portfolio

def calculate_user_stock_vwap(user_id, stock_id):
    """
    Calculate Volume Weighted Average Price for user's stock holdings
    """
    # Get all buy transactions for this user/stock combination
    buy_trades = get_user_stock_buy_transactions(user_id, stock_id)
    
    total_value = 0
    total_quantity = 0
    
    for trade in buy_trades:
        total_value += trade['quantity'] * trade['price']
        total_quantity += trade['quantity']
    
    return total_value / total_quantity if total_quantity > 0 else 0
```

#### 5. System Configuration Management
```python
def get_system_config(config_key, default_value=None):
    """
    Retrieve system configuration parameters
    """
    config_map = {
        'OrderPercentage': ('others', 'Settings', 'OrderPercentage', 'A3'),
        'LastTwoSessionsPercentage': ('others', 'Settings', 'LastTwoSessionsPercentage', 'A3'),
        'MarketValidation': ('others', 'Settings', 'MarketValidation', 'A3'),
        'MaxQuantityPrec': ('others', 'Settings', 'MaxQuantityPrec', 'A3'),
        'Broker': ('others', 'Settings', 'Broker', 'A3'),
        'SystemPercentage': ('others', 'Settings', 'SystemPercentage', 'A3'),
        'StockPriceChangePercentage': ('others', 'Settings', 'StockPriceChangePercentage', 'A3'),
        'BankMarkzy': ('others', 'bankMarkzy', None, 'A4'),  # Discount rates
    }
    
    if config_key in config_map:
        table, type_val, a2_val, column = config_map[config_key]
        config_value = query_system_config(table, type_val, a2_val, column)
        return float(config_value) if config_value else default_value
    
    return default_value

def update_system_config(config_key, config_value, user_id):
    """
    Update system configuration with audit trail
    """
    # Validate user permissions
    if not has_admin_permissions(user_id):
        raise PermissionError("User does not have admin permissions")
    
    # Update configuration
    config_record = get_config_record(config_key)
    if config_record:
        update_record('others', config_record['row_id'], 
                     {'A3': str(config_value), 'Modified_By': user_id})
    else:
        create_record('others', {
            'Type': 'Settings',
            'A2': config_key,
            'A3': str(config_value),
            'Created_By': user_id,
            'Modified_By': user_id
        })
    
    # Log configuration change
    log_system_event('CONFIG_CHANGE', user_id, f"Updated {config_key} to {config_value}")
```

#### 6. User Blocking Algorithm
```python
def check_user_block_status(user_id):
    """
    Check if user is currently blocked and return block details
    """
    current_time = get_current_datetime()
    current_session = get_current_session_number()
    
    # Query active blocks for user
    blocks = query_database("""
        SELECT * FROM blocked_user 
        WHERE User_ID = %s AND Status = 'Active'
        ORDER BY Created_Date DESC
    """, [user_id])
    
    for block in blocks:
        if block['Type'] == 'time':
            # Time-based block
            block_start = block['Blocked_From_Date']
            block_duration_minutes = block['Blocked_to_date']
            block_end = block_start + timedelta(minutes=block_duration_minutes)
            
            if current_time < block_end:
                return {
                    'is_blocked': True,
                    'block_type': 'time',
                    'reason': block['Reason'],
                    'expires_at': block_end,
                    'remaining_time': block_end - current_time
                }
            else:
                # Block has expired, deactivate it
                update_record('blocked_user', block['Row_ID'], {'Status': 'Inactive'})
        
        elif block['Type'] == 'session':
            # Session-based block
            block_until_session = block['Blocked_to_session']
            
            if current_session <= block_until_session:
                return {
                    'is_blocked': True,
                    'block_type': 'session',
                    'reason': block['Reason'],
                    'expires_at_session': block_until_session,
                    'remaining_sessions': block_until_session - current_session
                }
            else:
                # Block has expired, deactivate it
                update_record('blocked_user', block['Row_ID'], {'Status': 'Inactive'})
    
    return {'is_blocked': False}

def block_user(user_id, block_type, duration, reason, admin_user_id):
    """
    Block a user with specified type and duration
    """
    if block_type not in ['time', 'session']:
        raise ValueError("Block type must be 'time' or 'session'")
    
    block_data = {
        'User_ID': user_id,
        'Type': block_type,
        'Blocked_From_Date': get_current_datetime(),
        'Reason': reason,
        'Status': 'Active',
        'Created_By': admin_user_id
    }
    
    if block_type == 'time':
        block_data['Blocked_to_date'] = int(duration)  # Duration in minutes
    else:  # session
        block_data['Blocked_to_session'] = int(duration)  # Session number
    
    create_record('blocked_user', block_data)
    
    # Log blocking action
    log_system_event('USER_BLOCKED', admin_user_id, 
                    f"Blocked user {user_id} for {duration} {block_type}(s): {reason}")
```

### Error Handling and Validation Patterns

#### Comprehensive Error Response Format
```python
def create_error_response(error_code, message, details=None):
    """
    Standardized error response format
    """
    return {
        'success': False,
        'error_code': error_code,
        'error': message,
        'details': details or {},
        'timestamp': get_current_datetime().isoformat()
    }

def create_success_response(data=None, message=None):
    """
    Standardized success response format
    """
    return {
        'success': True,
        'data': data,
        'message': message,
        'timestamp': get_current_datetime().isoformat()
    }

# Error codes mapping
ERROR_CODES = {
    'VALIDATION_ERROR': 1001,
    'INSUFFICIENT_FUNDS': 1002,
    'INSUFFICIENT_STOCK': 1003,
    'USER_BLOCKED': 1004,
    'SESSION_INACTIVE': 1005,
    'PERMISSION_DENIED': 1006,
    'STOCK_NOT_FOUND': 1007,
    'ORDER_NOT_FOUND': 1008,
    'PRICE_OUT_OF_RANGE': 1009,
    'QUANTITY_EXCEEDED': 1010,
    'DUPLICATE_ENTRY': 1011,
    'SYSTEM_ERROR': 9999
}
```

### Key Technical Patterns

#### Row ID System Implementation
```python
def generate_row_id():
    """
    Generate unique Row_ID using the system's sequence
    """
    # Get next sequence number from RID table
    with get_database_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE rid SET Value = Value + 1 WHERE RID = 'RID'")
        cursor.execute("SELECT Value FROM rid WHERE RID = 'RID'")
        sequence_num = cursor.fetchone()[0]
        conn.commit()
    
    return f"1-{sequence_num}"

def update_record_with_modnum(table_name, row_id, update_data, user_id):
    """
    Update record with modification number validation
    """
    # Get current ModfNum
    current_record = get_record_by_id(table_name, row_id)
    if not current_record:
        raise RecordNotFoundError(f"Record {row_id} not found in {table_name}")
    
    current_modfnum = current_record['ModfNum']
    
    # Add system fields to update
    update_data.update({
        'ModfNum': current_modfnum + 1,
        'Modified_By': user_id,
        'Modified_Date': get_current_datetime()
    })
    
    # Update with concurrency control
    affected_rows = update_record_conditional(table_name, row_id, update_data, 
                                            {'ModfNum': current_modfnum})
    
    if affected_rows == 0:
        raise ConcurrencyError("Record was modified by another user. Please refresh and try again.")
    
    return affected_rows
```

#### Financial Precision Handling
```python
from decimal import Decimal, ROUND_HALF_UP

def format_currency(amount):
    """
    Format currency amounts with proper precision
    """
    if amount is None:
        return Decimal('0.00')
    
    return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_broker_fee(amount, percentage):
    """
    Calculate broker fee with proper rounding
    """
    fee = amount * Decimal(str(percentage))
    return fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def validate_financial_amount(amount, min_value=0, max_value=None):
    """
    Validate financial amounts
    """
    try:
        decimal_amount = Decimal(str(amount))
    except (ValueError, TypeError):
        return False, "Invalid number format"
    
    if decimal_amount < Decimal(str(min_value)):
        return False, f"Amount must be at least {min_value}"
    
    if max_value is not None and decimal_amount > Decimal(str(max_value)):
        return False, f"Amount cannot exceed {max_value}"
    
    return True, decimal_amount
```

### UI/UX Specifications

#### Layout and Navigation Structure
```python
# Main application layout based on user role
def get_user_menu_structure(user_type, user_level, user_sublevel):
    """
    Generate role-based menu structure
    """
    base_menu = {
        'Dashboard': {'url': '/dashboard', 'icon': 'fa-dashboard'},
        'Profile': {'url': '/profile', 'icon': 'fa-user'},
    }
    
    if user_level == 1:  # SuperAdmin
        base_menu.update({
            'Super Admin': {
                'submenu': {
                    'User Management': {'url': '/admin/users', 'icon': 'fa-users'},
                    'Stock Management': {'url': '/admin/stocks', 'icon': 'fa-line-chart'},
                    'Bond Management': {'url': '/admin/bonds', 'icon': 'fa-certificate'},
                    'Session Control': {'url': '/admin/sessions', 'icon': 'fa-clock-o'},
                    'System Configuration': {'url': '/admin/config', 'icon': 'fa-cogs'},
                    'Reports Generation': {'url': '/admin/reports', 'icon': 'fa-file-text'},
                    'Database Management': {'url': '/admin/database', 'icon': 'fa-database'},
                }
            },
            'Administration': {
                'submenu': {
                    'View Users': {'url': '/admin/users/view', 'icon': 'fa-list'},
                    'View Stocks': {'url': '/admin/stocks/view', 'icon': 'fa-list'},
                    'News Management': {'url': '/admin/news', 'icon': 'fa-newspaper-o'},
                    'Statistics': {'url': '/admin/statistics', 'icon': 'fa-bar-chart'},
                }
            }
        })
    
    elif user_level == 2:  # Admin
        base_menu.update({
            'Administration': {
                'submenu': {
                    'View Users': {'url': '/admin/users/view', 'icon': 'fa-list'},
                    'View Reports': {'url': '/admin/reports/view', 'icon': 'fa-file-text-o'},
                    'News Management': {'url': '/admin/news', 'icon': 'fa-newspaper-o'},
                }
            }
        })
    
    elif user_level == 3:  # Operational users
        if user_sublevel == 1:  # Banker
            base_menu.update({
                'Banking': {
                    'submenu': {
                        'Bank Accounts': {'url': '/banking/accounts', 'icon': 'fa-bank'},
                        'Deposit Management': {'url': '/banking/deposits', 'icon': 'fa-money'},
                        'Loan Management': {'url': '/banking/loans', 'icon': 'fa-handshake-o'},
                        'Certificate of Deposits': {'url': '/banking/cds', 'icon': 'fa-certificate'},
                        'Bank Portfolio': {'url': '/banking/portfolio', 'icon': 'fa-briefcase'},
                        'Banking Reports': {'url': '/banking/reports', 'icon': 'fa-file-text'},
                    }
                },
                'Mutual Funds': {
                    'submenu': {
                        'MF Management': {'url': '/mf/manage', 'icon': 'fa-pie-chart'},
                        'MF Trading': {'url': '/mf/trade', 'icon': 'fa-exchange'},
                        'MF Reports': {'url': '/mf/reports', 'icon': 'fa-file-text'},
                    }
                }
            })
        
        elif user_sublevel == 2:  # Broker
            base_menu.update({
                'Trading': {
                    'submenu': {
                        'Place Orders': {'url': '/trading/orders/new', 'icon': 'fa-plus-circle'},
                        'View Orders': {'url': '/trading/orders', 'icon': 'fa-list'},
                        'Market Data': {'url': '/trading/market', 'icon': 'fa-line-chart'},
                        'Trade History': {'url': '/trading/history', 'icon': 'fa-history'},
                        'Client Management': {'url': '/trading/clients', 'icon': 'fa-users'},
                    }
                },
                'Broker Reports': {
                    'submenu': {
                        'Commission Reports': {'url': '/broker/reports/commissions', 'icon': 'fa-dollar'},
                        'Trading Volume': {'url': '/broker/reports/volume', 'icon': 'fa-bar-chart'},
                        'Performance': {'url': '/broker/reports/performance', 'icon': 'fa-trophy'},
                    }
                }
            })
        
        elif user_sublevel == 3:  # Investor
            base_menu.update({
                'Portfolio': {
                    'submenu': {
                        'My Holdings': {'url': '/portfolio/holdings', 'icon': 'fa-briefcase'},
                        'Stock Portfolio': {'url': '/portfolio/stocks', 'icon': 'fa-line-chart'},
                        'Bond Portfolio': {'url': '/portfolio/bonds', 'icon': 'fa-certificate'},
                        'MF Holdings': {'url': '/portfolio/mutual-funds', 'icon': 'fa-pie-chart'},
                        'Performance': {'url': '/portfolio/performance', 'icon': 'fa-trophy'},
                    }
                },
                'Trading': {
                    'submenu': {
                        'Market Prices': {'url': '/market/prices', 'icon': 'fa-line-chart'},
                        'Order History': {'url': '/trading/history', 'icon': 'fa-history'},
                        'Trade Analytics': {'url': '/trading/analytics', 'icon': 'fa-bar-chart'},
                    }
                }
            })
    
    # Common menu items for all users
    base_menu.update({
        'Market': {
            'submenu': {
                'Current Prices': {'url': '/market/current-prices', 'icon': 'fa-line-chart'},
                'Market Directory': {'url': '/market/directory', 'icon': 'fa-book'},
                'Market News': {'url': '/market/news', 'icon': 'fa-newspaper-o'},
                'Rankings': {'url': '/market/rankings', 'icon': 'fa-trophy'},
            }
        },
        'Reports': {
            'submenu': {
                'My Reports': {'url': '/reports/personal', 'icon': 'fa-file-text-o'},
                'Session Reports': {'url': '/reports/sessions', 'icon': 'fa-calendar'},
            }
        }
    })
    
    return base_menu
```

#### Dashboard Components
```python
# Dashboard widget specifications based on user type
def get_dashboard_widgets(user_type, user_id):
    """
    Generate role-specific dashboard widgets
    """
    widgets = []
    
    # Common widgets for all users
    widgets.extend([
        {
            'id': 'session_info',
            'title': 'Current Session',
            'type': 'info_card',
            'size': 'col-md-3',
            'data_source': '/api/session/current',
            'refresh_interval': 30,  # seconds
            'template': 'session_info_widget.html'
        },
        {
            'id': 'user_balance',
            'title': 'Account Balance',
            'type': 'currency_card',
            'size': 'col-md-3',
            'data_source': f'/api/users/{user_id}/balance',
            'refresh_interval': 30,
            'template': 'balance_widget.html'
        },
        {
            'id': 'market_news',
            'title': 'Latest Market News',
            'type': 'news_feed',
            'size': 'col-md-6',
            'data_source': '/api/news/latest',
            'refresh_interval': 60,
            'template': 'news_widget.html'
        }
    ])
    
    if user_type == 'Investor':
        widgets.extend([
            {
                'id': 'portfolio_summary',
                'title': 'Portfolio Summary',
                'type': 'portfolio_chart',
                'size': 'col-md-6',
                'data_source': f'/api/portfolio/{user_id}/summary',
                'refresh_interval': 60,
                'template': 'portfolio_summary_widget.html'
            },
            {
                'id': 'top_performers',
                'title': 'Top Performing Stocks',
                'type': 'stock_list',
                'size': 'col-md-6',
                'data_source': f'/api/portfolio/{user_id}/top-performers',
                'refresh_interval': 120,
                'template': 'stock_list_widget.html'
            }
        ])
    
    elif user_type == 'Broker':
        widgets.extend([
            {
                'id': 'pending_orders',
                'title': 'Pending Orders',
                'type': 'order_table',
                'size': 'col-md-8',
                'data_source': f'/api/trading/orders/pending?broker_id={user_id}',
                'refresh_interval': 15,
                'template': 'pending_orders_widget.html'
            },
            {
                'id': 'daily_commissions',
                'title': "Today's Commissions",
                'type': 'currency_chart',
                'size': 'col-md-4',
                'data_source': f'/api/broker/{user_id}/daily-commissions',
                'refresh_interval': 60,
                'template': 'commission_chart_widget.html'
            }
        ])
    
    elif user_type == 'Banker':
        widgets.extend([
            {
                'id': 'deposit_summary',
                'title': 'Deposits Overview',
                'type': 'banking_summary',
                'size': 'col-md-6',
                'data_source': f'/api/banking/{user_id}/deposits-summary',
                'refresh_interval': 120,
                'template': 'deposit_summary_widget.html'
            },
            {
                'id': 'loan_portfolio',
                'title': 'Loan Portfolio',
                'type': 'loan_chart',
                'size': 'col-md-6',
                'data_source': f'/api/banking/{user_id}/loans-summary',
                'refresh_interval': 120,
                'template': 'loan_summary_widget.html'
            }
        ])
    
    return widgets
```

### Real-time Processing and Scheduled Tasks

#### Trading Engine Scheduler
```python
# Scheduled task for continuous order matching
@api.model
def _cron_match_pending_orders(self):
    """
    Scheduled task to continuously match pending trading orders
    Should run every 10-15 seconds during active sessions
    """
    try:
        # Check if there's an active session
        active_session = self.env['trading.session'].search([
            ('status', '=', 'ACTIVE')
        ], limit=1)
        
        if not active_session:
            return  # No active session, skip matching
        
        # Lock the matching process to prevent concurrent execution
        self.env.cr.execute("SELECT pg_advisory_lock(12345)")
        
        try:
            # Run the matching algorithm
            matches_found = True
            iterations = 0
            max_iterations = 100  # Prevent infinite loops
            
            while matches_found and iterations < max_iterations:
                matches_found = self._execute_order_matching()
                iterations += 1
                
                if matches_found:
                    # Commit each batch of matches
                    self.env.cr.commit()
                    
            # Update stock prices based on last trades if needed
            self._update_stock_prices_from_trades()
            
        finally:
            # Release the advisory lock
            self.env.cr.execute("SELECT pg_advisory_unlock(12345)")
            
    except Exception as e:
        _logger.error(f"Error in order matching cron: {str(e)}")
        self.env.cr.rollback()

# Portfolio valuation update scheduler
@api.model  
def _cron_update_portfolio_valuations(self):
    """
    Update portfolio valuations for all users
    Should run every few minutes to keep real-time values
    """
    try:
        # Get all users with active portfolios
        users_with_holdings = self.env['res.users'].search([
            ('user_type', 'in', ['Investor', 'Banker'])
        ])
        
        current_session = self._get_current_session_number()
        
        for user in users_with_holdings:
            try:
                # Calculate updated portfolio value
                portfolio_value = self._calculate_portfolio_value(user.id, current_session)
                
                # Update user's portfolio cache
                self._update_portfolio_cache(user.id, portfolio_value)
                
            except Exception as e:
                _logger.error(f"Error updating portfolio for user {user.id}: {str(e)}")
                continue
                
    except Exception as e:
        _logger.error(f"Error in portfolio valuation cron: {str(e)}")

# Session management scheduler
@api.model
def _cron_session_maintenance(self):
    """
    Perform session-related maintenance tasks
    """
    try:
        # Check for expired user blocks
        self._cleanup_expired_blocks()
        
        # Update session statistics
        self._update_session_statistics()
        
        # Clean up old data (if configured)
        self._cleanup_old_data()
        
        # Generate periodic reports (if scheduled)
        self._generate_scheduled_reports()
        
    except Exception as e:
        _logger.error(f"Error in session maintenance cron: {str(e)}")

def _cleanup_expired_blocks(self):
    """
    Automatically expire time-based and session-based user blocks
    """
    current_time = fields.Datetime.now()
    current_session = self._get_current_session_number()
    
    # Expire time-based blocks
    time_based_blocks = self.env['user.block'].search([
        ('block_type', '=', 'time'),
        ('status', '=', 'Active')
    ])
    
    for block in time_based_blocks:
        block_end = block.blocked_from_date + timedelta(minutes=block.blocked_to_date)
        if current_time > block_end:
            block.status = 'Inactive'
    
    # Expire session-based blocks
    session_based_blocks = self.env['user.block'].search([
        ('block_type', '=', 'session'),
        ('status', '=', 'Active'),
        ('blocked_to_session', '<', current_session)
    ])
    
    for block in session_based_blocks:
        block.status = 'Inactive'
```

#### Report Generation Algorithms
```python
def generate_end_of_session_reports(session_number):
    """
    Generate comprehensive reports at the end of each trading session
    This is the main report generation algorithm from the C# system
    """
    session_id = f"session_{session_number}"
    
    # Generate investor reports
    investors = self.env['res.users'].search([('user_type', '=', 'Investor')])
    for investor in investors:
        try:
            investor_report = self._generate_investor_report(investor.id, session_number)
            self._save_report('investor', investor.id, session_number, investor_report)
        except Exception as e:
            _logger.error(f"Error generating investor report for {investor.id}: {str(e)}")
    
    # Generate banker reports  
    bankers = self.env['res.users'].search([('user_type', '=', 'Banker')])
    for banker in bankers:
        try:
            banker_report = self._generate_banker_report(banker.id, session_number)
            self._save_report('banker', banker.id, session_number, banker_report)
        except Exception as e:
            _logger.error(f"Error generating banker report for {banker.id}: {str(e)}")
    
    # Generate broker reports
    brokers = self.env['res.users'].search([('user_type', '=', 'Broker')])
    for broker in brokers:
        try:
            broker_report = self._generate_broker_report(broker.id, session_number)
            self._save_report('broker', broker.id, session_number, broker_report)
        except Exception as e:
            _logger.error(f"Error generating broker report for {broker.id}: {str(e)}")
    
    # Generate system-wide statistics
    self._generate_system_statistics_report(session_number)

def _generate_investor_report(user_id, session_number):
    """
    Generate comprehensive investor report matching C# InvestorReport class
    """
    user = self.env['res.users'].browse(user_id)
    
    report_data = {
        'user_id': user_id,
        'user_type': 'investor',
        'session_number': session_number,
        'team_name': user.name,
        'team_members': user.team_members,
    }
    
    # Get starting capital
    report_data['initial_liquidity'] = user.start_profit
    report_data['current_liquidity'] = user.profit
    
    # Calculate stock investments
    stock_investments = 0
    stock_details = []
    user_stocks = self.env['user.stocks'].search([('user_id', '=', user_id)])
    
    for stock_holding in user_stocks:
        stock = stock_holding.stock_id
        current_value = stock_holding.quantity * stock.price
        stock_investments += current_value
        
        # Calculate VWAP for this user/stock
        vwap = self._calculate_stock_vwap(user_id, stock.id)
        
        stock_detail = {
            'reuters_code': stock.reuters_code,
            'total_quantity': stock_holding.quantity,
            'available_quantity': stock_holding.quantity - self._get_blocked_quantity(user_id, stock.id),
            'blocked_quantity': self._get_blocked_quantity(user_id, stock.id),
            'current_price': stock.price,
            'vwap': vwap,
            'ipo_price': stock.ipo_price,
        }
        stock_details.append(stock_detail)
    
    report_data['stock_investments'] = stock_investments
    report_data['stock_details'] = stock_details
    
    # Calculate bond investments with time-based pricing
    bond_investments = 0
    bond_details = []
    user_bonds = self.env['user.bonds'].search([('user_id', '=', user_id)])
    
    for bond_holding in user_bonds:
        bond = bond_holding.bond_id
        # Time-adjusted bond pricing
        if bond.end_session >= session_number >= bond.start_session:
            if bond.bond_type == 'conventional bond':
                bond_price = bond.price
            else:
                # Amortizing bond - time-based valuation
                time_factor = (bond.end_session - session_number + 1) / (bond.end_session - bond.start_session + 1)
                bond_price = bond.return_price * max(0, time_factor)
        else:
            bond_price = 0
            
        current_value = bond_holding.quantity * bond_price
        bond_investments += current_value
        
        bond_detail = {
            'reuters_code': bond.reuters_code,
            'quantity': bond_holding.quantity,
            'current_price': bond_price,
            'maturity_session': bond.end_session,
            'bond_type': bond.bond_type,
        }
        bond_details.append(bond_detail)
    
    report_data['bond_investments'] = bond_investments
    report_data['bond_details'] = bond_details
    
    # Calculate deposit accounts
    deposit_value = 0
    deposit_details = []
    user_deposits = self.env['deposit.account'].search([
        ('user_id', '=', user_id),
        ('status', '=', 'Active')
    ])
    
    for deposit in user_deposits:
        deposit_value += deposit.profit
        deposit_details.append({
            'banker_name': deposit.banker_id.name,
            'balance': deposit.profit,
        })
    
    report_data['deposits'] = deposit_value
    report_data['deposit_details'] = deposit_details
    
    # Calculate mutual fund investments
    mf_investments = 0
    mf_details = []
    user_mfs = self.env['user.mf'].search([
        ('user_id', '=', user_id),
        ('is_done', '=', 'N')
    ])
    
    for mf_holding in user_mfs:
        mf = mf_holding.mf_id
        current_value = mf_holding.quantity * mf.price
        mf_investments += current_value
        
        mf_details.append({
            'mf_name': mf.name,
            'quantity': mf_holding.quantity,
            'current_price': mf.price,
            'current_value': current_value,
        })
    
    report_data['mf_investments'] = mf_investments
    report_data['mf_details'] = mf_details
    
    # Calculate totals
    report_data['total_investments'] = stock_investments + bond_investments + mf_investments
    report_data['account_value'] = (report_data['current_liquidity'] + 
                                  report_data['total_investments'] + 
                                  report_data['deposits'])
    
    # Calculate performance metrics
    overall_change = report_data['account_value'] - report_data['initial_liquidity']
    percentage_change = (overall_change / report_data['initial_liquidity'] * 100) if report_data['initial_liquidity'] > 0 else 0
    
    report_data['overall_change'] = overall_change
    report_data['percentage_change'] = percentage_change
    
    return report_data

def _calculate_stock_vwap(self, user_id, stock_id):
    """
    Calculate Volume Weighted Average Price for user's stock purchases
    """
    # Get all buy transactions for this user/stock
    buy_transactions = self.env.cr.execute("""
        SELECT dt.quantity, dt.price
        FROM detailtrans dt
        JOIN tranlog tl_bid ON dt.bid_row_id = tl_bid.row_id
        WHERE tl_bid.team_id = %s 
        AND tl_bid.stock_id = %s
        AND tl_bid.type = 'Bid'
    """, [user_id, stock_id])
    
    transactions = self.env.cr.fetchall()
    
    total_value = 0
    total_quantity = 0
    
    for quantity, price in transactions:
        total_value += quantity * price
        total_quantity += quantity
    
    return total_value / total_quantity if total_quantity > 0 else 0
```

### Performance and Optimization Specifications

#### Database Indexing Strategy
```sql
-- Critical indexes for performance
-- Trading orders - frequently queried by stock, status, and type
CREATE INDEX idx_tranlog_matching ON tranlog(stock_id, type, status, created_date);
CREATE INDEX idx_tranlog_user_orders ON tranlog(team_id, broker_id, status);

-- Portfolio queries - user holdings
CREATE INDEX idx_user_stocks_portfolio ON user_stocks(user_id, stock_id, quantity);
CREATE INDEX idx_user_bonds_portfolio ON user_bonds(user_id, bond_id, quantity);

-- Price history for charts and analytics  
CREATE INDEX idx_price_changes_timeline ON stockpricechange(stock_id, created_date);
CREATE INDEX idx_bond_price_changes_timeline ON bondpricechange(bond_id, created_date);

-- Session-based queries
CREATE INDEX idx_tranlog_session ON tranlog(session_no, status);
CREATE INDEX idx_reports_session ON report_main(session_no, user_id);

-- User blocking system performance
CREATE INDEX idx_blocks_active_check ON blocked_user(user_id, status, blocked_from_date, type);

-- News and alerts
CREATE INDEX idx_news_active ON news(status, start_session, end_session);
CREATE INDEX idx_alerts_user_session ON alerts(user_id, session_no);

-- Financial calculations
CREATE INDEX idx_deposits_banker ON deposit_accounts(banker_id, status);
CREATE INDEX idx_mf_active ON user_mf(user_id, is_done);
```

#### Caching Strategy
```python
# Redis-based caching for frequently accessed data
def get_cached_stock_price(stock_id):
    """
    Get cached stock price with fallback to database
    """
    cache_key = f"stock_price_{stock_id}"
    
    # Try to get from cache first
    cached_price = redis_client.get(cache_key)
    if cached_price:
        return float(cached_price)
    
    # Fallback to database
    stock = self.env['trading.stock'].browse(stock_id)
    if stock.exists():
        # Cache for 30 seconds
        redis_client.setex(cache_key, 30, str(stock.price))
        return stock.price
    
    return None

def invalidate_stock_cache(stock_id):
    """
    Invalidate stock-related cache entries
    """
    cache_keys = [
        f"stock_price_{stock_id}",
        f"stock_info_{stock_id}",
        f"order_book_{stock_id}",
    ]
    
    for key in cache_keys:
        redis_client.delete(key)

def get_cached_portfolio_value(user_id):
    """
    Get cached portfolio valuation
    """
    cache_key = f"portfolio_value_{user_id}"
    
    cached_value = redis_client.get(cache_key)
    if cached_value:
        return json.loads(cached_value)
    
    # Calculate and cache for 60 seconds
    portfolio_value = self._calculate_portfolio_value(user_id)
    redis_client.setex(cache_key, 60, json.dumps(portfolio_value))
    
    return portfolio_value
```

### Security Architecture

#### Authentication and Authorization Framework
```python
class TradingSecurityMixin:
    """
    Security mixin for trading system models
    """
    
    def _check_user_permissions(self, operation, resource_id=None):
        """
        Check if current user has permission for operation
        """
        current_user = self.env.user
        
        # Check if user is blocked
        if self._is_user_blocked(current_user.id):
            raise AccessError(_("User is currently blocked from system access"))
        
        # Get user level and permissions
        user_level = self._get_user_level(current_user)
        
        # Define permission matrix
        permission_rules = {
            'stock.create': lambda u: u['level'] == 1,  # SuperAdmin only
            'stock.write': lambda u: u['level'] == 1,   # SuperAdmin only
            'stock.read': lambda u: True,               # All users
            
            'order.create': lambda u: u['level'] in [1, 2, 3] and u['sublevel'] == 2,  # Brokers
            'order.read': lambda u: self._check_order_access(u, resource_id),
            
            'session.manage': lambda u: u['level'] == 1,  # SuperAdmin only
            
            'user.create': lambda u: u['level'] in [1, 2],  # SuperAdmin, Admin
            'user.block': lambda u: u['level'] in [1, 2],   # SuperAdmin, Admin
            
            'banking.manage': lambda u: u['level'] in [1] or (u['level'] == 3 and u['sublevel'] == 1),  # SuperAdmin, Bankers
            
            'report.view': lambda u: self._check_report_access(u, resource_id),
        }
        
        permission_key = f"{self._name.replace('.', '')}.{operation}"
        if permission_key in permission_rules:
            if not permission_rules[permission_key](user_level):
                raise AccessError(_("Insufficient permissions for this operation"))
        
        return True
    
    def _is_user_blocked(self, user_id):
        """
        Check if user is currently blocked
        """
        current_time = fields.Datetime.now()
        current_session = self._get_current_session_number()
        
        active_blocks = self.env['user.block'].search([
            ('user_id', '=', user_id),
            ('status', '=', 'Active'),
            '|',
            '&', ('block_type', '=', 'time'),
                 ('blocked_from_date', '<=', current_time),
            '&', ('block_type', '=', 'session'),
                 ('blocked_to_session', '>=', current_session)
        ])
        
        return len(active_blocks) > 0
    
    def _check_data_access(self, record_ids):
        """
        Ensure users can only access their own data
        """
        current_user = self.env.user
        
        # SuperAdmin can access all data
        if self._get_user_level(current_user)['level'] == 1:
            return True
        
        # Check ownership for specific models
        if self._name == 'user.portfolio':
            allowed_records = self.search([
                ('id', 'in', record_ids),
                ('user_id', '=', current_user.id)
            ])
            return len(allowed_records) == len(record_ids)
        
        # Brokers can access their client's data
        if self._name == 'trading.order':
            allowed_records = self.search([
                ('id', 'in', record_ids),
                '|', ('broker_id', '=', current_user.id),
                     ('team_id', '=', current_user.id)
            ])
            return len(allowed_records) == len(record_ids)
        
        return True

# Input validation and sanitization
def validate_trading_input(data):
    """
    Comprehensive input validation for trading operations
    """
    validators = {
        'price': lambda x: isinstance(x, (int, float)) and x > 0,
        'quantity': lambda x: isinstance(x, int) and x > 0,
        'stock_id': lambda x: isinstance(x, str) and len(x) > 0,
        'broker_percentage': lambda x: isinstance(x, (int, float)) and 0 <= x <= 0.5,
    }
    
    errors = []
    for field, validator in validators.items():
        if field in data:
            if not validator(data[field]):
                errors.append(f"Invalid {field}: {data[field]}")
    
    # SQL injection prevention - ensure all IDs are properly formatted
    if 'stock_id' in data:
        if not re.match(r'^1-\d+$', str(data['stock_id'])):
            errors.append("Invalid stock ID format")
    
    if 'user_id' in data:
        if not re.match(r'^1-\d+$', str(data['user_id'])):
            errors.append("Invalid user ID format")
    
    return errors

# Audit logging system
def log_security_event(event_type, user_id, details, severity='INFO'):
    """
    Log security-related events
    """
    security_log = {
        'timestamp': fields.Datetime.now(),
        'event_type': event_type,
        'user_id': user_id,
        'details': details,
        'severity': severity,
        'ip_address': request.httprequest.environ.get('REMOTE_ADDR'),
        'user_agent': request.httprequest.environ.get('HTTP_USER_AGENT'),
    }
    
    # Log to database
    self.env['security.log'].create(security_log)
    
    # Log to system logger for high-severity events
    if severity in ['ERROR', 'CRITICAL']:
        _logger.error(f"Security Event [{event_type}]: {details} - User: {user_id}")
```

### Deployment and Configuration

#### Environment Configuration
```python
# Production deployment configuration
DEPLOYMENT_CONFIG = {
    'database': {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', '3306'),
        'name': os.environ.get('DB_NAME', 'borsa'),
        'user': os.environ.get('DB_USER', 'newuser1'),
        'password': os.environ.get('DB_PASSWORD', '1234'),
        'charset': 'utf8mb4',
        'connection_pool_size': int(os.environ.get('DB_POOL_SIZE', '20')),
    },
    
    'redis': {
        'host': os.environ.get('REDIS_HOST', 'localhost'),
        'port': int(os.environ.get('REDIS_PORT', '6379')),
        'db': int(os.environ.get('REDIS_DB', '0')),
        'password': os.environ.get('REDIS_PASSWORD'),
    },
    
    'trading_engine': {
        'matching_interval': int(os.environ.get('MATCHING_INTERVAL', '10')),  # seconds
        'max_iterations_per_run': int(os.environ.get('MAX_MATCH_ITERATIONS', '100')),
        'portfolio_update_interval': int(os.environ.get('PORTFOLIO_UPDATE_INTERVAL', '60')),
        'price_cache_ttl': int(os.environ.get('PRICE_CACHE_TTL', '30')),
    },
    
    'security': {
        'session_timeout': int(os.environ.get('SESSION_TIMEOUT', '3600')),  # seconds
        'max_login_attempts': int(os.environ.get('MAX_LOGIN_ATTEMPTS', '5')),
        'password_min_length': int(os.environ.get('PASSWORD_MIN_LENGTH', '8')),
        'enable_audit_logging': os.environ.get('ENABLE_AUDIT_LOGGING', 'True').lower() == 'true',
    },
    
    'performance': {
        'enable_caching': os.environ.get('ENABLE_CACHING', 'True').lower() == 'true',
        'cache_ttl_default': int(os.environ.get('CACHE_TTL_DEFAULT', '300')),
        'max_concurrent_trades': int(os.environ.get('MAX_CONCURRENT_TRADES', '1000')),
        'database_query_timeout': int(os.environ.get('DB_QUERY_TIMEOUT', '30')),
    }
}

# System initialization and health checks
def initialize_trading_system():
    """
    Initialize trading system with proper configuration
    """
    # Check database connectivity
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            _logger.info("Database connectivity: OK")
    except Exception as e:
        _logger.critical(f"Database connectivity failed: {str(e)}")
        raise SystemExit("Cannot connect to database")
    
    # Check Redis connectivity
    if DEPLOYMENT_CONFIG['performance']['enable_caching']:
        try:
            redis_client.ping()
            _logger.info("Redis connectivity: OK")
        except Exception as e:
            _logger.warning(f"Redis connectivity failed: {str(e)}. Caching disabled.")
    
    # Initialize system configuration
    initialize_default_system_config()
    
    # Create default admin user if not exists
    create_default_admin_user()
    
    # Setup scheduled tasks
    setup_cron_jobs()
    
    _logger.info("Trading system initialization completed successfully")

def setup_cron_jobs():
    """
    Configure scheduled tasks for the trading system
    """
    cron_configs = [
        {
            'name': 'Order Matching Engine',
            'interval': DEPLOYMENT_CONFIG['trading_engine']['matching_interval'],
            'function': 'match_pending_orders',
            'active_only': True,  # Only run during active sessions
        },
        {
            'name': 'Portfolio Valuation Update',
            'interval': DEPLOYMENT_CONFIG['trading_engine']['portfolio_update_interval'],
            'function': 'update_portfolio_valuations',
            'active_only': False,
        },
        {
            'name': 'User Block Cleanup',
            'interval': 300,  # 5 minutes
            'function': 'cleanup_expired_blocks',
            'active_only': False,
        },
        {
            'name': 'System Health Check',
            'interval': 600,  # 10 minutes
            'function': 'system_health_check',
            'active_only': False,
        }
    ]
    
    for cron_config in cron_configs:
        setup_individual_cron(cron_config)

# System health monitoring
def system_health_check():
    """
    Perform comprehensive system health check
    """
    health_status = {
        'timestamp': fields.Datetime.now(),
        'database': 'OK',
        'cache': 'OK',
        'trading_engine': 'OK',
        'active_users': 0,
        'pending_orders': 0,
        'system_errors': 0,
    }
    
    try:
        # Check database performance
        start_time = time.time()
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
        db_response_time = time.time() - start_time
        
        if db_response_time > 1.0:  # Slow database response
            health_status['database'] = f'SLOW ({db_response_time:.2f}s)'
        
        health_status['active_users'] = user_count
        
    except Exception as e:
        health_status['database'] = f'ERROR: {str(e)}'
    
    # Check cache performance
    if DEPLOYMENT_CONFIG['performance']['enable_caching']:
        try:
            start_time = time.time()
            redis_client.ping()
            cache_response_time = time.time() - start_time
            
            if cache_response_time > 0.1:
                health_status['cache'] = f'SLOW ({cache_response_time:.3f}s)'
                
        except Exception as e:
            health_status['cache'] = f'ERROR: {str(e)}'
    
    # Check trading engine status
    try:
        pending_orders = self.env['trading.order'].search_count([
            ('status', '=', 'Pending')
        ])
        health_status['pending_orders'] = pending_orders
        
        if pending_orders > 1000:  # High order backlog
            health_status['trading_engine'] = f'BACKLOG ({pending_orders} orders)'
            
    except Exception as e:
        health_status['trading_engine'] = f'ERROR: {str(e)}'
    
    # Log health status
    _logger.info(f"System Health Check: {health_status}")
    
    # Alert on critical issues
    critical_issues = [k for k, v in health_status.items() if isinstance(v, str) and 'ERROR' in v]
    if critical_issues:
        _logger.critical(f"Critical system issues detected: {critical_issues}")
    
    return health_status
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
**Objective**: Establish core system infrastructure

**Deliverables**:
- User management system with role-based access
- Authentication and session management
- Basic database schema implementation
- System configuration framework
- Admin interface for user management

**User Stories Included**:
- Secure User Login
- Comprehensive User Management
- Password Management
- User Blocking System
- System Configuration Management

**Success Criteria**:
- Users can register, login, and manage accounts
- Role-based access control functioning
- Admin can create and manage users
- System parameters configurable

---

### Phase 2: Core Trading (Weeks 5-10)
**Objective**: Implement basic trading functionality

**Deliverables**:
- Stock management system
- Trading order creation and management
- Basic order matching engine
- Portfolio tracking
- Session management

**User Stories Included**:
- Stock Management
- Trading Order Creation
- Market Session Control
- Real-time Order Book
- Portfolio Management

**Success Criteria**:
- Stocks can be created and managed
- Users can place BID/ASK orders
- Orders execute automatically when matched
- Portfolios update in real-time

---

### Phase 3: Advanced Trading (Weeks 11-16)
**Objective**: Enhanced trading features and validation

**Deliverables**:
- Automatic trade matching engine
- Advanced order validation
- Price controls and circuit breakers
- Trade history and reporting
- Market data management

**User Stories Included**:
- Automatic Trade Matching
- Trade Validation System
- Market Control Tools
- Session Information Display
- Performance Analytics

**Success Criteria**:
- Complex multi-party trades execute correctly
- Market integrity controls prevent manipulation
- Comprehensive trade history available
- Real-time market data feeds working

---

### Phase 4: Banking Operations (Weeks 17-22)
**Objective**: Full banking functionality

**Deliverables**:
- Deposit account management
- Loan origination and servicing
- Interest calculation engine
- Certificate of deposit products
- Banking risk management

**User Stories Included**:
- Deposit Account Management
- Loan Management System
- Certificate of Deposit Products
- Banking Portfolio Dashboard
- Banking Business Reports

**Success Criteria**:
- Banks can offer deposit products
- Loan system with collateral management working
- Interest calculations accurate
- Banking reports comprehensive

---

### Phase 5: Bonds and MF (Weeks 23-28)
**Objective**: Fixed income and mutual fund capabilities

**Deliverables**:
- Bond trading system
- Complex bond pricing models
- Mutual fund management
- NAV calculations
- Fund performance tracking

**User Stories Included**:
- Bond Management
- Bond Trading Orders
- Bond Portfolio Tracking
- Mutual Fund Product Management
- Mutual Fund Operations
- Mutual Fund Investment

**Success Criteria**:
- Bonds trade with proper pricing
- Complex bond structures supported
- Mutual funds operate correctly
- NAV calculations accurate

---

### Phase 6: Analytics and Reporting (Weeks 29-34)
**Objective**: Comprehensive reporting and analytics

**Deliverables**:
- Portfolio reporting system
- Performance analytics
- Risk management reports
- Regulatory reporting
- Business intelligence dashboards

**User Stories Included**:
- Comprehensive Portfolio Reports
- Performance Rankings System
- System-wide Analytics
- Broker Performance Reports
- Performance Analytics

**Success Criteria**:
- All user types have appropriate reports
- Performance calculations accurate
- Rankings system functional
- Analytics provide business insights

---

### Phase 7: Market Features (Weeks 35-40)
**Objective**: Market simulation and engagement features

**Deliverables**:
- News management system
- Market event simulation
- Competition and ranking systems
- Advanced market controls
- User engagement features

**User Stories Included**:
- Market News Management
- News Consumption
- Performance Rankings System
- Market Validation Controls
- Penalty and Bonus System

**Success Criteria**:
- News system drives market activity
- Rankings motivate user engagement
- Market controls maintain integrity
- Gamification elements working

---

### Phase 8: Administration (Weeks 41-44)
**Objective**: Complete system administration tools

**Deliverables**:
- Complete admin dashboard
- System monitoring tools
- Database management utilities
- Backup and recovery systems
- Performance optimization

**User Stories Included**:
- Database Management
- System Configuration Management
- Market Control Tools
- Comprehensive system administration

**Success Criteria**:
- Admins have full system control
- System monitoring comprehensive
- Backup/recovery tested
- Performance optimized

---

## Business Rules

### Trading Rules
1. **Order Matching**: BID price ≥ ASK price for execution
2. **Execution Price**: Minimum of BID and ASK prices (favorable to buyer)
3. **Order Priority**: First In, First Out (FIFO) for same-priced orders
4. **Self-Trading**: Same team/user cannot trade with itself
5. **Price Limits**: Orders must be within ±20% of current market price
6. **Session Trading**: Orders only accepted during active sessions
7. **Partial Fills**: Orders can be partially executed, remainder stays pending

### Financial Rules
1. **Account Validation**: Sufficient funds required before order acceptance
2. **Stock Ownership**: Must own stocks to place sell orders
3. **Broker Fees**: Mandatory on all trades, paid by both parties
4. **Interest Calculations**: Based on daily balances or per-session rates
5. **Margin Requirements**: Loans require collateral with safety margins
6. **Currency**: All amounts in EGP (Egyptian Pounds)
7. **Precision**: Financial amounts to 2 decimal places

### Risk Management Rules
1. **Position Limits**: Maximum position size per user/stock
2. **Concentration Limits**: Portfolio diversification requirements
3. **Collateral Monitoring**: Daily mark-to-market of loan collateral
4. **Margin Calls**: Automatic when collateral falls below threshold
5. **Circuit Breakers**: Trading halts on extreme price movements
6. **Bank Capital**: Banks must maintain minimum capital ratios
7. **Liquidity Requirements**: Minimum cash reserves for operations

### Session Management Rules
1. **Single Active Session**: Only one session can be active system-wide
2. **Sequential Sessions**: Sessions must be numbered sequentially
3. **Session Data**: All transactions tied to specific sessions
4. **End-of-Session**: Automatic report generation when session ends
5. **Session Transition**: Clear procedures for session changes
6. **Historical Integrity**: Past session data cannot be modified

### User Management Rules
1. **Unique Identifiers**: Usernames must be unique system-wide
2. **Role Hierarchy**: Higher-level users can manage lower-level users
3. **Permission Inheritance**: Users inherit all permissions of their level
4. **Account Status**: Blocked users cannot perform any transactions
5. **Team Relationships**: Team members can be assigned to users
6. **Initial Capital**: All users start with defined capital amounts

### Data Integrity Rules
1. **Audit Trail**: All changes logged with user and timestamp
2. **Modification Control**: ModfNum prevents concurrent updates
3. **Referential Integrity**: Foreign key relationships enforced
4. **Status Consistency**: Status changes follow defined workflows
5. **Balance Reconciliation**: Total system balance must always balance
6. **Transaction Atomicity**: Complex operations are all-or-nothing

### Validation Rules
1. **Input Validation**: All user inputs validated before processing
2. **Business Logic Validation**: Rules enforced at application level
3. **Database Constraints**: Additional validation at database level
4. **Real-time Checks**: Continuous monitoring of system state
5. **Exception Handling**: Graceful handling of error conditions
6. **Recovery Procedures**: Defined processes for error recovery

### Reporting Rules
1. **Real-time Updates**: Portfolio values updated immediately
2. **Historical Accuracy**: Past reports remain unchanged
3. **Calculation Consistency**: Same formulas used across all reports
4. **Access Control**: Users can only see their own data
5. **Export Capabilities**: Reports available in multiple formats
6. **Audit Requirements**: All report generation logged

These business rules ensure system integrity, user protection, market fairness, and regulatory compliance while providing a realistic trading simulation environment.
