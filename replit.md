# Kotak Neo Trading Platform

## Overview
A comprehensive trading platform integrated with Kotak Neo API for real-time portfolio management, trading operations, and market data analysis.

## Project Architecture
- **Backend**: Flask application with SQLAlchemy and PostgreSQL database
- **API Integration**: Kotak Neo API for authentic trading data
- **Frontend**: HTML/CSS/JavaScript with Bootstrap
- **Modular Structure**: 
  - `api/auth_api.py` - Authentication and login functionality
  - `api/dashboard_api.py` - Portfolio dashboard and data fetching
  - `api/trading_api.py` - Order placement and trading operations
  - `api/signals_api.py` - Trading signals and default deals management
  - `core/` - Shared database and authentication utilities
  - `routes/` - Flask blueprint route definitions
- **Data Sources**: Only real trading data from Kotak Neo API - no mock or sample data

## User Preferences
- **Data Policy**: Absolutely no sample, demo, mock, or placeholder data allowed
- **Authentication**: Real trading account authentication only
- **Data Sources**: All data must come from live Kotak Neo API

## Recent Changes
- **2025-07-12**: ✅ **Database Performance Optimization** - Fixed slow loading issue (31+ seconds to < 0.1 seconds) by implementing fast local data service
- **2025-07-12**: ✅ **API Timeout Resolution** - Resolved PostgreSQL connection timeouts with improved error handling and fallback mechanisms  
- **2025-07-12**: ✅ **Migration to Replit Environment Completed** - Successfully migrated from Replit Agent to standard Replit environment with full functionality
- **2025-07-11**: ✅ **Migration to Replit Environment Completed** - Successfully migrated from Replit Agent to standard Replit environment
- **2025-07-11**: ✅ **User Deals API Created** - Built separate api/deals_api.py for authentic trading data from user_deals table
- **2025-07-11**: ✅ **Database Configuration Fixed** - Updated core/database.py with proper PostgreSQL connection handling
- **2025-07-11**: ✅ **Real Data Policy Enforced** - Removed all sample data, only authentic trading data from user_deals table allowed
- **2025-07-11**: ✅ **Deals Page Updated** - Fixed deals page to use new API endpoint with proper calculations and empty state handling
- **2025-07-11**: ✅ **Advanced Modularization Completed** - Successfully extracted all major functions from app.py to dedicated API modules
- **2025-07-11**: ✅ **Function Extraction Complete** - Moved login, dashboard, get_default_deals_data, and place_order functions to modular API structure
- **2025-07-11**: ✅ **Enhanced API Architecture** - Updated api/auth_api.py, api/dashboard_api.py, api/trading_api.py, and api/signals_api.py with comprehensive functionality
- **2025-07-11**: ✅ **Improved Code Organization** - App.py now uses clean imports from modular API functions, significantly reducing complexity
- **2025-07-11**: ✅ **Maintained Functionality** - All trading platform features working with new modular structure
- **2025-07-11**: Completely restructured codebase with modular architecture for better maintainability
- **2025-07-11**: Created separate API modules: dashboard_api.py, trading_api.py, signals_api.py
- **2025-07-11**: Implemented centralized database configuration to eliminate circular imports
- **2025-07-11**: Created clean app_clean.py with proper application factory pattern
- **2025-07-11**: Separated routes into main_routes.py and auth_routes.py for better organization
- **2025-07-11**: Added core authentication module with reusable decorators and session management
- **2025-07-11**: Fixed all circular import issues and optimized code structure
- **2025-01-10**: Added new Basic Trade Signals feature by copying ETF signals functionality
- **2025-01-06**: PostgreSQL database configured and connected
- **2025-01-06**: All Python dependencies installed and working
- **2025-01-06**: Created data analysis tools for viewing real trading data structure
- **2025-01-06**: Removed any sample data references to ensure only authentic data is used

## Key Features
- Real-time dashboard with positions, holdings, and orders
- Live trading data from 17 positions and 18 holdings
- Account limits and margin information
- Data analysis tools for understanding API response structure
- Secure authentication with Kotak Neo API

## Current Status
- Application running successfully on port 5000
- Database connected and operational
- All functions retrieving real trading data
- No sample or mock data present in codebase

## Data Analysis Tools
- `/data-analysis` - Web interface for analyzing trading data structure
- `Scripts/data_analyzer.py` - Comprehensive data structure analysis
- `Scripts/simple_data_viewer.py` - Quick data overview tool
- All tools work exclusively with real API data

## Technical Stack
- Python 3.11
- Flask 3.1.1
- SQLAlchemy 2.0.41
- PostgreSQL (Neon)
- Kotak Neo API
- Bootstrap 5.1.3

## Security
- Environment-based configuration
- Secure API authentication
- No hardcoded credentials
- Real trading session management