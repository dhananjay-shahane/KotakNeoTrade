"""
Deals API for user deals functionality using real data
"""

from flask import jsonify, request
import json
from datetime import datetime

def get_deals_data():
    """Get real user deals data from external database"""
    try:
        # Import user deals service for real data
        from scripts.user_deals_service import UserDealsService
        
        # Initialize user deals service
        deals_service = UserDealsService()
        
        # Get real user deals data with CMP from symbols schema
        deals_data = deals_service.get_user_deals_with_cmp()
        
        if deals_data:
            # Calculate summary statistics
            total_investment = sum(float(deal.get('investment', 0)) for deal in deals_data if deal.get('investment'))
            current_value = sum(float(deal.get('current_value', 0)) for deal in deals_data if deal.get('current_value'))
            total_pnl = current_value - total_investment
            total_pnl_percent = (total_pnl / total_investment * 100) if total_investment > 0 else 0
            profitable_deals = len([deal for deal in deals_data if float(deal.get('pnl', 0)) > 0])
            
            summary = {
                "total_investment": f"{total_investment:.2f}",
                "current_value": f"{current_value:.2f}",
                "total_pnl": f"{total_pnl:+.2f}",
                "total_pnl_percent": f"{total_pnl_percent:+.2f}%",
                "active_deals": len(deals_data),
                "profitable_deals": profitable_deals
            }
            
            return jsonify({
                "status": "success",
                "data": deals_data,
                "total": len(deals_data),
                "summary": summary
            })
        else:
            return jsonify({
                "status": "success",
                "data": [],
                "total": 0,
                "message": "No user deals data available",
                "summary": {
                    "total_investment": "0.00",
                    "current_value": "0.00", 
                    "total_pnl": "0.00",
                    "total_pnl_percent": "0.00%",
                    "active_deals": 0,
                    "profitable_deals": 0
                }
            })
    
    except Exception as e:
        print(f"Error getting user deals data: {e}")
        return jsonify({
            "status": "error",
            "message": f"Database connection error: {str(e)}",
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