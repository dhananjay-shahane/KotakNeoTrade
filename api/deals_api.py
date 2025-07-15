"""
Deals API for user deals functionality
"""

from flask import jsonify, request
import json
from datetime import datetime

def get_deals_data():
    """Get deals data for the datatable"""
    try:
        # Sample deals data structure
        sample_deals = [
            {
                "deal_id": 1,
                "symbol": "GOLDBEES",
                "quantity": 100,
                "entry_price": "44.50",
                "current_price": "45.20",
                "investment": "4450.00",
                "current_value": "4520.00",
                "pnl": "+70.00",
                "pnl_percent": "+1.57%",
                "entry_date": "2025-01-10",
                "status": "Active",
                "target_price": "48.00",
                "stop_loss": "42.00",
                "days_held": 5
            },
            {
                "deal_id": 2,
                "symbol": "NIFTYBEES",
                "quantity": 50,
                "entry_price": "209.00",
                "current_price": "210.50",
                "investment": "10450.00",
                "current_value": "10525.00",
                "pnl": "+75.00",
                "pnl_percent": "+0.72%",
                "entry_date": "2025-01-12",
                "status": "Active",
                "target_price": "215.00",
                "stop_loss": "200.00",
                "days_held": 3
            },
            {
                "deal_id": 3,
                "symbol": "BANKBEES",
                "quantity": 25,
                "entry_price": "422.00",
                "current_price": "425.80",
                "investment": "10550.00",
                "current_value": "10645.00",
                "pnl": "+95.00",
                "pnl_percent": "+0.90%",
                "entry_date": "2025-01-08",
                "status": "Active",
                "target_price": "435.00",
                "stop_loss": "410.00",
                "days_held": 7
            },
            {
                "deal_id": 4,
                "symbol": "LIQUIDBEES",
                "quantity": 200,
                "entry_price": "100.25",
                "current_price": "99.80",
                "investment": "20050.00",
                "current_value": "19960.00",
                "pnl": "-90.00",
                "pnl_percent": "-0.45%",
                "entry_date": "2025-01-05",
                "status": "Active",
                "target_price": "101.50",
                "stop_loss": "98.00",
                "days_held": 10
            }
        ]
        
        return jsonify({
            "status": "success",
            "data": sample_deals,
            "total": len(sample_deals),
            "summary": {
                "total_investment": "45500.00",
                "current_value": "45650.00",
                "total_pnl": "+150.00",
                "total_pnl_percent": "+0.33%",
                "active_deals": 4,
                "profitable_deals": 3
            }
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": []
        }), 500

def update_deal():
    """Update deal information"""
    try:
        deal_data = request.get_json()
        deal_id = deal_data.get("deal_id")
        
        # Sample update logic
        updated_deal = {
            "deal_id": deal_id,
            "status": "updated",
            "timestamp": datetime.now().isoformat(),
            "message": f"Deal {deal_id} updated successfully"
        }
        
        return jsonify({
            "status": "success",
            "message": "Deal updated successfully",
            "deal": updated_deal
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def close_deal():
    """Close a deal"""
    try:
        deal_data = request.get_json()
        deal_id = deal_data.get("deal_id")
        
        # Sample close logic
        closed_deal = {
            "deal_id": deal_id,
            "status": "closed",
            "close_timestamp": datetime.now().isoformat(),
            "message": f"Deal {deal_id} closed successfully"
        }
        
        return jsonify({
            "status": "success",
            "message": "Deal closed successfully",
            "deal": closed_deal
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500