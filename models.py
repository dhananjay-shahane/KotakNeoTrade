from app import db


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    ucc = db.Column(db.String(50), unique=True, nullable=False, index=True)  # Kotak UCC
    mobile_number = db.Column(db.String(15), nullable=False)
    greeting_name = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.String(50), nullable=True)  # Kotak user ID
    client_code = db.Column(db.String(50), nullable=True)
    product_code = db.Column(db.String(50), nullable=True)
    account_type = db.Column(db.String(50), nullable=True)
    branch_code = db.Column(db.String(50), nullable=True)
    is_trial_account = db.Column(db.Boolean, default=False)
    
    # Session management
    access_token = db.Column(db.Text, nullable=True)
    session_token = db.Column(db.Text, nullable=True)
    sid = db.Column(db.String(100), nullable=True)
    rid = db.Column(db.String(100), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    last_login = db.Column(db.DateTime, nullable=True)
    session_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<User {self.ucc}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'ucc': self.ucc,
            'mobile_number': self.mobile_number,
            'greeting_name': self.greeting_name,
            'user_id': self.user_id,
            'client_code': self.client_code,
            'product_code': self.product_code,
            'account_type': self.account_type,
            'branch_code': self.branch_code,
            'is_trial_account': self.is_trial_account,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Session tokens
    access_token = db.Column(db.Text, nullable=True)
    session_token = db.Column(db.Text, nullable=True)
    sid = db.Column(db.String(100), nullable=True)
    rid = db.Column(db.String(100), nullable=True)
    
    # Store complete login response
    login_response = db.Column(db.Text, nullable=True)  # Store full login response as JSON
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'


class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Trading preferences
    default_exchange = db.Column(db.String(10), nullable=True)
    default_product_type = db.Column(db.String(20), nullable=True)
    default_order_type = db.Column(db.String(20), nullable=True)
    
    # UI preferences
    auto_refresh_interval = db.Column(db.Integer, default=30)  # seconds
    show_notifications = db.Column(db.Boolean, default=True)
    theme = db.Column(db.String(20), default='dark')
    
    # Alert preferences
    email_alerts = db.Column(db.Boolean, default=False)
    sms_alerts = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relationship
    user = db.relationship('User', backref=db.backref('preferences', uselist=False))
    
    def __repr__(self):
        return f'<UserPreferences for User {self.user_id}>'