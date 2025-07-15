from core.database import db
from datetime import datetime, timedelta
import logging

class AdminTradeSignal(db.Model):
    __tablename__ = 'admin_trade_signals'

    id = db.Column(db.Integer, primary_key=True)
    # target_user_id column doesn't exist in actual database schema

    # Signal Information
    symbol = db.Column(db.String(50), nullable=False)
    trading_symbol = db.Column(db.String(100), nullable=True)
    token = db.Column(db.String(50), nullable=True)
    exchange = db.Column(db.String(20), default='NSE')

    # Signal Details
    signal_type = db.Column(db.String(20), nullable=False)  # BUY, SELL
    entry_price = db.Column(db.Numeric(10, 2), nullable=False)
    target_price = db.Column(db.Numeric(10, 2), nullable=True)
    stop_loss = db.Column(db.Numeric(10, 2), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)

    # Signal Metadata
    signal_title = db.Column(db.String(200), nullable=True)
    signal_description = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), default='MEDIUM')  # HIGH, MEDIUM, LOW

    # Status and Timestamps
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, EXECUTED, EXPIRED, CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    signal_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)

    # Current Market Data
    current_price = db.Column(db.Numeric(10, 2), nullable=True)
    change_percent = db.Column(db.Numeric(5, 2), nullable=True)
    last_update_time = db.Column(db.DateTime, nullable=True)

    # Additional Trading Data
    investment_amount = db.Column(db.Numeric(12, 2), nullable=True)
    current_value = db.Column(db.Numeric(12, 2), nullable=True)
    pnl = db.Column(db.Numeric(12, 2), nullable=True)
    pnl_percentage = db.Column(db.Numeric(5, 2), nullable=True)

    # Relationships
    #admin_user = db.relationship('User', foreign_keys=[admin_user_id], backref='sent_signals')
    #target_user = db.relationship('User', foreign_keys=[target_user_id], backref='received_signals')

    def __repr__(self):
        return f'<AdminTradeSignal {self.symbol} - {self.signal_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            #'admin_user_id': self.admin_user_id,
            # 'target_user_id': self.target_user_id,  # Column doesn't exist
            'symbol': self.symbol,
            'trading_symbol': self.trading_symbol,
            'token': self.token,
            'exchange': self.exchange,
            'signal_type': self.signal_type,
            'entry_price': float(self.entry_price) if self.entry_price else None,
            'target_price': float(self.target_price) if self.target_price else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'quantity': self.quantity,
            'signal_title': self.signal_title,
            'signal_description': self.signal_description,
            'priority': self.priority,
            'status': self.status,
            'current_price': float(self.current_price) if self.current_price else None,
            'change_percent': float(self.change_percent) if self.change_percent else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None
        }

class KotakNeoQuote(db.Model):
    """Enhanced Kotak Neo quotes data table with comprehensive market data"""
    __tablename__ = 'kotak_neo_quotes'

    id = db.Column(db.Integer, primary_key=True)

    # Instrument Identification
    symbol = db.Column(db.String(50), nullable=False, index=True)
    trading_symbol = db.Column(db.String(100), nullable=True)
    token = db.Column(db.String(50), nullable=True, index=True)
    exchange = db.Column(db.String(20), default='NSE')
    segment = db.Column(db.String(20), nullable=True)  # EQ, FO, CD, etc.
    instrument_type = db.Column(db.String(20), nullable=True)  # EQ, FUT, OPT, etc.

    # Price Data (from Kotak Neo Quotes API)
    ltp = db.Column(db.Numeric(12, 4), nullable=False)  # Last Traded Price
    open_price = db.Column(db.Numeric(12, 4), nullable=True)
    high_price = db.Column(db.Numeric(12, 4), nullable=True)
    low_price = db.Column(db.Numeric(12, 4), nullable=True)
    close_price = db.Column(db.Numeric(12, 4), nullable=True)  # Previous close

    # Change Calculations
    net_change = db.Column(db.Numeric(12, 4), nullable=True)  # Price change
    percentage_change = db.Column(db.Numeric(8, 4), nullable=True)  # % change

    # Volume Data
    volume = db.Column(db.BigInteger, nullable=True)  # Today's volume
    value = db.Column(db.Numeric(15, 2), nullable=True)  # Turnover value

    # Bid/Ask Data
    bid_price = db.Column(db.Numeric(12, 4), nullable=True)
    ask_price = db.Column(db.Numeric(12, 4), nullable=True)
    bid_size = db.Column(db.Integer, nullable=True)
    ask_size = db.Column(db.Integer, nullable=True)

    # Circuit Limits
    upper_circuit = db.Column(db.Numeric(12, 4), nullable=True)
    lower_circuit = db.Column(db.Numeric(12, 4), nullable=True)

    # 52-week Data
    week_52_high = db.Column(db.Numeric(12, 4), nullable=True)
    week_52_low = db.Column(db.Numeric(12, 4), nullable=True)

    # Average Prices
    avg_price = db.Column(db.Numeric(12, 4), nullable=True)  # VWAP

    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_trade_time = db.Column(db.DateTime, nullable=True)

    # Market Status
    market_status = db.Column(db.String(20), default='OPEN')  # OPEN, CLOSED, PRE_OPEN

    # Data Quality
    data_source = db.Column(db.String(50), default='KOTAK_NEO_API')
    fetch_status = db.Column(db.String(20), default='SUCCESS')  # SUCCESS, ERROR, STALE

    # Additional Meta Data
    lot_size = db.Column(db.Integer, nullable=True)
    tick_size = db.Column(db.Numeric(8, 4), nullable=True)

    def __repr__(self):
        return f'<KotakNeoQuote {self.symbol} @ ₹{self.ltp}>'

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'trading_symbol': self.trading_symbol,
            'token': self.token,
            'exchange': self.exchange,
            'segment': self.segment,
            'instrument_type': self.instrument_type,
            'ltp': float(self.ltp) if self.ltp else None,
            'open_price': float(self.open_price) if self.open_price else None,
            'high_price': float(self.high_price) if self.high_price else None,
            'low_price': float(self.low_price) if self.low_price else None,
            'close_price': float(self.close_price) if self.close_price else None,
            'net_change': float(self.net_change) if self.net_change else None,
            'percentage_change': float(self.percentage_change) if self.percentage_change else None,
            'volume': self.volume,
            'value': float(self.value) if self.value else None,
            'bid_price': float(self.bid_price) if self.bid_price else None,
            'ask_price': float(self.ask_price) if self.ask_price else None,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size,
            'upper_circuit': float(self.upper_circuit) if self.upper_circuit else None,
            'lower_circuit': float(self.lower_circuit) if self.lower_circuit else None,
            'week_52_high': float(self.week_52_high) if self.week_52_high else None,
            'week_52_low': float(self.week_52_low) if self.week_52_low else None,
            'avg_price': float(self.avg_price) if self.avg_price else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'last_trade_time': self.last_trade_time.isoformat() if self.last_trade_time else None,
            'market_status': self.market_status,
            'data_source': self.data_source,
            'fetch_status': self.fetch_status,
            'lot_size': self.lot_size,
            'tick_size': float(self.tick_size) if self.tick_size else None
        }

class RealtimeQuote(db.Model):
    """Legacy real-time quotes table for backward compatibility"""
    __tablename__ = 'realtime_quotes'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), nullable=False, index=True)
    trading_symbol = db.Column(db.String(100), nullable=True)
    token = db.Column(db.String(50), nullable=True)
    exchange = db.Column(db.String(20), default='NSE')

    # Market Data
    current_price = db.Column(db.Numeric(10, 2), nullable=False)
    open_price = db.Column(db.Numeric(10, 2), nullable=True)
    high_price = db.Column(db.Numeric(10, 2), nullable=True)
    low_price = db.Column(db.Numeric(10, 2), nullable=True)
    close_price = db.Column(db.Numeric(10, 2), nullable=True)

    # Change Calculations
    change_amount = db.Column(db.Numeric(10, 2), nullable=True)
    change_percent = db.Column(db.Numeric(5, 2), nullable=True)

    # Volume and Liquidity
    volume = db.Column(db.BigInteger, nullable=True)
    avg_volume = db.Column(db.BigInteger, nullable=True)

    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    market_status = db.Column(db.String(20), default='OPEN')  # OPEN, CLOSED, PRE_OPEN

    # Data Source
    data_source = db.Column(db.String(50), default='KOTAK_NEO')
    fetch_status = db.Column(db.String(20), default='SUCCESS')  # SUCCESS, ERROR, STALE

    def __repr__(self):
        return f'<RealtimeQuote {self.symbol} @ {self.current_price}>'

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'trading_symbol': self.trading_symbol,
            'token': self.token,
            'exchange': self.exchange,
            'current_price': float(self.current_price) if self.current_price else None,
            'open_price': float(self.open_price) if self.open_price else None,
            'high_price': float(self.high_price) if self.high_price else None,
            'low_price': float(self.low_price) if self.low_price else None,
            'close_price': float(self.close_price) if self.close_price else None,
            'change_amount': float(self.change_amount) if self.change_amount else None,
            'change_percent': float(self.change_percent) if self.change_percent else None,
            'volume': self.volume,
            'avg_volume': self.avg_volume,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'market_status': self.market_status,
            'data_source': self.data_source,
            'fetch_status': self.fetch_status
        }

class UserNotification(db.Model):
    __tablename__ = 'user_notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Notification Content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='GENERAL')  # TRADE_SIGNAL, DEAL_UPDATE, GENERAL
    priority = db.Column(db.String(20), default='MEDIUM')

    # Status
    is_read = db.Column(db.Boolean, default=False)
    is_delivered = db.Column(db.Boolean, default=False)

    # Relationships
    related_signal_id = db.Column(db.Integer, db.ForeignKey('admin_trade_signals.id'), nullable=True)
    related_deal_id = db.Column(db.Integer, db.ForeignKey('user_deals.id'), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='notifications')
    related_signal = db.relationship('AdminTradeSignal', backref='notifications')

    def __repr__(self):
        return f'<UserNotification {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'priority': self.priority,
            'is_read': self.is_read,
            'is_delivered': self.is_delivered,
            'related_signal_id': self.related_signal_id,
            'related_deal_id': self.related_deal_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None
        }

class UserDeal(db.Model):
    __tablename__ = 'user_deals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    signal_id = db.Column(db.Integer, db.ForeignKey('admin_trade_signals.id'), nullable=True)

    # ETF Signal Trade ID and Basic Info
    trade_signal_id = db.Column(db.String(50), nullable=True)  # Original trade signal ID from ETF signals
    etf_symbol = db.Column(db.String(50), nullable=False)  # ETF field from signals
    symbol = db.Column(db.String(50), nullable=False)
    trading_symbol = db.Column(db.String(100), nullable=False)
    exchange = db.Column(db.String(20), default='NSE')

    # Complete ETF Signal Data (All fields from signals table)
    pos = db.Column(db.Integer, nullable=True)  # Position (1=LONG, -1=SHORT)
    qty = db.Column(db.Integer, nullable=False)  # Quantity
    ep = db.Column(db.Numeric(10, 2), nullable=False)  # Entry Price
    cmp = db.Column(db.Numeric(10, 2), nullable=True)  # Current Market Price
    tp = db.Column(db.Numeric(10, 2), nullable=True)  # Target Price
    inv = db.Column(db.Numeric(12, 2), nullable=True)  # Investment Amount
    pl = db.Column(db.Numeric(12, 2), nullable=True)  # Profit/Loss
    chan_percent = db.Column(db.String(20), nullable=True)  # % Change
    thirty = db.Column(db.String(20), nullable=True)  # 30 day performance
    dh = db.Column(db.Integer, nullable=True)  # Days Held
    signal_date = db.Column(db.String(20), nullable=True)  # Date from signal
    ed = db.Column(db.String(20), nullable=True)  # Entry Date
    exp = db.Column(db.String(50), nullable=True)  # Expiry
    pr = db.Column(db.String(20), nullable=True)  # Price Range
    pp = db.Column(db.String(20), nullable=True)  # Performance Points
    iv = db.Column(db.String(20), nullable=True)  # Implied Volatility
    ip = db.Column(db.String(20), nullable=True)  # Intraday Performance
    nt = db.Column(db.Text, nullable=True)  # Notes/Tags
    qt = db.Column(db.String(20), nullable=True)  # Quote Time
    seven = db.Column(db.String(20), nullable=True)  # 7 day change
    ch = db.Column(db.String(20), nullable=True)  # % Change (alternate)
    tva = db.Column(db.Numeric(12, 2), nullable=True)  # Target Value Amount
    tpr = db.Column(db.Numeric(12, 2), nullable=True)  # Target Profit Return

    # Standard Deal Fields (derived from signal data)
    position_type = db.Column(db.String(10), nullable=False)  # LONG, SHORT
    quantity = db.Column(db.Integer, nullable=False)
    entry_price = db.Column(db.Numeric(10, 2), nullable=False)
    current_price = db.Column(db.Numeric(10, 2), nullable=True)
    target_price = db.Column(db.Numeric(10, 2), nullable=True)
    stop_loss = db.Column(db.Numeric(10, 2), nullable=True)

    # P&L Calculations
    invested_amount = db.Column(db.Numeric(12, 2), nullable=False)
    current_value = db.Column(db.Numeric(12, 2), nullable=True)
    pnl_amount = db.Column(db.Numeric(12, 2), nullable=True)
    pnl_percent = db.Column(db.Numeric(5, 2), nullable=True)

    # Deal Status
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, CLOSED, CANCELLED
    deal_type = db.Column(db.String(20), default='SIGNAL')  # SIGNAL, MANUAL

    # Additional Metadata
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(200), nullable=True)

    # Timestamps
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)
    exit_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_price_update = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='deals')
    signal = db.relationship('AdminTradeSignal', backref='deals')

    @property
    def days_held(self):
        """Calculate days held for the deal"""
        if self.entry_date:
            end_date = self.exit_date or datetime.utcnow()
            return (end_date - self.entry_date).days
        return 0

    def calculate_pnl(self):
        """Calculate P&L based on current price vs entry price"""
        try:
            if not self.current_price or not self.entry_price or not self.quantity:
                self.pnl_amount = 0.0
                self.pnl_percent = 0.0
                return

            # Calculate P&L based on position type
            if self.position_type == 'LONG':
                self.pnl_amount = (float(self.current_price) - float(self.entry_price)) * int(self.quantity)
            else:  # SHORT
                self.pnl_amount = (float(self.entry_price) - float(self.current_price)) * int(self.quantity)

            # Calculate percentage
            if self.invested_amount and float(self.invested_amount) > 0:
                self.pnl_percent = (float(self.pnl_amount) / float(self.invested_amount)) * 100
            else:
                self.pnl_percent = 0.0

            # Update current value
            self.current_value = float(self.invested_amount or 0) + float(self.pnl_amount or 0)
            self.last_price_update = datetime.utcnow()

        except Exception as e:
            logging.error(f"Error calculating P&L for deal {self.id}: {e}")
            self.pnl_amount = 0.0
            self.pnl_percent = 0.0
            self.current_value = float(self.invested_amount or 0)

    def to_dict(self):
        """Convert deal to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'signal_id': self.signal_id,
            'trade_signal_id': self.trade_signal_id,
            'etf_symbol': self.etf_symbol,
            'symbol': self.symbol,
            'trading_symbol': self.trading_symbol,
            'exchange': self.exchange,
            'position_type': self.position_type,
            'quantity': self.quantity,
            'entry_price': float(self.entry_price) if self.entry_price else 0.0,
            'current_price': float(self.current_price) if self.current_price else 0.0,
            'target_price': float(self.target_price) if self.target_price else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'invested_amount': float(self.invested_amount) if self.invested_amount else 0.0,
            'pnl_amount': float(self.pnl_amount) if self.pnl_amount else 0.0,
            'pnl_percent': float(self.pnl_percent) if self.pnl_percent else 0.0,
            'status': self.status,
            'notes': self.notes,
            'tags': self.tags,
            'deal_type': self.deal_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'exit_date': self.exit_date.isoformat() if self.exit_date else None,

            # Position data - ensure both formats are available
            'pos': self.pos if hasattr(self, 'pos') and self.pos is not None else (1 if self.position_type == 'LONG' else 0),
            'position': self.pos if hasattr(self, 'pos') and self.pos is not None else (1 if self.position_type == 'LONG' else 0),

            # ETF Signal specific fields
            'qty': self.qty,
            'ep': float(self.ep) if self.ep else 0.0,
            'cmp': float(self.cmp) if self.cmp else 0.0,
            'tp': float(self.tp) if self.tp else None,
            'inv': float(self.inv) if self.inv else 0.0,
            'pl': float(self.pl) if self.pl else 0.0,
            'chan_percent': self.chan_percent,
            'thirty': self.thirty,
            'dh': self.dh,
            'date': self.signal_date,
            'signal_date': self.signal_date,
            'ed': self.ed,
            'exp': self.exp,
            'pr': self.pr,
            'pp': self.pp,
            'iv': self.iv,
            'ip': self.ip,
            'nt': self.nt,
            'qt': self.qt,
            'seven': self.seven,
            'ch': self.ch,
            'tva': float(self.tva) if self.tva else None,
            'tpr': float(self.tpr) if self.tpr else None
        }

    def __repr__(self):
        return f'<UserDeal {self.id}: {self.symbol} {self.position_type}>'

class ETFSignalTrade(db.Model):
    """ETF Signal Trade Model for tracking ETF trading signals and performance"""
    __tablename__ = 'etf_signal_trades'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # ETF Information
    symbol = db.Column(db.String(50), nullable=False, index=True)
    etf_name = db.Column(db.String(200), nullable=True)
    trading_symbol = db.Column(db.String(100), nullable=True)
    token = db.Column(db.String(50), nullable=True)
    exchange = db.Column(db.String(20), default='NSE')

    # Signal Details
    signal_type = db.Column(db.String(20), nullable=False)  # BUY, SELL, HOLD
    quantity = db.Column(db.Integer, nullable=False)
    entry_price = db.Column(db.Numeric(10, 2), nullable=False)
    current_price = db.Column(db.Numeric(10, 2), nullable=True)
    target_price = db.Column(db.Numeric(10, 2), nullable=True)
    stop_loss = db.Column(db.Numeric(10, 2), nullable=True)

    # Financial Calculations
    invested_amount = db.Column(db.Numeric(12, 2), nullable=False)
    current_value = db.Column(db.Numeric(12, 2), nullable=True)
    pnl_amount = db.Column(db.Numeric(12, 2), nullable=True)
    pnl_percent = db.Column(db.Numeric(5, 2), nullable=True)

    # Trade Metadata
    trade_title = db.Column(db.String(200), nullable=True)
    trade_description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), default='MEDIUM')  # HIGH, MEDIUM, LOW
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, CLOSED, EXPIRED

    # Position Information
    position_type = db.Column(db.String(10), default='LONG')  # LONG, SHORT

    # Additional Trading Fields
    change_pct = db.Column(db.String(20), nullable=True)
    tp_value = db.Column(db.Numeric(12, 2), nullable=True)
    tp_return = db.Column(db.String(20), nullable=True)

    # Timestamps
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_price_update = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='etf_signal_trades')
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_user_id], backref='assigned_etf_trades')

    def __repr__(self):
        return f'<ETFSignalTrade {self.symbol} - {self.signal_type}>'

    def calculate_pnl(self):
        """Calculate current P&L based on current price"""
        if self.current_price and self.entry_price and self.quantity:
            if self.position_type == 'LONG':
                self.pnl_amount = (self.current_price - self.entry_price) * self.quantity
            else:  # SHORT
                self.pnl_amount = (self.entry_price - self.current_price) * self.quantity

            if self.invested_amount and self.invested_amount > 0:
                self.pnl_percent = (self.pnl_amount / self.invested_amount) * 100

            self.current_value = self.invested_amount + self.pnl_amount if self.invested_amount else 0
            self.change_pct = f"{self.pnl_percent:.2f}%" if self.pnl_percent else "0.00%"

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'assigned_by_user_id': self.assigned_by_user_id,
            'symbol': self.symbol,
            'etf_name': self.etf_name,
            'trading_symbol': self.trading_symbol,
            'token': self.token,
            'exchange': self.exchange,
            'signal_type': self.signal_type,
            'quantity': self.quantity,
            'entry_price': float(self.entry_price) if self.entry_price else None,
            'current_price': float(self.current_price) if self.current_price else None,
            'target_price': float(self.target_price) if self.target_price else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'invested_amount': float(self.invested_amount) if self.invested_amount else None,
            'current_value': float(self.current_value) if self.current_value else None,
            'pnl_amount': float(self.pnl_amount) if self.pnl_amount else None,
            'pnl_percent': float(self.pnl_percent) if self.pnl_percent else None,
            'trade_title': self.trade_title,
            'trade_description': self.trade_description,
            'priority': self.priority,
            'status': self.status,
            'position_type': self.position_type,
            'change_pct': self.change_pct,
            'tp_value': float(self.tp_value) if self.tp_value else None,
            'tp_return': self.tp_return,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_price_update': self.last_price_update.isoformat() if self.last_price_update else None
        }
# Remove admin_user_id column from AdminTradeSignal model