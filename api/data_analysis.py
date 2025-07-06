"""
Data Analysis API - Endpoint to analyze trading data
"""
from flask import Blueprint, jsonify, session, render_template, redirect, url_for
import logging
from Scripts.data_analyzer import DataAnalyzer
from utils.auth import validate_current_session

# Create blueprint
data_analysis_bp = Blueprint('data_analysis', __name__)

@data_analysis_bp.route('/data-analysis', methods=['GET'])
def data_analysis_page():
    """
    Data analysis page - shows interface for analyzing trading data
    """
    if not validate_current_session():
        return redirect(url_for('auth.login'))
    
    return render_template('data_analysis.html')

@data_analysis_bp.route('/api/analyze-data', methods=['GET'])
def analyze_trading_data():
    """
    API endpoint to analyze all trading data
    Returns comprehensive analysis of data structure and content
    """
    if not validate_current_session():
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'No active client'}), 400
        
        # Create data analyzer
        analyzer = DataAnalyzer()
        
        # Analyze all data
        analysis = analyzer.analyze_all_data(client)
        
        # Save report to file
        analyzer.save_analysis_report(analysis, 'data_analysis_report.json')
        
        # Print summary to console
        analyzer.print_summary_report(analysis)
        
        return jsonify({
            'status': 'success',
            'message': 'Data analysis completed successfully',
            'analysis': analysis,
            'report_file': 'data_analysis_report.json'
        })
        
    except Exception as e:
        logging.error(f"Data analysis error: {str(e)}")
        return jsonify({'error': f'Data analysis failed: {str(e)}'}), 500

@data_analysis_bp.route('/api/analyze-specific/<data_type>', methods=['GET'])
def analyze_specific_data(data_type):
    """
    API endpoint to analyze specific data type
    data_type can be: dashboard, positions, holdings, orders, limits
    """
    if not validate_current_session():
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        client = session.get('client')
        if not client:
            return jsonify({'error': 'No active client'}), 400
        
        analyzer = DataAnalyzer()
        
        # Analyze specific data type
        if data_type == 'dashboard':
            analysis = analyzer.analyze_dashboard_data(client)
        elif data_type == 'positions':
            analysis = analyzer.analyze_positions_data(client)
        elif data_type == 'holdings':
            analysis = analyzer.analyze_holdings_data(client)
        elif data_type == 'orders':
            analysis = analyzer.analyze_orders_data(client)
        elif data_type == 'limits':
            analysis = analyzer.analyze_limits_data(client)
        else:
            return jsonify({'error': f'Invalid data type: {data_type}'}), 400
        
        return jsonify({
            'status': 'success',
            'data_type': data_type,
            'analysis': analysis
        })
        
    except Exception as e:
        logging.error(f"Specific data analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500