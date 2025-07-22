import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import pandas as pd
import logging
from datetime import datetime, timedelta
import sqlite3
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Dash app
dash_app = dash.Dash(__name__, url_base_pathname='/dash-charts/')
dash_app.title = "Stock Analysis Dashboard"

def get_historical_data(symbol='AUTO'):
    """Get historical data from database or create sample data"""
    try:
        # Try to get data from database
        db_path = os.path.join('instance', 'trading_platform.db')
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            query = f"SELECT * FROM daily WHERE symbol = '{symbol}' ORDER BY date DESC LIMIT 100"
            df = pd.read_sql_query(query, conn)
            conn.close()
            if not df.empty:
                return df
    except Exception as e:
        logger.warning(f"Could not fetch data from database: {e}")

    # Create sample data if database is not available
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    data = []
    base_price = 1000

    for i, date in enumerate(dates):
        open_price = base_price + (i * 2) + (i % 5 - 2) * 10
        high_price = open_price + abs(i % 7) * 5
        low_price = open_price - abs(i % 6) * 3
        close_price = open_price + (i % 3 - 1) * 8
        volume = 100000 + (i % 10) * 50000

        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume,
            'symbol': symbol
        })

    return pd.DataFrame(data)

# App layout
dash_app.layout = html.Div([
    html.Div([
        html.Div([
            html.H1("Stock Analysis Dashboard", className="header-title"),
            html.P("Interactive candlestick charts with historical data", className="header-subtitle")
        ], className="header-content"),

        html.Div([
            dcc.Input(
                id='symbol-input',
                type='text',
                placeholder='Enter symbol',
                className='symbol-input',
                value='AUTO'
            ),
            html.Button('Submit', id='submit-button', n_clicks=0, className='submit-button'),
        ], className='input-container'),
    ], className="header"),

    html.Div([
        html.Button('1D', id='period-1d', className='period-button active', n_clicks=0),
        html.Button('1W', id='period-1w', className='period-button', n_clicks=0),
        html.Button('1M', id='period-1m', className='period-button', n_clicks=0),
        html.Button('3M', id='period-3m', className='period-button', n_clicks=0),
        html.Button('1Y', id='period-1y', className='period-button', n_clicks=0),
    ], className="period-selector"),

    html.Div([
        dcc.Graph(id='candlestick-chart', className='chart'),
    ]),

    html.Div(id='chart-status', className='status-message')
])

@dash_app.callback(
    [Output('candlestick-chart', 'figure'),
     Output('chart-status', 'children')],
    [Input('submit-button', 'n_clicks'),
     Input('period-1d', 'n_clicks'),
     Input('period-1w', 'n_clicks'), 
     Input('period-1m', 'n_clicks'),
     Input('period-3m', 'n_clicks'),
     Input('period-1y', 'n_clicks')],
    [State('symbol-input', 'value')]
)
def update_chart(submit_clicks, d1_clicks, w1_clicks, m1_clicks, m3_clicks, y1_clicks, symbol):
    """Update candlestick chart based on symbol and period selection"""
    if not symbol:
        symbol = 'AUTO'

    try:
        # Get historical data
        df = get_historical_data(symbol.upper())

        if df.empty:
            return {}, f"No data available for symbol: {symbol}"

        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol.upper(),
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        )])

        # Update layout
        fig.update_layout(
            title=f"{symbol.upper()} - Candlestick Chart",
            xaxis_title="Date",
            yaxis_title="Price (₹)",
            template="plotly_dark",
            height=600,
            margin=dict(l=50, r=50, t=50, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff')
        )

        fig.update_xaxes(
            gridcolor='rgba(255,255,255,0.1)',
            linecolor='rgba(255,255,255,0.2)'
        )
        fig.update_yaxes(
            gridcolor='rgba(255,255,255,0.1)',
            linecolor='rgba(255,255,255,0.2)'
        )

        status_message = f"Showing {len(df)} data points for {symbol.upper()}"

        return fig, status_message

    except Exception as e:
        logger.error(f"Error updating chart: {e}")
        return {}, f"Error loading chart for {symbol}: {str(e)}"

# Custom CSS
dash_app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
        :root {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --card-bg: #333333;
            --text-primary: #ffffff;
            --text-secondary: #cccccc;
            --border-color: #444444;
            --primary-color: #007bff;
            --success-color: #00ff88;
            --danger-color: #ff4444;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: var(--text-primary);
            min-height: 100vh;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: var(--card-bg);
            border-radius: 16px;
            border: 1px solid var(--border-color);
        }

        .header-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin: 0 0 10px 0;
        }

        .header-subtitle {
            color: var(--text-secondary);
            margin: 0;
            font-size: 1.1rem;
        }

        .input-container {
            display: flex;
            gap: 15px;
            justify-content: center;
            align-items: center;
            margin-top: 20px;
        }

        .symbol-input {
            padding: 12px 16px;
            font-size: 16px;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            outline: none;
            transition: border-color 0.3s;
        }

        .symbol-input:focus {
            border-color: var(--primary-color);
        }

        .submit-button {
            padding: 12px 24px;
            font-size: 16px;
            font-weight: 600;
            background: linear-gradient(45deg, var(--primary-color), #0056b3);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .submit-button:hover {
            transform: translateY(-2px);
        }

        .period-selector {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }

        .period-button {
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            background: var(--bg-secondary);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .period-button:hover,
        .period-button.active {
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
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

# Add server for integration
server = dash_app.server