# Kotak Neo Trading Platform

## Overview
A comprehensive trading platform integrated with Kotak Neo API for real-time portfolio management, trading operations, and market data analysis. The project aims to provide a robust and secure platform for users to manage their trading accounts, view live market data, and execute trades directly through the Kotak Neo API. It prioritizes authentic data and a seamless user experience for active traders.

## User Preferences
- **Data Policy**: Absolutely no sample, demo, mock, or placeholder data allowed
- **Authentication**: Real trading account authentication only
- **Data Sources**: All data must come from live Kotak Neo API
- **Performance**: Proper loading states for all data sections and charts
- **Date Filtering**: Functional date filtering for "Last 10 Days" and "Last 6 Days" options

## System Architecture
The platform is built with a Flask backend, utilizing SQLAlchemy for ORM and PostgreSQL for database management. The frontend uses HTML/CSS/JavaScript with Bootstrap for a responsive UI.

**Core Architectural Decisions:**
- **Modular Structure**: The application follows a highly modular design, separating concerns into dedicated API modules (`auth_api`, `dashboard_api`, `trading_api`, `signals_api`), `core` utilities, and `config` for centralized database management.
- **Centralized Database Configuration**: A `config/database_config.py` module acts as a single source of truth for all database connections, ensuring consistency, security, and easy management of credentials via environment variables.
- **Dynamic User-Specific Data**: The system supports dynamic creation and management of user-specific deal tables in the external PostgreSQL database, enabling personalized trading data for each registered user.
- **Real-time Data Processing**: Integrates live market data (CMP, historical prices) directly from Kotak Neo API and external database sources, with complex calculation logic for profit/loss, target prices, and historical comparisons.
- **UI/UX Design**:
    - **Modern & Responsive UI**: Utilizes Bootstrap for a responsive design, with specific enhancements for mobile devices (e.g., touch-friendly scrolling, improved form elements).
    - **Consistent Styling**: Employs a consistent visual language across all pages, including compact table layouts, standardized button sizes, and professional email templates.
    - **Interactive Elements**: Features dynamic elements like sortable table headers, search and filter functionalities, and interactive charts for market data visualization.
    - **Loading States**: Incorporates shimmer loading UIs for a better user experience during data fetching.
    - **Modal System**: Enhanced modal popups with consistent styling, theme awareness, and improved responsiveness.

**Key Technical Implementations:**
- **Authentication System**: Robust user registration and login system with auto-generated usernames, email verification, and secure password management.
- **Deals Management**: Comprehensive functionality for managing trading deals, including adding, editing (entry/target price), and closing deals with confirmation dialogs.
- **Enhanced Modal System**: Draggable and resizable modals for edit/close deal operations, allowing users to reposition and resize modal windows to view underlying data while interacting with the modals. Modals have no backdrop overlay, enabling full interaction with the data table behind them.
- **Enhanced Deal Management Forms**: 
  - Edit Deal Modal: Includes Deal ID display, date field (ddmmyy format), quantity, entry price, TPR percentage, and target price fields
  - Close Deal Modal: Includes Deal ID display, exit date (ddmmyy format), and exit price fields with proper validation
- **Charting Functionality**: Integrated candlestick charts with proper state management and real-time data display.
- **Data Analysis Tools**: Dedicated web interfaces and scripts for analyzing the structure of real trading data from the API.

## External Dependencies
- **Kotak Neo API**: Primary API for all real-time trading data, authentication, and operations.
- **PostgreSQL**: Used as the primary database, specifically deployed on Render (dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com).
- **Flask**: Python web framework.
- **SQLAlchemy**: Python SQL toolkit and Object Relational Mapper.
- **Bootstrap 5.1.3**: Frontend framework for responsive design.
- **Plotly**: For charting and data visualization.
- **SweetAlert2**: For interactive and visually appealing alert/confirmation dialogs.
- **python-dotenv**: For managing environment variables securely.
- **Gmail SMTP**: For sending email confirmations and notifications.

## Email Notification System
A comprehensive email notification system has been implemented with 4 specific notification cases:

**RECENT FIXES (Aug 2025):**
- ✅ Successfully migrated project from Replit Agent to standard Replit environment
- ✅ Fixed email notification toggle state persistence issue completely
- ✅ Created dedicated API endpoints for email notification state management
- ✅ Implemented real-time toggle saving in base.js for immediate state persistence
- ✅ Enhanced database integration with proper authentication and error handling
- ✅ Fixed missing email notifications for deal creation (Case 2)
- ✅ Fixed missing email notifications for deal closure (Case 4)
- ✅ Fixed deal deletion functionality with proper email notifications
- ✅ Added get_deal_by_id method to support deal deletion operations
- ✅ Improved import error handling and code robustness
- ✅ Added Market Watch page with dual table structure (Default + User Custom lists)
- ✅ Implemented comprehensive Market Watch functionality with add/remove symbols
- ✅ Created responsive table UI with live market data columns (ID, Symbol, 7D, 30D, 7D%, 30D%, CMP, %CHAN, CPL, Actions)
- ✅ Enhanced Custom Watchlists with search, filter, and pagination functionality matching Default Market Watch
- ✅ Updated CSV storage format to include proper headers ("market watch, symbol 1, symbol 2, symbol 3...")
- ✅ Improved symbol search input in addSymbolModal with enhanced autocomplete suggestions based on first letter matching
- ✅ Added comprehensive search and pagination controls for all custom watchlist cards

**Case 1: Trade Signal Notifications to External Users**
- Triggers when admin creates new trading signals
- Sends email alerts to external users about new trading opportunities
- Integrated in `api/admin.py` - `send_signal` endpoint

**Case 2: Deal Creation Notifications** 
- Triggers when users create new deals from trading signals
- Sends confirmation emails with deal details (symbol, quantity, entry price, investment amount)
- Integrated in `api/deals_api.py` - `create_deal_from_signal` endpoint

**Case 3: Daily Trading Signal Change Emails (Subscription-based)**
- Scheduled daily emails summarizing trading signal changes from last 24 hours
- Users can subscribe/unsubscribe via email settings
- Implemented via `Scripts/daily_email_scheduler.py` with background scheduler

**Case 4: Deal Status Notifications**
- Triggers when users close deals
- Sends emails with closure details including P&L calculations
- Integrated in `api/deals_api.py` - `close_deal` endpoint

**Technical Implementation:**
- SMTP Configuration: Gmail SMTP with credentials from environment variables
- Email Templates: Professional HTML templates for each notification type
- Database Integration: Uses external PostgreSQL database for user email settings
- User Preferences: Users can enable/disable each notification type individually
- Error Handling: Graceful failure - email errors don't break application functionality