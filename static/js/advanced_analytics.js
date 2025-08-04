/**
 * Advanced Analytics Manager for Trading Signals
 * Handles time series analysis and percentage change visualizations using real data
 */
function AdvancedAnalyticsManager() {
    var self = this;
    
    // Chart configurations for dark theme
    this.darkThemeLayout = {
        paper_bgcolor: '#343a40',
        plot_bgcolor: '#495057',
        font: { color: '#ffffff', size: 12 },
        xaxis: { 
            gridcolor: '#6c757d',
            linecolor: '#6c757d',
            tickcolor: '#6c757d'
        },
        yaxis: { 
            gridcolor: '#6c757d',
            linecolor: '#6c757d',
            tickcolor: '#6c757d'
        },
        margin: { l: 50, r: 50, t: 50, b: 50 }
    };
    
    // Chart data storage
    this.timeSeriesData = null;
    this.percentageData = null;
    
    // Initialize when DOM is ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function() {
            self.init();
        });
    } else {
        this.init();
    }
}

AdvancedAnalyticsManager.prototype.init = function() {
    console.log("Advanced Analytics Manager initialized");
    this.loadAnalyticsData();
};

AdvancedAnalyticsManager.prototype.loadAnalyticsData = function() {
    var self = this;
    
    // Show loading states for both charts
    self.showChartLoading('timeSeriesChart', 'Loading time series data...');
    self.showChartLoading('percentageChangeChart', 'Loading multi-period performance data...');
    
    // Load time series data
    this.fetchTimeSeriesData()
        .then(function(data) {
            self.timeSeriesData = data;
            self.renderTimeSeriesChart();
        })
        .catch(function(error) {
            console.error('Error loading time series data:', error);
            self.showChartError('timeSeriesChart', 'Failed to load time series data');
        });
    
    // Load percentage analysis data
    this.fetchPercentageAnalysisData()
        .then(function(data) {
            self.percentageData = data;
            self.renderPercentageChart();
            self.updateTrendInsights(data.insights);
        })
        .catch(function(error) {
            console.error('Error loading percentage analysis data:', error);
            self.showChartError('percentageChangeChart', 'Failed to load percentage analysis data');
        });
};

AdvancedAnalyticsManager.prototype.fetchTimeSeriesData = function() {
    return fetch('/api/analytics/time-series')
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(function(data) {
            if (!data.success) {
                throw new Error(data.error || 'API returned error');
            }
            return data;
        });
};

AdvancedAnalyticsManager.prototype.fetchPercentageAnalysisData = function() {
    return fetch('/api/analytics/percentage-analysis')
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(function(data) {
            if (!data.success) {
                throw new Error(data.error || 'API returned error');
            }
            return data;
        });
};

AdvancedAnalyticsManager.prototype.renderTimeSeriesChart = function() {
    if (!this.timeSeriesData || !this.timeSeriesData.data) {
        this.showChartError('timeSeriesChart', 'No time series data available');
        return;
    }
    
    // Clear any existing loading state
    var chartDiv = document.getElementById('timeSeriesChart');
    if (chartDiv) {
        chartDiv.innerHTML = '';
    }
    
    var data = this.timeSeriesData.data;
    
    // Group data by date for better visualization
    var dateGroups = {};
    data.forEach(function(item) {
        var date = item.date;
        if (!dateGroups[date]) {
            dateGroups[date] = [];
        }
        dateGroups[date].push(item);
    });
    
    // Calculate average performance per date
    var dates = [];
    var performances = [];
    var cplValues = [];
    
    Object.keys(dateGroups).sort().forEach(function(date) {
        var dayData = dateGroups[date];
        var avgPerformance = dayData.reduce(function(sum, item) {
            return sum + (item.performance || 0);
        }, 0) / dayData.length;
        
        var avgCpl = dayData.reduce(function(sum, item) {
            return sum + (item.cpl || 0);
        }, 0) / dayData.length;
        
        dates.push(date);
        performances.push(avgPerformance);
        cplValues.push(avgCpl);
    });
    
    var traces = [
        {
            x: dates,
            y: performances,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Average % Change',
            line: { color: '#17a2b8', width: 3 },
            marker: { size: 8, color: '#17a2b8' },
            hovertemplate: '<b>Date:</b> %{x}<br><b>Avg Performance:</b> %{y:.2f}%<extra></extra>'
        },
        {
            x: dates,
            y: cplValues,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Average P&L',
            yaxis: 'y2',
            line: { color: '#28a745', width: 2 },
            marker: { size: 6, color: '#28a745' },
            hovertemplate: '<b>Date:</b> %{x}<br><b>Avg P&L:</b> ₹%{y:.2f}<extra></extra>'
        }
    ];
    
    var layout = Object.assign({}, this.darkThemeLayout, {
        title: {
            text: 'Time Series Analysis: Entry Date vs Performance',
            font: { color: '#ffffff', size: 16 }
        },
        xaxis: Object.assign({}, this.darkThemeLayout.xaxis, {
            title: 'Entry Date',
            type: 'category'
        }),
        yaxis: Object.assign({}, this.darkThemeLayout.yaxis, {
            title: 'Average % Change',
            ticksuffix: '%'
        }),
        yaxis2: {
            title: 'Average P&L (₹)',
            overlaying: 'y',
            side: 'right',
            gridcolor: '#6c757d',
            linecolor: '#6c757d',
            tickcolor: '#6c757d'
        },
        hovermode: 'x unified',
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.2,
            x: 0.5,
            xanchor: 'center'
        }
    });
    
    var config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false
    };
    
    Plotly.newPlot('timeSeriesChart', traces, layout, config);
};

AdvancedAnalyticsManager.prototype.renderPercentageChart = function() {
    if (!this.percentageData || !this.percentageData.data) {
        this.showChartError('percentageChangeChart', 'No percentage analysis data available');
        return;
    }
    
    // Clear any existing loading state
    var chartDiv = document.getElementById('percentageChangeChart');
    if (chartDiv) {
        chartDiv.innerHTML = '';
    }
    
    var data = this.percentageData.data;
    
    // Prepare data for grouped bar chart
    var symbols = data.map(function(item) { return item.symbol; });
    var perf7d = data.map(function(item) { return item.perf_7d; });
    var perf30d = data.map(function(item) { return item.perf_30d; });
    var perf90d = data.map(function(item) { return item.perf_90d; });
    
    // Color function based on performance
    function getColor(value) {
        if (value > 5) return '#28a745'; // Strong green for good performance
        if (value > 0) return '#20c997'; // Light green for positive
        if (value > -5) return '#ffc107'; // Yellow for slight negative
        return '#dc3545'; // Red for poor performance
    }
    
    var traces = [
        {
            x: symbols,
            y: perf7d,
            type: 'bar',
            name: '7 Days %',
            marker: {
                color: perf7d.map(getColor),
                line: { color: '#ffffff', width: 1 }
            },
            hovertemplate: '<b>%{x}</b><br>7D Performance: %{y:.2f}%<extra></extra>'
        },
        {
            x: symbols,
            y: perf30d,
            type: 'bar',
            name: '30 Days %',
            marker: {
                color: perf30d.map(getColor),
                opacity: 0.8,
                line: { color: '#ffffff', width: 1 }
            },
            hovertemplate: '<b>%{x}</b><br>30D Performance: %{y:.2f}%<extra></extra>'
        },
        {
            x: symbols,
            y: perf90d,
            type: 'bar',
            name: '90 Days %',
            marker: {
                color: perf90d.map(getColor),
                opacity: 0.6,
                line: { color: '#ffffff', width: 1 }
            },
            hovertemplate: '<b>%{x}</b><br>90D Performance: %{y:.2f}%<extra></extra>'
        }
    ];
    
    var layout = Object.assign({}, this.darkThemeLayout, {
        title: {
            text: 'Multi-Period Performance Analysis (7D, 30D, 90D)',
            font: { color: '#ffffff', size: 16 }
        },
        xaxis: Object.assign({}, this.darkThemeLayout.xaxis, {
            title: 'Stock Symbols',
            tickangle: -45
        }),
        yaxis: Object.assign({}, this.darkThemeLayout.yaxis, {
            title: 'Performance (%)',
            ticksuffix: '%',
            zeroline: true,
            zerolinecolor: '#ffffff',
            zerolinewidth: 2
        }),
        barmode: 'group',
        bargap: 0.15,
        bargroupgap: 0.1,
        hovermode: 'closest',
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.3,
            x: 0.5,
            xanchor: 'center'
        }
    });
    
    var config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
        displaylogo: false
    };
    
    Plotly.newPlot('percentageChangeChart', traces, layout, config);
};

AdvancedAnalyticsManager.prototype.updateTrendInsights = function(insights) {
    if (!insights) return;
    
    var trendContainer = document.getElementById('trendInsights');
    if (!trendContainer) return;
    
    var html = '';
    
    // Consistent winners
    if (insights.consistent_winners && insights.consistent_winners.length > 0) {
        html += '<div class="trend-item mb-2">';
        html += '<span class="badge bg-success me-2">★ Consistent Winners</span>';
        html += '<small class="text-success">' + insights.consistent_winners.slice(0, 3).join(', ');
        if (insights.consistent_winners.length > 3) {
            html += ' +' + (insights.consistent_winners.length - 3) + ' more';
        }
        html += '</small>';
        html += '</div>';
    }
    
    // Declining stocks
    if (insights.declining_stocks && insights.declining_stocks.length > 0) {
        html += '<div class="trend-item mb-2">';
        html += '<span class="badge bg-danger me-2">↓ Declining</span>';
        html += '<small class="text-danger">' + insights.declining_stocks.slice(0, 3).join(', ');
        if (insights.declining_stocks.length > 3) {
            html += ' +' + (insights.declining_stocks.length - 3) + ' more';
        }
        html += '</small>';
        html += '</div>';
    }
    
    // Volatile stocks
    if (insights.volatile_stocks && insights.volatile_stocks.length > 0) {
        html += '<div class="trend-item mb-2">';
        html += '<span class="badge bg-warning me-2">⚡ Volatile</span>';
        html += '<small class="text-warning">' + insights.volatile_stocks.slice(0, 3).join(', ');
        if (insights.volatile_stocks.length > 3) {
            html += ' +' + (insights.volatile_stocks.length - 3) + ' more';
        }
        html += '</small>';
        html += '</div>';
    }
    
    // Stable performers
    if (insights.stable_performers && insights.stable_performers.length > 0) {
        html += '<div class="trend-item">';
        html += '<span class="badge bg-info me-2">➤ Stable</span>';
        html += '<small class="text-info">' + insights.stable_performers.slice(0, 3).join(', ');
        if (insights.stable_performers.length > 3) {
            html += ' +' + (insights.stable_performers.length - 3) + ' more';
        }
        html += '</small>';
        html += '</div>';
    }
    
    if (html === '') {
        html = '<small class="text-muted">No trend patterns detected</small>';
    }
    
    trendContainer.innerHTML = html;
};

// Helper functions for chart states
AdvancedAnalyticsManager.prototype.showChartLoading = function(chartId, message) {
    var chartDiv = document.getElementById(chartId);
    if (chartDiv) {
        chartDiv.innerHTML = '<div class="d-flex justify-content-center align-items-center h-100">' +
            '<div class="text-center text-muted">' +
            '<i class="fas fa-spinner fa-spin fa-3x mb-3"></i>' +
            '<p>' + message + '</p>' +
            '</div>' +
            '</div>';
    }
};

AdvancedAnalyticsManager.prototype.showChartError = function(containerId, message) {
    var container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '<div class="text-center text-danger p-4">' +
            '<i class="fas fa-exclamation-triangle fa-2x mb-3"></i>' +
            '<br><span>' + message + '</span>' +
            '<br><small class="text-muted">Check console for details</small>' +
            '</div>';
    }
};

// Initialize Advanced Analytics Manager
var advancedAnalytics = new AdvancedAnalyticsManager();

// Export for global access if needed
window.AdvancedAnalyticsManager = AdvancedAnalyticsManager;