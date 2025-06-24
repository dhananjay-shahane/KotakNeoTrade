#!/usr/bin/env python3
"""
Import CSV data to admin_trade_signals table
"""
import csv
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL not found in environment variables")
    sys.exit(1)

def clean_numeric_value(value):
    """Clean numeric values from CSV"""
    if not value or value == '#N/A' or value == '':
        return None
    
    # Remove currency symbols and commas
    cleaned = str(value).replace('₹', '').replace(',', '').replace('"', '').strip()
    
    # Handle percentage values
    if cleaned.endswith('%'):
        try:
            return float(cleaned[:-1])
        except ValueError:
            return None
    
    try:
        return float(cleaned)
    except ValueError:
        return None

def clean_text_value(value):
    """Clean text values from CSV"""
    if not value or value == '#N/A':
        return None
    return str(value).strip()

def parse_date(date_str):
    """Parse date string to standard format"""
    if not date_str or date_str == '#N/A':
        return None
    
    try:
        # Try parsing DD-MMM-YYYY format
        date_obj = datetime.strptime(date_str, '%d-%b-%Y')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        try:
            # Try parsing DD-MM-YYYY format
            date_obj = datetime.strptime(date_str, '%d-%m-%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return date_str

def import_csv_to_database():
    """Import CSV data to admin_trade_signals table"""
    
    # Read CSV file
    csv_file = 'attached_assets/sheet_1750748101773.csv'
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file {csv_file} not found")
        return False
    
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        # Clear existing data
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM admin_trade_signals"))
            conn.commit()
            print("Cleared existing data from admin_trade_signals table")
        
        # Read CSV file
        df = pd.read_csv(csv_file)
        print(f"Read {len(df)} rows from CSV file")
        
        # Insert data row by row
        inserted_count = 0
        with engine.connect() as conn:
            for index, row in df.iterrows():
                try:
                    # Extract and clean data
                    etf = clean_text_value(row.get('ETF'))
                    if not etf:  # Skip rows without ETF symbol
                        continue
                    
                    # Map CSV columns to database columns
                    data = {
                        'etf': etf,
                        'thirty': clean_text_value(row.get('30')),
                        'dh': clean_text_value(row.get('DH')),
                        'date': parse_date(clean_text_value(row.get('Date'))),
                        'pos': clean_numeric_value(row.get('Pos')),
                        'qty': clean_numeric_value(row.get('Qty')),
                        'ep': clean_numeric_value(row.get('EP')),
                        'cmp': clean_numeric_value(row.get('CMP')),
                        'chan': clean_text_value(row.get('%Chan')),
                        'inv': clean_numeric_value(row.get('Inv.')),
                        'tp': clean_numeric_value(row.get('TP')),
                        'tva': clean_numeric_value(row.get('TVA')),
                        'tpr': clean_text_value(row.get('TPR')),
                        'pl': clean_numeric_value(row.get('PL')),
                        'ed': clean_text_value(row.get('ED')),
                        'exp': clean_text_value(row.get('EXP')),
                        'pr': clean_numeric_value(row.get('PR')),
                        'pp': clean_numeric_value(row.get('PP')),
                        'iv': clean_numeric_value(row.get('IV')),
                        'ip': clean_numeric_value(row.get('IP')),
                        'nt': clean_numeric_value(row.get('NT')),
                        'qt': clean_numeric_value(row.get('Qt')),
                        'seven': clean_text_value(row.get('7')),
                        'ch': clean_text_value(row.get('%Ch'))
                    }
                    
                    # Create insert query
                    insert_query = text("""
                        INSERT INTO admin_trade_signals 
                        (etf, thirty, dh, date, pos, qty, ep, cmp, chan, inv, tp, tva, tpr, pl, ed, exp, pr, pp, iv, ip, nt, qt, seven, ch, created_at)
                        VALUES 
                        (:etf, :thirty, :dh, :date, :pos, :qty, :ep, :cmp, :chan, :inv, :tp, :tva, :tpr, :pl, :ed, :exp, :pr, :pp, :iv, :ip, :nt, :qt, :seven, :ch, NOW())
                    """)
                    
                    # Execute insert
                    conn.execute(insert_query, data)
                    inserted_count += 1
                    
                except Exception as row_error:
                    print(f"Error inserting row {index}: {row_error}")
                    continue
            
            # Commit all changes
            conn.commit()
            print(f"Successfully inserted {inserted_count} rows into admin_trade_signals table")
        
        return True
        
    except Exception as e:
        print(f"Error importing CSV data: {e}")
        return False

if __name__ == "__main__":
    print("Starting CSV import to admin_trade_signals table...")
    success = import_csv_to_database()
    
    if success:
        print("CSV import completed successfully!")
    else:
        print("CSV import failed!")
        sys.exit(1)