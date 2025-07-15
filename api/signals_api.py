"""
Trading Signals API for ETF signals functionality
"""

from flask import jsonify, request
import json
from datetime import datetime

def get_etf_signals_data():
    """Get ETF signals data for the datatable"""
    try:
        # Sample trading signals data structure
        sample_signals = [
            {
                "trade_signal_id": 1,
                "symbol": "GOLDBEES",
                "seven": "45.20",
                "ch": "+2.3%",
                "thirty": "44.80",
                "dh": "+3.1%",
                "date": "2025-01-10",
                "qty": 100,
                "ep": "44.50",
                "cmp": "45.20",
                "changePct": "+1.57%",
                "inv": "4450.00",
                "tp": "48.00",
                "tpr": "+7.87%",
                "tva": "4800.00",
                "cpl": "+70.00",
                "ed": "2025-01-10",
                "exp": "2025-02-10",
                "pr": "43.00-47.00",
                "pp": "8.5",
                "iv": "15.2%",
                "ip": "+0.8%"
            },
            {
                "trade_signal_id": 2,
                "symbol": "NIFTYBEES",
                "seven": "210.50",
                "ch": "+1.8%",
                "thirty": "208.30",
                "dh": "+2.5%",
                "date": "2025-01-12",
                "qty": 50,
                "ep": "209.00",
                "cmp": "210.50",
                "changePct": "+0.72%",
                "inv": "10450.00",
                "tp": "215.00",
                "tpr": "+2.87%",
                "tva": "10750.00",
                "cpl": "+75.00",
                "ed": "2025-01-12",
                "exp": "2025-02-12",
                "pr": "205.00-220.00",
                "pp": "7.2",
                "iv": "12.8%",
                "ip": "+0.5%"
            },
            {
                "trade_signal_id": 3,
                "symbol": "BANKBEES",
                "seven": "425.80",
                "ch": "-0.5%",
                "thirty": "420.50",
                "dh": "+1.2%",
                "date": "2025-01-08",
                "qty": 25,
                "ep": "422.00",
                "cmp": "425.80",
                "changePct": "+0.90%",
                "inv": "10550.00",
                "tp": "435.00",
                "tpr": "+3.08%",
                "tva": "10875.00",
                "cpl": "+95.00",
                "ed": "2025-01-08",
                "exp": "2025-02-08",
                "pr": "415.00-440.00",
                "pp": "6.8",
                "iv": "18.5%",
                "ip": "-0.2%"
            }
        ]
        
        return jsonify({
            "status": "success",
            "data": sample_signals,
            "total": len(sample_signals)
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": []
        }), 500

def create_deal_from_signal():
    """Create a deal from trading signal"""
    try:
        signal_data = request.get_json()
        
        # Sample deal creation logic
        deal = {
            "deal_id": signal_data.get("trade_signal_id", 1),
            "symbol": signal_data.get("symbol", ""),
            "quantity": signal_data.get("qty", 0),
            "entry_price": signal_data.get("ep", 0),
            "current_price": signal_data.get("cmp", 0),
            "status": "created",
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify({
            "status": "success",
            "message": "Deal created successfully",
            "deal": deal
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500