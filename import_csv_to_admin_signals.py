#!/usr/bin/env python3
"""
Import CSV data to admin_trade_signals table
"""
import csv
import sys
from datetime import datetime
from app import app, db
from models_etf import AdminTradeSignal

def parse_csv_and_import(csv_file_path):
    """Parse CSV file and import data to admin_trade_signals table"""
    
    with app.app_context():
        try:
            # Clear existing data for user ZHZ3J (ID=1)
            print("Clearing existing admin trade signals for user ZHZ3J...")
            AdminTradeSignal.query.filter_by(target_user_id=1).delete()
            db.session.commit()
            
            imported_count = 0
            
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Skip first two header rows and find the actual header
                lines = file.readlines()
                
                # Find the header row (contains ETF,30,DH,Date...)
                header_line_idx = None
                for i, line in enumerate(lines):
                    if line.strip().startswith('ETF,30,DH,Date'):
                        header_line_idx = i
                        break
                
                if header_line_idx is None:
                    print("Could not find header row in CSV")
                    return
                
                # Parse the header to get column indices
                header = lines[header_line_idx].strip().split(',')
                print(f"Found header: {header[:10]}...")  # Show first 10 columns
                
                # Process data rows
                for line_idx in range(header_line_idx + 1, len(lines)):
                    line = lines[line_idx].strip()
                    if not line or line.startswith(','):
                        continue
                    
                    try:
                        data = line.split(',')
                        if len(data) < 10:  # Skip incomplete rows
                            continue
                        
                        # Extract data from CSV columns
                        etf_symbol = data[0].strip() if data[0] else None
                        if not etf_symbol or etf_symbol in ['', '#N/A']:
                            continue
                        
                        # Parse date (format: 22-Nov-2024)
                        date_str = data[3].strip() if len(data) > 3 else ''
                        try:
                            if date_str and date_str != '#N/A':
                                signal_date = datetime.strptime(date_str, '%d-%b-%Y')
                            else:
                                signal_date = datetime.now()
                        except:
                            signal_date = datetime.now()
                        
                        # Parse position (1 = active, 0 = closed)
                        pos = data[4].strip() if len(data) > 4 else '1'
                        status = 'ACTIVE' if pos == '1' else 'CLOSED'
                        
                        # Parse quantity
                        try:
                            quantity = int(float(data[5])) if len(data) > 5 and data[5].strip() else 100
                        except:
                            quantity = 100
                        
                        # Parse entry price
                        try:
                            entry_price = float(data[6]) if len(data) > 6 and data[6].strip() else 100.0
                        except:
                            entry_price = 100.0
                        
                        # Parse current price (CMP)
                        try:
                            current_price = float(data[7]) if len(data) > 7 and data[7].strip() else entry_price
                        except:
                            current_price = entry_price
                        
                        # Parse percentage change
                        try:
                            change_str = data[8].strip() if len(data) > 8 else '0%'
                            if change_str and change_str != '#N/A':
                                change_percent = float(change_str.replace('%', ''))
                            else:
                                change_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                        except:
                            change_percent = 0
                        
                        # Parse investment amount
                        try:
                            inv_str = data[9].strip().replace(',', '') if len(data) > 9 else ''
                            investment_amount = float(inv_str) if inv_str and inv_str != '#N/A' else entry_price * quantity
                        except:
                            investment_amount = entry_price * quantity
                        
                        # Parse target price
                        try:
                            target_price = float(data[10]) if len(data) > 10 and data[10].strip() and data[10].strip() != '#N/A' else entry_price * 1.1
                        except:
                            target_price = entry_price * 1.1
                        
                        # Calculate current value and PnL
                        current_value = current_price * quantity
                        pnl = current_value - investment_amount
                        pnl_percentage = (pnl / investment_amount * 100) if investment_amount > 0 else 0
                        
                        # Create admin trade signal
                        signal = AdminTradeSignal(
                            admin_user_id=1,  # Admin user
                            target_user_id=1,  # ZHZ3J user
                            symbol=etf_symbol,
                            trading_symbol=etf_symbol,
                            token=str(26000 + imported_count),  # Generate token
                            exchange='NSE',
                            signal_type='BUY',
                            entry_price=entry_price,
                            target_price=target_price,
                            stop_loss=entry_price * 0.95,  # 5% stop loss
                            quantity=quantity,
                            signal_title=f'{etf_symbol} Position',
                            signal_description=f'ETF position imported from CSV data',
                            priority='MEDIUM',
                            status=status,
                            created_at=signal_date,
                            updated_at=datetime.now(),
                            current_price=current_price,
                            change_percent=change_percent,
                            investment_amount=investment_amount,
                            current_value=current_value,
                            pnl=pnl,
                            pnl_percentage=pnl_percentage
                        )
                        
                        db.session.add(signal)
                        imported_count += 1
                        
                        if imported_count % 10 == 0:
                            print(f"Imported {imported_count} signals...")
                            
                    except Exception as e:
                        print(f"Error processing line {line_idx}: {str(e)}")
                        continue
                
                # Commit all changes
                db.session.commit()
                print(f"\nSuccessfully imported {imported_count} admin trade signals for user ZHZ3J")
                
                # Show summary
                total_investment = sum([s.investment_amount for s in AdminTradeSignal.query.filter_by(target_user_id=1).all()])
                total_current_value = sum([s.current_value for s in AdminTradeSignal.query.filter_by(target_user_id=1).all()])
                total_pnl = total_current_value - total_investment
                
                print(f"Portfolio Summary:")
                print(f"Total Signals: {imported_count}")
                print(f"Total Investment: ₹{total_investment:,.2f}")
                print(f"Current Value: ₹{total_current_value:,.2f}")
                print(f"Total P&L: ₹{total_pnl:,.2f} ({total_pnl/total_investment*100:.2f}%)")
                
        except Exception as e:
            print(f"Error importing CSV data: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    csv_file = "attached_assets/INVESTMENTS - ETFS-V2_1750486227969.csv"
    parse_csv_and_import(csv_file)