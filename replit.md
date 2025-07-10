# Kotak Neo Trading Platform

## Overview
A comprehensive trading platform integrated with Kotak Neo API for real-time portfolio management, trading operations, and market data analysis.

## Project Architecture
- **Backend**: Flask application with SQLAlchemy and PostgreSQL database
- **API Integration**: Kotak Neo API for authentic trading data
- **Frontend**: HTML/CSS/JavaScript with Bootstrap
- **Data Sources**: Only real trading data from Kotak Neo API - no mock or sample data

## User Preferences
- **Data Policy**: Absolutely no sample, demo, mock, or placeholder data allowed
- **Authentication**: Real trading account authentication only
- **Data Sources**: All data must come from live Kotak Neo API

## Recent Changes
- **2025-01-10**: Successfully completed migration from Replit Agent to standard Replit environment
- **2025-01-10**: Completely removed all Yahoo Finance, Google Finance, and Supabase integrations
- **2025-01-10**: Cleaned up frontend JavaScript to remove external data source selectors
- **2025-01-10**: Simplified architecture to use only Kotak Neo API for all market data
- **2025-01-10**: Project now runs cleanly with PostgreSQL database only
- **2025-01-10**: Added new Basic Trade Signals feature by copying ETF signals functionality
- **2025-01-10**: Created Basic Trade Signals page, JavaScript handler, and API endpoint
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