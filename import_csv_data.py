#!/usr/bin/env python3
"""
Import CSV data to external PostgreSQL database admin_trade_signals table
"""
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from decimal import Decimal
import re

# External database connection
EXTERNAL_DB_URL = "postgresql://kotak_trading_db_user:JRUlk8RutdgVcErSiUXqljDUdK8sBsYO@dpg-d1cjd66r433s73fsp4n0-a.oregon-postgres.render.com/kotak_trading_db"

def clean_numeric_value(value):
    """Clean and convert numeric values from CSV"""
    if pd.isna(value) or value in ['#N/A', '', 'N/A']:
        return None
    
    if isinstance(value, str):
        # Remove currency symbols, commas, quotes
        value = re.sub(r'[₹,"\'%]', '', value)
        # Handle negative values in parentheses
        if value.strip().startswith('(') and value.strip().endswith(')'):
            value = '-' + value.strip()[1:-1]
        value = value.strip()
        
        if value == '' or value == '#N/A':
            return None
            
        try:
            return float(value)
        except ValueError:
            return None
    
    return float(value) if value is not None else None

def parse_date(date_str):
    """Parse date string from CSV"""
    if pd.isna(date_str) or date_str in ['#N/A', '', 'N/A']:
        return None
    
    try:
        # Handle DD-MMM-YYYY format like "22-Nov-2024"
        from datetime import datetime
        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%d-%b-%Y').date()
    except:
        return None
    
    return None

def import_csv_to_database():
    """Import CSV data to external database"""
    try:
        print("Loading CSV data...")
        
        # Read CSV file
        df = pd.read_csv('attached_assets/sheet_1750741257789.csv')
        print(f"Loaded {len(df)} rows from CSV")
        
        # Connect to external database
        external_engine = create_engine(EXTERNAL_DB_URL)
        
        with external_engine.connect() as conn:
            # Drop and recreate table to match CSV structure
            print("Creating admin_trade_signals table with CSV structure...")
            
            conn.execute(text("DROP TABLE IF EXISTS admin_trade_signals"))
            conn.execute(text("""
                CREATE TABLE admin_trade_signals (
                    id SERIAL PRIMARY KEY,
                    etf VARCHAR(50),
                    thirty VARCHAR(20),
                    dh VARCHAR(20),
                    date DATE,
                    pos INTEGER,
                    qty INTEGER,
                    ep DECIMAL(10,2),
                    cmp DECIMAL(10,2),
                    chan VARCHAR(20),
                    inv DECIMAL(15,2),
                    tp DECIMAL(10,2),
                    tva DECIMAL(15,2),
                    tpr VARCHAR(50),
                    pl DECIMAL(15,2),
                    ed DATE,
                    exp DATE,
                    pr DECIMAL(15,2),
                    pp VARCHAR(20),
                    iv DECIMAL(15,2),
                    ip DECIMAL(10,2),
                    nt INTEGER,
                    qt DECIMAL(10,2),
                    seven VARCHAR(20),
                    ch VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            
            # Import data row by row
            imported_count = 0
            for index, row in df.iterrows():
                try:
                    # Parse and clean data
                    etf = str(row['ETF']) if pd.notna(row['ETF']) else None
                    thirty = str(row['30']) if pd.notna(row['30']) else None
                    dh = str(row['DH']) if pd.notna(row['DH']) else None
                    date_val = parse_date(row['Date'])
                    pos = int(clean_numeric_value(row['Pos'])) if clean_numeric_value(row['Pos']) is not None else None
                    qty = int(clean_numeric_value(row['Qty'])) if clean_numeric_value(row['Qty']) is not None else None
                    ep = clean_numeric_value(row['EP'])
                    cmp = clean_numeric_value(row['CMP'])
                    chan = str(row['%Chan']) if pd.notna(row['%Chan']) else None
                    inv = clean_numeric_value(row['Inv.'])
                    tp = clean_numeric_value(row['TP'])
                    tva = clean_numeric_value(row['TVA'])
                    tpr = str(row['TPR']) if pd.notna(row['TPR']) else None
                    pl = clean_numeric_value(row['PL'])
                    ed = parse_date(row['ED']) if 'ED' in row and pd.notna(row['ED']) else None
                    exp = parse_date(row['EXP']) if 'EXP' in row and pd.notna(row['EXP']) else None
                    pr = clean_numeric_value(row['PR']) if 'PR' in row else None
                    pp = str(row['PP']) if 'PP' in row and pd.notna(row['PP']) else None
                    iv = clean_numeric_value(row['IV']) if 'IV' in row else None
                    ip = clean_numeric_value(row['IP']) if 'IP' in row else None
                    nt = int(clean_numeric_value(row['NT'])) if 'NT' in row and clean_numeric_value(row['NT']) is not None else None
                    qt = clean_numeric_value(row['Qt']) if 'Qt' in row else None
                    seven = str(row['7']) if '7' in row and pd.notna(row['7']) else None
                    ch = str(row['%Ch']) if '%Ch' in row and pd.notna(row['%Ch']) else None
                    
                    # Skip rows with no ETF symbol
                    if not etf or etf == 'nan':
                        continue
                    
                    # Insert into database
                    conn.execute(text("""
                        INSERT INTO admin_trade_signals 
                        (etf, thirty, dh, date, pos, qty, ep, cmp, chan, inv, tp, tva, tpr, pl, ed, exp, pr, pp, iv, ip, nt, qt, seven, ch)
                        VALUES (:etf, :thirty, :dh, :date, :pos, :qty, :ep, :cmp, :chan, :inv, :tp, :tva, :tpr, :pl, :ed, :exp, :pr, :pp, :iv, :ip, :nt, :qt, :seven, :ch)
                    """), {
                        'etf': etf, 'thirty': thirty, 'dh': dh, 'date': date_val, 'pos': pos, 'qty': qty,
                        'ep': ep, 'cmp': cmp, 'chan': chan, 'inv': inv, 'tp': tp, 'tva': tva, 'tpr': tpr,
                        'pl': pl, 'ed': ed, 'exp': exp, 'pr': pr, 'pp': pp, 'iv': iv, 'ip': ip, 'nt': nt,
                        'qt': qt, 'seven': seven, 'ch': ch
                    })
                    imported_count += 1
                    
                except Exception as e:
                    print(f"Error importing row {index}: {e}")
                    continue
            
            conn.commit()
            
            # Verify import
            result = conn.execute(text("SELECT COUNT(*) FROM admin_trade_signals"))
            total_count = result.fetchone()[0]
            print(f"Successfully imported {imported_count} records to external database")
            print(f"Total records in database: {total_count}")
            
            # Show sample data
            sample_result = conn.execute(text("""
                SELECT etf, ep, cmp, qty, pos, date 
                FROM admin_trade_signals 
                WHERE etf IS NOT NULL 
                ORDER BY date DESC LIMIT 10
            """))
            
            print("\nSample imported data:")
            for row in sample_result.fetchall():
                etf, ep, cmp, qty, pos, date = row
                print(f"  {etf}: ₹{ep} → ₹{cmp} ({qty} qty, pos: {pos}) - {date}")
        
        return True
        
    except Exception as e:
        print(f"Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import_csv_to_database()