"""
Trading Signals API for ETF signals functionality using real data
"""

from flask import jsonify, request
import json
from datetime import datetime

def get_etf_signals_data():
    """API endpoint for ETF signals data - only real data from external database"""
    try:
        # Import external database service for real data
        from scripts.external_db_service import ExternalDBService

        # Initialize database service
        db_service = ExternalDBService()

        # Get real trading signals data
        signals_data = db_service.get_admin_trade_signals()

        if signals_data:
            return jsonify({
                "status": "success",
                "data": signals_data,
                "total": len(signals_data)
            })
        else:
            return jsonify({
                "status": "success", 
                "data": [],
                "total": 0,
                "message": "No trading signals data available"
            })

    except Exception as e:
        print(f"Error getting ETF signals data: {e}")
        return jsonify({
            "status": "error",
            "message": f"Database connection error: {str(e)}",
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