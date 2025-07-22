import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import pandas as pd
import logging
from core.database import get_db_connection
import datetime
from dateutil.relativedelta import relativedelta

# Initialize Dash app
app = dash.Dash(__name__, url_base_pathname='/dash-charts/')
app.title = "Stock Analysis Dashboard - Kotak Neo Trading"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# App layout
app.layout = html.Div([
    html.Div([
        html.Div([
            html.H1("📈 Interactive Charts", className="header-title"),
            html.P("Real-time candlestick charts with historical data", className="header-subtitle")
        ], className="header-left"),
        html.Div([
            dcc.Input(
                id='symbol-input',
                type='text',
                placeholder='Enter symbol (e.g., AUTO, RELIANCE)',
                className='symbol-input',
                value='AUTO'  # Default value
            ),
            html.Button('🔍 Load Chart', id='submit-button', n_clicks=0, className='submit-button'),
        ], className='input-container'),
    ], className="header"),

    html.Div([
        html.Button('1D', id='period-1d', className='period-button', n_clicks=0),
        html.Button('5D', id='period-5d', className='period-button', n_clicks=0),
        html.Button('1M', id='period-1m', className='period-button', n_clicks=0),
        html.Button('6M', id='period-6m', className='period-button', n_clicks=0),
        html.Button('YTD', id='period-ytd', className='period-button', n_clicks=0),
        html.Button('1Y', id='period-1y', className='period-button', n_clicks=0),
        html.Button('5Y', id='period-5y', className='period-button', n_clicks=0),
        html.Button('MAX', id='period-max', className='period-button', n_clicks=0),
    ], className='period-selector'),

    html.Div(id='metrics-container', className='metrics-container'),

    dcc.Loading(
        id="loading-chart",
        type="circle",
        color="#2563eb",
        children=[dcc.Graph(id='candlestick-chart', className='chart')]
    ),

    html.Div(id='status-message', className='status-message'),

    dcc.Store(id='store-cmp-data'),
    dcc.Store(id='selected-period', data='1M')  # Default period
], className='container')

# Custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
        :root {
            --primary-color: #2563eb;
            --positive-color: #16a34a;
            --negative-color: #dc2626;
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --text-secondary: #94a3b8;
            --border-color: #334155;
            --header-bg: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            min-height: 100vh;
        }

        .header {
            background: var(--header-bg);
            color: white;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }

        .header-left {
            display: flex;
            flex-direction: column;
        }

        .header-title {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 8px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .header-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 400;
        }

        .input-container {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .symbol-input {
            padding: 14px 18px;
            font-size: 16px;
            border: 2px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            width: 250px;
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        .symbol-input:focus {
            outline: none;
            border-color: rgba(255, 255, 255, 0.5);
            background-color: rgba(255, 255, 255, 0.15);
        }

        .symbol-input::placeholder {
            color: rgba(255, 255, 255, 0.7);
        }

        .submit-button {
            padding: 14px 24px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
        }

        .submit-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
        }

        .period-selector {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 25px;
            flex-wrap: wrap;
            background-color: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .period-button {
            padding: 12px 20px;
            background-color: rgba(255, 255, 255, 0.05);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s ease;
            min-width: 60px;
        }

        .period-button:hover {
            background-color: rgba(37, 99, 235, 0.2);
            border-color: var(--primary-color);
            transform: translateY(-1px);
        }

        .period-button.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        }

        .metrics-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .metric-card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid var(--border-color);
        }

        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.3);
            border-color: var(--primary-color);
        }

        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            margin: 12px 0;
            color: var(--text-color);
        }

        .metric-label {
            color: var(--text-secondary);
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            font-weight: 500;
        }

        .metric-pct {
            font-weight: 600;
            margin-top: 8px;
            font-size: 1.2rem;
            padding: 6px 12px;
            border-radius: 8px;
            display: inline-block;
        }

        .positive {
            color: var(--positive-color);
            background-color: rgba(22, 163, 74, 0.15);
        }

        .negative {
            color: var(--negative-color);
            background-color: rgba(220, 38, 38, 0.15);
        }

        .chart {
            height: 600px;
            border-radius: 16px;
            background-color: var(--card-bg);
            padding: 20px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-color);
        }

        .status-message {
            text-align: center;
            padding: 15px;
            margin-top: 20px;
            border-radius: 8px;
            background-color: var(--card-bg);
            color: var(--text-secondary);
            font-style: italic;
        }

        ._dash-loading {
            margin: 20px 0;
        }

        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                text-align: center;
            }
            
            .header-title {
                font-size: 1.8rem;
            }
            
            .input-container {
                flex-direction: column;
                width: 100%;
            }
            
            .symbol-input {
                width: 100%;
            }
            
            .period-selector {
                justify-content: center;
            }
        }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Helper functions
def get_db_connector():
    """Get database connection using existing connection function"""
    try:
        conn = get_db_connection()
        if conn:
            return conn
        return None
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

import psycopg2
import psycopg2.extras

def table_exists(conn, table_name):
    """Check if a table exists in the symbols schema"""
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'symbols' 
                    AND table_name = %s
                )
            """, (table_name,))
            result = cursor.fetchone()
            return result['exists'] if result else False
    except Exception as e:
        logger.error(f"Table existence check error: {e}")
        return False

def get_cmp(conn, symbol):
    """Get current market price from 5m table"""
    table_name = f"{symbol.lower()}_5m"
    if not table_exists(conn, table_name):
        logger.warning(f"Table not found: symbols.{table_name}")
        return None
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(f"""
                SELECT close 
                FROM symbols."{table_name}"
                ORDER BY datetime DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            return float(result['close']) if result else None
    except Exception as e:
        logger.error(f"Error fetching CMP for {symbol}: {e}")
        return None

def get_ohlc_data(conn, symbol, period='1M'):
    """Get OHLC data for candlestick chart based on selected period"""
    daily_table = f"{symbol.lower()}_daily"
    intraday_table = f"{symbol.lower()}_5m"
    
    try:
        today = datetime.date.today()
        
        if period == '1D':
            # Intraday data for today
            if not table_exists(conn, intraday_table):
                return pd.DataFrame()
            
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(f"""
                    SELECT datetime, open, high, low, close 
                    FROM symbols."{intraday_table}"
                    WHERE datetime::date = CURRENT_DATE
                    ORDER BY datetime ASC
                """)
                result = cursor.fetchall()
                return pd.DataFrame(result) if result else pd.DataFrame()
        
        else:
            # Daily data for longer periods
            if not table_exists(conn, daily_table):
                return pd.DataFrame()
            
            # Calculate start date based on period
            if period == '5D':
                start_date = today - relativedelta(days=7)  # Get more days to account for weekends
            elif period == '1M':
                start_date = today - relativedelta(months=1)
            elif period == '6M':
                start_date = today - relativedelta(months=6)
            elif period == 'YTD':
                start_date = datetime.date(today.year, 1, 1)
            elif period == '1Y':
                start_date = today - relativedelta(years=1)
            elif period == '5Y':
                start_date = today - relativedelta(years=5)
            else:  # MAX
                start_date = None
            
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                if start_date:
                    cursor.execute(f"""
                        SELECT datetime, open, high, low, close 
                        FROM symbols."{daily_table}"
                        WHERE datetime >= %s
                        ORDER BY datetime ASC
                    """, (start_date,))
                else:
                    cursor.execute(f"""
                        SELECT datetime, open, high, low, close 
                        FROM symbols."{daily_table}"
                        ORDER BY datetime ASC
                    """)
                
                result = cursor.fetchall()
                return pd.DataFrame(result) if result else pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching OHLC data for {symbol}: {e}")
        return pd.DataFrame()

def get_historical_cmp(conn, symbol, offset):
    """Get historical close price N trading days ago"""
    table_name = f"{symbol.lower()}_daily"
    if not table_exists(conn, table_name):
        return None
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(f"""
                SELECT close
                FROM (
                    SELECT datetime, close,
                           ROW_NUMBER() OVER (ORDER BY datetime DESC) as rn
                    FROM symbols."{table_name}"
                ) t
                WHERE rn = %s
            """, (offset + 1,))
            result = cursor.fetchone()
            return float(result['close']) if result else None
    except Exception as e:
        logger.error(f"Error fetching historical CMP for {symbol}: {e}")
        return None

# Callback to update selected period
@app.callback(
    Output('selected-period', 'data'),
    [Input('period-1d', 'n_clicks'),
     Input('period-5d', 'n_clicks'),
     Input('period-1m', 'n_clicks'),
     Input('period-6m', 'n_clicks'),
     Input('period-ytd', 'n_clicks'),
     Input('period-1y', 'n_clicks'),
     Input('period-5y', 'n_clicks'),
     Input('period-max', 'n_clicks')],
    [State('selected-period', 'data')]
)
def update_period(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, current_period):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_period
        
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    period_map = {
        'period-1d': '1D',
        'period-5d': '5D',
        'period-1m': '1M',
        'period-6m': '6M',
        'period-ytd': 'YTD',
        'period-1y': '1Y',
        'period-5y': '5Y',
        'period-max': 'MAX'
    }
    
    return period_map.get(button_id, current_period)

# Callback to update metrics and store data
@app.callback(
    [Output('metrics-container', 'children'),
     Output('store-cmp-data', 'data'),
     Output('status-message', 'children')],
    [Input('submit-button', 'n_clicks')],
    [State('symbol-input', 'value')]
)
def update_metrics(n_clicks, symbol):
    if n_clicks == 0 or not symbol:
        return [html.Div()], {}, ""
    
    symbol = symbol.strip().upper()
    conn = get_db_connector()
    if not conn:
        return [html.Div("❌ Database connection failed")], {}, "Database connection error"
    
    try:
        # Get current and historical prices
        cmp = get_cmp(conn, symbol)
        cmp_5d = get_historical_cmp(conn, symbol, 5)
        cmp_1m = get_historical_cmp(conn, symbol, 20)
        
        if cmp is None:
            return [html.Div(f"❌ No data found for symbol: {symbol}")], {}, f"Symbol '{symbol}' not found in database"
        
        # Calculate percentage changes
        def calc_pct(current, historical):
            if None in (current, historical) or historical == 0:
                return None, '--'
            pct = ((current - historical) / historical) * 100
            return pct, f"{pct:+.2f}%"
        
        pct_5d_val, pct_5d = calc_pct(cmp, cmp_5d)
        pct_1m_val, pct_1m = calc_pct(cmp, cmp_1m)
        
        # Create metrics cards
        metrics = [
            {
                "label": "📈 Current Price", 
                "value": f"₹{cmp:.2f}" if cmp else "N/A", 
                "pct": "",
                "class": ""
            },
            {
                "label": "📅 5 Days Change", 
                "value": f"₹{cmp_5d:.2f}" if cmp_5d else "N/A", 
                "pct": pct_5d,
                "class": "positive" if pct_5d_val and pct_5d_val >= 0 else "negative"
            },
            {
                "label": "📆 1 Month Change", 
                "value": f"₹{cmp_1m:.2f}" if cmp_1m else "N/A", 
                "pct": pct_1m,
                "class": "positive" if pct_1m_val and pct_1m_val >= 0 else "negative"
            }
        ]
        
        metric_cards = []
        for metric in metrics:
            card = html.Div([
                html.Div(metric["label"], className="metric-label"),
                html.Div(metric["value"], className="metric-value"),
                html.Div(metric["pct"], className=f"metric-pct {metric['class']}") if metric["pct"] else html.Div()
            ], className="metric-card")
            metric_cards.append(card)
        
        # Store data for chart callback
        store_data = {
            "symbol": symbol,
            "cmp": cmp,
            "cmp_5d": cmp_5d,
            "cmp_1m": cmp_1m
        }
        
        status = f"✅ Successfully loaded data for {symbol}"
        return metric_cards, store_data, status
        
    except Exception as e:
        logger.error(f"Error updating metrics: {e}")
        return [html.Div(f"❌ Error processing data: {str(e)}")], {}, f"Error: {str(e)}"
    finally:
        if conn:
            conn.close()

# Callback to update candlestick chart
@app.callback(
    Output('candlestick-chart', 'figure'),
    [Input('store-cmp-data', 'data'),
     Input('selected-period', 'data')]
)
def update_chart(store_data, period):
    if not store_data or 'symbol' not in store_data:
        return go.Figure()
    
    symbol = store_data['symbol']
    conn = get_db_connector()
    if not conn:
        return go.Figure()
    
    try:
        # Get OHLC data based on selected period
        ohlc_data = get_ohlc_data(conn, symbol, period)
        if ohlc_data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"No data available for {symbol}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=20, color="gray")
            )
            return fig
        
        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=ohlc_data['datetime'],
            open=ohlc_data['open'],
            high=ohlc_data['high'],
            low=ohlc_data['low'],
            close=ohlc_data['close'],
            increasing_line_color='#10b981',
            decreasing_line_color='#ef4444',
            increasing_fillcolor='#10b981',
            decreasing_fillcolor='#ef4444',
            name=symbol
        )])
        
        # Update layout
        period_labels = {
            '1D': '1 Day',
            '5D': '5 Days',
            '1M': '1 Month',
            '6M': '6 Months',
            'YTD': 'Year-to-Date',
            '1Y': '1 Year',
            '5Y': '5 Years',
            'MAX': 'All Time'
        }
        
        fig.update_layout(
            title={
                'text': f'📊 {symbol} Candlestick Chart ({period_labels.get(period, period)})',
                'x': 0.5,
                'font': {'size': 20, 'color': '#f8fafc'}
            },
            xaxis_title='📅 Date',
            yaxis_title='💰 Price (₹)',
            xaxis_rangeslider_visible=False,
            plot_bgcolor='#0f172a',
            paper_bgcolor='#1e293b',
            font=dict(family="Segoe UI, Arial, sans-serif", color='#f8fafc'),
            margin=dict(l=60, r=60, t=80, b=60),
            hovermode='x unified',
            xaxis=dict(
                gridcolor='#334155',
                showgrid=True,
                color='#94a3b8'
            ),
            yaxis=dict(
                gridcolor='#334155',
                showgrid=True,
                color='#94a3b8'
            )
        )
        
        # Add moving averages for periods longer than 1D
        if period != '1D' and len(ohlc_data) > 20:
            ohlc_data['20ma'] = ohlc_data['close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(
                x=ohlc_data['datetime'],
                y=ohlc_data['20ma'],
                mode='lines',
                name='20-Day MA',
                line=dict(color='#3b82f6', width=2),
                opacity=0.8
            ))
        
        if period not in ['1D', '5D'] and len(ohlc_data) > 50:
            ohlc_data['50ma'] = ohlc_data['close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(
                x=ohlc_data['datetime'],
                y=ohlc_data['50ma'],
                mode='lines',
                name='50-Day MA',
                line=dict(color='#f59e0b', width=2),
                opacity=0.8
            ))
        
        return fig
        
    except Exception as e:
        logger.error(f"Error updating chart: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading chart: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="red")
        )
        return fig
    finally:
        if conn:
            conn.close()

# Callback to update active period button classes
@app.callback(
    [Output(f'period-{period}', 'className') for period in ['1d', '5d', '1m', '6m', 'ytd', '1y', '5y', 'max']],
    [Input('selected-period', 'data')]
)
def update_active_button(selected_period):
    # Map selected period to button ID
    period_map = {
        '1D': '1d',
        '5D': '5d',
        '1M': '1m',
        '6M': '6m',
        'YTD': 'ytd',
        '1Y': '1y',
        '5Y': '5y',
        'MAX': 'max'
    }
    
    # Initialize all buttons as inactive
    class_names = ['period-button'] * 8
    
    # Activate the selected button
    if selected_period in period_map:
        btn_index = ['1d', '5d', '1m', '6m', 'ytd', '1y', '5y', 'max'].index(period_map[selected_period])
        class_names[btn_index] = 'period-button active'
    
    return class_names

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import pandas as pd
import logging
from datetime import datetime, timedelta
import sqlite3
import os

# Initialize Dash app
dash_app = dash.Dash(__name__, url_base_pathname='/dash-charts/')
dash_app.title = "Stock Analysis Dashboard"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# App layout
dash_app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Input(
                id='symbol-input',
                type='text',
                placeholder='Enter symbol',
                className='symbol-input',
                value='RELIANCE'  # Default value
            ),
            html.Button('Submit', id='submit-button', n_clicks=0, className='submit-button'),
        ], className='input-container'),
    ], className="header"),
    
    html.Div([
        html.Button('1D', id='period-1d', className='period-button', n_clicks=0),
        html.Button('1W', id='period-1w', className='period-button', n_clicks=0),
        html.Button('1M', id='period-1m', className='period-button', n_clicks=0),
        html.Button('3M', id='period-3m', className='period-button', n_clicks=0),
    ], className='period-buttons'),
    
    html.Div([
        dcc.Graph(id='candlestick-chart')
    ], className='chart-container'),
    
], className='dashboard')

def get_sample_data(symbol='RELIANCE', period='1D'):
    """Generate sample OHLC data for demonstration"""
    try:
        # Generate sample data based on period
        if period == '1D':
            periods = 24
            freq = 'H'
        elif period == '1W':
            periods = 7
            freq = 'D'
        elif period == '1M':
            periods = 30
            freq = 'D'
        else:  # 3M
            periods = 90
            freq = 'D'
        
        # Create sample dates
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=periods, freq=freq)
        
        # Generate sample OHLC data
        import numpy as np
        np.random.seed(42)  # For consistent demo data
        
        base_price = 2500  # Sample base price
        
        # Generate price movements
        price_changes = np.random.normal(0, 20, periods)
        prices = base_price + np.cumsum(price_changes)
        
        # Generate OHLC data
        data = []
        for i, date in enumerate(dates):
            open_price = prices[i] if i == 0 else data[i-1]['close']
            close_price = prices[i]
            high_price = max(open_price, close_price) + abs(np.random.normal(0, 10))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, 10))
            
            data.append({
                'date': date,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': np.random.randint(100000, 1000000)
            })
        
        df = pd.DataFrame(data)
        logger.info(f"Generated sample data for {symbol} with {len(df)} records")
        return df
        
    except Exception as e:
        logger.error(f"Error generating sample data: {e}")
        return pd.DataFrame()

def get_historical_data(symbol, period='1D'):
    """
    Get historical data for the symbol from database or fallback to sample data
    """
    try:
        # Try to get data from database first
        db_path = os.path.join('instance', 'trading_platform.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            
            # Try to get data from _daily table if it exists
            query = f"""
            SELECT date, open, high, low, close, volume 
            FROM _daily 
            WHERE symbol = ? 
            ORDER BY date DESC 
            LIMIT 100
            """
            
            try:
                df = pd.read_sql_query(query, conn, params=[symbol])
                conn.close()
                
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    logger.info(f"Retrieved {len(df)} records from database for {symbol}")
                    return df
            except Exception as db_error:
                logger.warning(f"Database query failed: {db_error}")
                conn.close()
        
        # Fallback to sample data
        logger.info(f"Using sample data for {symbol}")
        return get_sample_data(symbol, period)
        
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return get_sample_data(symbol, period)

@dash_app.callback(
    Output('candlestick-chart', 'figure'),
    [Input('submit-button', 'n_clicks'),
     Input('period-1d', 'n_clicks'),
     Input('period-1w', 'n_clicks'),
     Input('period-1m', 'n_clicks'),
     Input('period-3m', 'n_clicks')],
    [State('symbol-input', 'value')]
)
def update_chart(submit_clicks, period_1d, period_1w, period_1m, period_3m, symbol):
    """Update candlestick chart based on symbol and period"""
    try:
        # Determine which period was clicked
        ctx = dash.callback_context
        if ctx.triggered:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if 'period-1d' in button_id:
                period = '1D'
            elif 'period-1w' in button_id:
                period = '1W'
            elif 'period-1m' in button_id:
                period = '1M'
            elif 'period-3m' in button_id:
                period = '3M'
            else:
                period = '1D'
        else:
            period = '1D'
        
        if not symbol:
            symbol = 'RELIANCE'
            
        # Get historical data
        df = get_historical_data(symbol, period)
        
        if df.empty:
            # Return empty chart if no data
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            return fig
        
        # Create candlestick chart
        fig = go.Figure(data=go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol,
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        ))
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} - {period} Candlestick Chart',
            xaxis_title='Date',
            yaxis_title='Price (₹)',
            template='plotly_dark',
            height=600,
            xaxis_rangeslider_visible=False,
            showlegend=False
        )
        
        logger.info(f"Updated chart for {symbol} with {len(df)} data points")
        return fig
        
    except Exception as e:
        logger.error(f"Error updating chart: {e}")
        # Return error chart
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading chart: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color='red')
        )
        return fig

# Add CSS styling
dash_app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #1e1e1e;
                color: white;
                margin: 0;
                padding: 20px;
            }
            .dashboard {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 20px;
            }
            .input-container {
                display: flex;
                justify-content: center;
                gap: 10px;
                margin-bottom: 20px;
            }
            .symbol-input {
                padding: 10px;
                border: 1px solid #444;
                border-radius: 5px;
                background-color: #333;
                color: white;
                font-size: 16px;
            }
            .submit-button {
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            .submit-button:hover {
                background-color: #0056b3;
            }
            .period-buttons {
                display: flex;
                justify-content: center;
                gap: 10px;
                margin-bottom: 20px;
            }
            .period-button {
                padding: 8px 16px;
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                cursor: pointer;
            }
            .period-button:hover {
                background-color: #555;
            }
            .chart-container {
                background-color: #2a2a2a;
                border-radius: 10px;
                padding: 20px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    dash_app.run_server(debug=True, host='0.0.0.0', port=8050)
