#!/usr/bin/env python3
import pandas as pd
from sqlalchemy import create_engine, text

import os
import sys
sys.path.append('.')
from config.database_config import get_database_url
EXTERNAL_DB_URL = get_database_url()

def clean_numeric(value):
    if pd.isna(value) or value == '#N/A' or value == '': return None
    cleaned = str(value).replace('₹', '').replace(',', '').replace('"', '').strip()
    if cleaned.endswith('%'):
        try: return float(cleaned[:-1])
        except: return None
    try: return float(cleaned)
    except: return None

def clean_text(value):
    if pd.isna(value) or value == '#N/A': return None
    return str(value).strip()

engine = create_engine(EXTERNAL_DB_URL)

with engine.connect() as conn:
    # Get admin user
    result = conn.execute(text("SELECT id FROM users WHERE ucc = 'ADMIN' LIMIT 1"))
    admin_user = result.fetchone()
    if not admin_user:
        conn.execute(text("INSERT INTO users (ucc, mobile_number, greeting_name, is_active) VALUES ('ADMIN', '9999999999', 'Admin User', true)"))
        result = conn.execute(text("SELECT id FROM users WHERE ucc = 'ADMIN' LIMIT 1"))
        admin_user = result.fetchone()
    admin_user_id = admin_user[0]
    
    # Clear and import
    conn.execute(text("DELETE FROM admin_trade_signals"))
    df = pd.read_csv('attached_assets/sheet_1750748101773.csv')
    
    count = 0
    for _, row in df.iterrows():
        etf = clean_text(row.get('ETF'))
        if not etf: continue
        
        conn.execute(text("""
            INSERT INTO admin_trade_signals 
            (admin_user_id, target_user_id, symbol, signal_type, etf, thirty, dh, date, pos, qty, ep, cmp, chan, inv, tp, tva, tpr, pl, ed, exp, pr, pp, iv, ip, nt, qt, seven, ch, created_at)
            VALUES 
            (:admin_user_id, :target_user_id, :symbol, :signal_type, :etf, :thirty, :dh, :date, :pos, :qty, :ep, :cmp, :chan, :inv, :tp, :tva, :tpr, :pl, :ed, :exp, :pr, :pp, :iv, :ip, :nt, :qt, :seven, :ch, NOW())
        """), {
            'admin_user_id': admin_user_id,
            'target_user_id': admin_user_id,
            'symbol': etf,
            'signal_type': 'BUY' if clean_numeric(row.get('Pos')) == 1 else 'SELL',
            'etf': etf,
            'thirty': clean_text(row.get('30')),
            'dh': clean_text(row.get('DH')),
            'date': clean_text(row.get('Date')),
            'pos': clean_numeric(row.get('Pos')),
            'qty': clean_numeric(row.get('Qty')),
            'ep': clean_numeric(row.get('EP')),
            'cmp': clean_numeric(row.get('CMP')),
            'chan': clean_text(row.get('%Chan')),
            'inv': clean_numeric(row.get('Inv.')),
            'tp': clean_numeric(row.get('TP')),
            'tva': clean_numeric(row.get('TVA')),
            'tpr': clean_text(row.get('TPR')),
            'pl': clean_numeric(row.get('PL')),
            'ed': clean_text(row.get('ED')),
            'exp': clean_text(row.get('EXP')),
            'pr': clean_text(row.get('PR')),
            'pp': clean_text(row.get('PP')),
            'iv': clean_text(row.get('IV')),
            'ip': clean_text(row.get('IP')),
            'nt': clean_numeric(row.get('NT')),
            'qt': clean_numeric(row.get('Qt')),
            'seven': clean_text(row.get('7')),
            'ch': clean_text(row.get('%Ch'))
        })
        count += 1
    
    conn.commit()
    
    # Verify
    result = conn.execute(text("SELECT COUNT(*) FROM admin_trade_signals WHERE etf IS NOT NULL"))
    total = result.fetchone()[0]
    print(f"Imported {count} records, total: {total}")