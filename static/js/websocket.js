// WebSocket handler for real-time market data feeds - Kotak Neo Trading App

function WebSocketHandler() {
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.heartbeatInterval = null;
    this.subscriptions = {};
    this.messageHandlers = {};
    this.init();
}

WebSocketHandler.prototype.init = function() {
    this.setupMessageHandlers();
    console.log('WebSocket Handler initialized');
};

WebSocketHandler.prototype.setupMessageHandlers = function() {
    // Register message handlers for different data types
    this.messageHandlers['quote'] = this.handleQuoteUpdate.bind(this);
    this.messageHandlers['depth'] = this.handleDepthUpdate.bind(this);
    this.messageHandlers['order'] = this.handleOrderUpdate.bind(this);
    this.messageHandlers['position'] = this.handlePositionUpdate.bind(this);
    this.messageHandlers['holding'] = this.handleHoldingUpdate.bind(this);
    this.messageHandlers['error'] = this.handleError.bind(this);
};

WebSocketHandler.prototype.connect = function() {
    try {
        console.log('Attempting to establish WebSocket connection...');
        this.simulateConnection();
    } catch (error) {
        console.error('WebSocket connection failed:', error);
        this.handleConnectionError();
    }
};

WebSocketHandler.prototype.simulateConnection = function() {
    var self = this;
    
    setTimeout(function() {
        self.isConnected = true;
        self.reconnectAttempts = 0;
        console.log('WebSocket connection established (simulated)');
        
        self.startHeartbeat();
        self.startDataSimulation();
    }, 1000);
};

WebSocketHandler.prototype.startHeartbeat = function() {
    var self = this;
    
    this.heartbeatInterval = setInterval(function() {
        if (self.isConnected) {
            console.log('WebSocket heartbeat');
        }
    }, 30000); // 30 seconds
};

WebSocketHandler.prototype.startDataSimulation = function() {
    var self = this;
    
    // Simulate periodic quote updates
    setInterval(function() {
        if (self.isConnected) {
            self.simulateQuoteUpdate();
        }
    }, 5000); // Every 5 seconds
};

WebSocketHandler.prototype.simulateQuoteUpdate = function() {
    var symbols = ['NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY'];
    var randomSymbol = symbols[Math.floor(Math.random() * symbols.length)];
    
    var mockQuote = {
        type: 'quote',
        symbol: randomSymbol,
        ltp: (Math.random() * 1000 + 100).toFixed(2),
        change: (Math.random() * 20 - 10).toFixed(2),
        change_percent: (Math.random() * 5 - 2.5).toFixed(2),
        volume: Math.floor(Math.random() * 100000),
        timestamp: new Date().toISOString()
    };
    
    this.handleMessage(mockQuote);
};

WebSocketHandler.prototype.handleMessage = function(message) {
    try {
        var handler = this.messageHandlers[message.type];
        if (handler) {
            handler(message);
        } else {
            console.warn('No handler for message type:', message.type);
        }
    } catch (error) {
        console.error('Error handling WebSocket message:', error);
    }
};

WebSocketHandler.prototype.handleQuoteUpdate = function(data) {
    // Update price displays on the page
    this.updatePriceElements(data);
    
    // Trigger custom event for other components
    var event = new CustomEvent('quoteUpdate', { detail: data });
    document.dispatchEvent(event);
};

WebSocketHandler.prototype.updatePriceElements = function(data) {
    var priceElements = document.querySelectorAll('[data-symbol="' + data.symbol + '"]');
    
    for (var i = 0; i < priceElements.length; i++) {
        var element = priceElements[i];
        
        if (element.classList.contains('price-ltp')) {
            element.textContent = '₹' + data.ltp;
            this.animatePriceChange(element, data.change);
        }
        
        if (element.classList.contains('price-change')) {
            element.textContent = data.change;
            element.className = 'price-change ' + (parseFloat(data.change) >= 0 ? 'text-success' : 'text-danger');
        }
        
        if (element.classList.contains('price-change-percent')) {
            element.textContent = data.change_percent + '%';
            element.className = 'price-change-percent ' + (parseFloat(data.change_percent) >= 0 ? 'text-success' : 'text-danger');
        }
    }
};

WebSocketHandler.prototype.animatePriceChange = function(element, change) {
    var changeValue = parseFloat(change);
    var animationClass = changeValue >= 0 ? 'price-up' : 'price-down';
    
    element.classList.add(animationClass);
    
    setTimeout(function() {
        element.classList.remove(animationClass);
    }, 1000);
};

WebSocketHandler.prototype.handleDepthUpdate = function(data) {
    console.log('Depth update received:', data);
    // Update market depth displays
};

WebSocketHandler.prototype.handleOrderUpdate = function(data) {
    console.log('Order update received:', data);
    // Update order status displays
    
    var event = new CustomEvent('orderUpdate', { detail: data });
    document.dispatchEvent(event);
};

WebSocketHandler.prototype.handlePositionUpdate = function(data) {
    console.log('Position update received:', data);
    // Update position displays
    
    var event = new CustomEvent('positionUpdate', { detail: data });
    document.dispatchEvent(event);
};

WebSocketHandler.prototype.handleHoldingUpdate = function(data) {
    console.log('Holding update received:', data);
    // Update holding displays
    
    var event = new CustomEvent('holdingUpdate', { detail: data });
    document.dispatchEvent(event);
};

WebSocketHandler.prototype.handleError = function(data) {
    console.error('WebSocket error:', data);
    this.showError('WebSocket Error: ' + (data.message || 'Unknown error'));
};

WebSocketHandler.prototype.showError = function(message) {
    var alertHtml = '<div class="alert alert-warning alert-dismissible fade show" role="alert">' +
        message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
        '</div>';
    
    var container = document.querySelector('.container, .container-fluid');
    if (container) {
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        setTimeout(function() {
            var alert = document.querySelector('.alert-warning');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
};

WebSocketHandler.prototype.subscribe = function(symbols) {
    if (!Array.isArray(symbols)) {
        symbols = [symbols];
    }
    
    for (var i = 0; i < symbols.length; i++) {
        this.subscriptions[symbols[i]] = true;
    }
    
    console.log('Subscribed to symbols:', symbols);
};

WebSocketHandler.prototype.unsubscribe = function(symbols) {
    if (!Array.isArray(symbols)) {
        symbols = [symbols];
    }
    
    for (var i = 0; i < symbols.length; i++) {
        delete this.subscriptions[symbols[i]];
    }
    
    console.log('Unsubscribed from symbols:', symbols);
};

WebSocketHandler.prototype.handleConnectionError = function() {
    this.isConnected = false;
    this.reconnectAttempts++;
    
    if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        var delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        console.log('Attempting to reconnect in ' + delay + 'ms (attempt ' + this.reconnectAttempts + ')');
        
        var self = this;
        setTimeout(function() {
            self.connect();
        }, delay);
    } else {
        console.error('Max reconnection attempts reached');
        this.showError('Connection lost. Please refresh the page to reconnect.');
    }
};

WebSocketHandler.prototype.disconnect = function() {
    this.isConnected = false;
    
    if (this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
    }
    
    if (this.ws) {
        this.ws.close();
        this.ws = null;
    }
    
    console.log('WebSocket disconnected');
};

WebSocketHandler.prototype.addPriceUpdateCSS = function() {
    var style = document.createElement('style');
    style.textContent = 
        '.price-up {' +
        '    animation: priceUp 1s ease-in-out;' +
        '}' +
        '.price-down {' +
        '    animation: priceDown 1s ease-in-out;' +
        '}' +
        '@keyframes priceUp {' +
        '    0% { background-color: rgba(40, 167, 69, 0.3); }' +
        '    50% { background-color: rgba(40, 167, 69, 0.1); }' +
        '    100% { background-color: transparent; }' +
        '}' +
        '@keyframes priceDown {' +
        '    0% { background-color: rgba(220, 53, 69, 0.3); }' +
        '    50% { background-color: rgba(220, 53, 69, 0.1); }' +
        '    100% { background-color: transparent; }' +
        '}';
    
    document.head.appendChild(style);
};

// Initialize WebSocket Handler when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.webSocketHandler === 'undefined') {
        window.webSocketHandler = new WebSocketHandler();
        window.webSocketHandler.addPriceUpdateCSS();
    }
});

// Fallback initialization
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    if (typeof window.webSocketHandler === 'undefined') {
        window.webSocketHandler = new WebSocketHandler();
        window.webSocketHandler.addPriceUpdateCSS();
    }
}