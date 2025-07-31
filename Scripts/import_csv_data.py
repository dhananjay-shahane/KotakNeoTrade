#!/usr/bin/env python3
"""
Import real ETF trading data from CSV into external PostgreSQL database
"""

import pandas as pd
import psycopg2
from datetime import datetime, date
import os
from dotenv import load_dotenv

load_dotenv()

def clean_numeric_value(value):
    """Clean and convert numeric values from CSV"""
    if pd.isna(value) or value == '' or value == '#N/A':
        return None
    
    # Remove commas and currency symbols
    if isinstance(value, str):
        value = value.replace(',', '').replace('₹', '').replace('%', '')
        if value == '' or value == '#N/A':
            return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def parse_date(date_str):
    """Parse date from CSV format"""
    if pd.isna(date_str) or date_str == '' or date_str == '#N/A':
        return None
    
    try:
        # Parse format like "22-Nov-2024"
        return datetime.strptime(str(date_str), "%d-%b-%Y").date()
    except:
        return None

def import_csv_to_database():
    """Import CSV data into admin_trade_signals table"""
    
    # Database connection using centralized config
    import sys
    sys.path.append('.')
    from config.database_config import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Read CSV file, skip first 2 rows (headers)
    csv_file = 'attached_assets/INVESTMENTS - ETFS-V2_1750508406649.csv'
    df = pd.read_csv(csv_file, skiprows=2)
    
    # Clean and process data
    records_imported = 0
    
    for index, row in df.iterrows():
        try:
            # Check if ETF column exists and has valid data
            if 'ETF' not in row or pd.isna(row['ETF']):
                continue
                
            etf_symbol = str(row['ETF']).strip()
            if etf_symbol in ['', 'nan', 'ETF', '#N/A']:
                continue
            
            print(f"Processing ETF: {etf_symbol}")
            
            # Extract data from CSV columns
            signal_date = parse_date(row['Date'])
            position = row['Pos'] if not pd.isna(row['Pos']) else 1
            quantity = clean_numeric_value(row['Qty'])
            entry_price = clean_numeric_value(row['EP'])
            current_price = clean_numeric_value(row['CMP'])
            change_percent = clean_numeric_value(row['%Chan'])
            investment_amount = clean_numeric_value(row['Inv.'])
            target_price = clean_numeric_value(row['TP'])
            current_value = clean_numeric_value(row['TVA'])
            pnl = clean_numeric_value(row['PL'])
            
            # Skip if essential data is missing
            if not etf_symbol or not quantity or not entry_price:
                continue
            
            # Calculate PnL percentage if not available
            pnl_percentage = None
            if pnl and investment_amount and investment_amount > 0:
                pnl_percentage = (pnl / investment_amount) * 100
            elif change_percent:
                pnl_percentage = change_percent
            
            # Determine signal type based on position
            signal_type = 'BUY' if position == 1 else 'SELL'
            
            # Insert into database
            insert_query = """
                INSERT INTO admin_trade_signals (
                    admin_user_id, target_user_id, symbol, signal_type, 
                    entry_price, target_price, quantity, signal_title,
                    signal_description, status, created_at, updated_at,
                    signal_date, current_price, change_percent,
                    investment_amount, current_value, pnl, pnl_percentage
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cursor.execute(insert_query, (
                1,  # admin_user_id
                1,  # target_user_id
                etf_symbol,
                signal_type,
                entry_price,
                target_price,
                int(quantity) if quantity else 0,
                f"ETF Signal - {etf_symbol}",
                f"Real trading signal for {etf_symbol} with entry at ₹{entry_price}",
                'ACTIVE',
                datetime.now(),
                datetime.now(),
                signal_date or datetime.now().date(),
                current_price,
                change_percent,
                investment_amount,
                current_value,
                pnl,
                pnl_percentage
            ))
            
            records_imported += 1
            
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            continue
    
    # Commit changes
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Successfully imported {records_imported} ETF trading records")
    return records_imported

if __name__ == "__main__":
    import_csv_to_database()