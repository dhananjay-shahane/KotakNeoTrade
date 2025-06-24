# Complete Render Deployment Guide for Kotak Neo Trading Platform

## 🚀 One-Click Deployment

### Method 1: Blueprint Deployment (Recommended)
1. Push your code to GitHub repository
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New" → "Blueprint"
4. Connect your GitHub repository
5. Render will automatically:
   - Create PostgreSQL database
   - Deploy web service
   - Set up environment variables
   - Configure health checks

### Method 2: Manual Deployment

#### Step 1: Create Database
1. In Render Dashboard: "New" → "PostgreSQL"
2. Settings:
   - **Name**: `kotak-trading-db`
   - **Database**: `kotak_trading_db`
   - **User**: `kotak_trading_user`
   - **Region**: Oregon (or closest to users)
   - **Plan**: Starter ($7/month) or Free tier

#### Step 2: Deploy Web Service
1. "New" → "Web Service"
2. Connect GitHub repository
3. Configuration:
   - **Name**: `kotak-neo-trading`
   - **Environment**: Python 3
   - **Build Command**: 
     ```bash
     pip install --upgrade pip && pip install -r render_requirements.txt
     ```
   - **Start Command**: 
     ```bash
     gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 main_render:app
     ```

#### Step 3: Environment Variables
Add these in Render dashboard:

| Variable | Value |
|----------|--------|
| `DATABASE_URL` | (Auto-filled from database) |
| `SESSION_SECRET` | Generate secure random string |
| `ENVIRONMENT` | `production` |
| `FLASK_ENV` | `production` |
| `DEMO_MODE` | `false` |

## 🔧 Production Configuration

### Database Schema
The application automatically creates these tables:
- `users` - User accounts and authentication
- `admin_trade_signals` - ETF trading signals
- `user_sessions` - Session management
- `user_preferences` - User settings
- `kotak_neo_quotes` - Market data
- `etf_signal_trades` - Trading positions
- `realtime_quotes` - Live market updates

### Performance Settings
- **Workers**: 2 (optimized for Starter plan)
- **Timeout**: 120 seconds
- **Max Requests**: 1000 per worker
- **Preload**: Enabled for faster startup

### Security Features
- HTTPS enforced by Render
- Session security configured
- CORS properly set for API access
- XSS protection enabled

## 🌐 Custom Domain Setup

1. In web service settings: "Custom Domains"
2. Add your domain (e.g., `trading.yourdomain.com`)
3. Configure DNS:
   ```
   CNAME trading yourdomain.onrender.com
   ```
4. SSL certificate automatically provisioned

## 📊 Monitoring & Logs

### Access Logs
```bash
# In Render dashboard
Service → Logs → View real-time logs
```

### Health Monitoring
- **Health Check**: `/health`
- **Render Health**: `/render-health`
- **Simple Test**: `/webview`

### Performance Metrics
- Response times
- Memory usage
- Database connections
- Error rates

## 💰 Cost Breakdown

### Free Tier
- Database: Limited (500MB storage)
- Web Service: Limited (750 hours/month)
- **Total**: Free

### Starter Plan
- Database: $7/month
- Web Service: $7/month
- **Total**: $14/month

### Production Plan
- Database: $20/month
- Web Service: $25/month
- **Total**: $45/month

## 🔧 Advanced Configuration

### Auto-Scaling
```yaml
# In render.yaml
plan: standard  # Enables auto-scaling
autoDeploy: true
```

### Environment-Specific Settings
```bash
# Development
DEMO_MODE=true
FLASK_DEBUG=True

# Production  
DEMO_MODE=false
FLASK_DEBUG=False
ENVIRONMENT=production
```

### Database Migrations
```python
# Automatic on deployment
with app.app_context():
    db.create_all()
```

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check `render_requirements.txt` compatibility
   - Verify Python version (3.11.10)

2. **Database Connection**
   - Ensure `DATABASE_URL` is set
   - Check database service status

3. **Memory Issues**
   - Upgrade to Standard plan
   - Optimize worker configuration

4. **Session Issues**
   - Check `SESSION_SECRET` is set
   - Verify cookie settings

### Debug Commands
```bash
# View logs
render logs <service-name>

# Check service status
render services list

# Manual deployment
render deploy <service-name>
```

## 📞 Support Resources

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Community**: [community.render.com](https://community.render.com)
- **Status**: [status.render.com](https://status.render.com)

## 🔄 Continuous Deployment

### GitHub Integration
- Automatic deployments on push to main branch
- Preview deployments for pull requests
- Rollback capability

### Deployment Process
1. Push code to GitHub
2. Render detects changes
3. Automatic build and deployment
4. Health checks verify deployment
5. Traffic switches to new version

## 📱 Post-Deployment Checklist

- [ ] Database tables created
- [ ] Health checks passing
- [ ] Custom domain configured (if needed)
- [ ] SSL certificate active
- [ ] Environment variables set
- [ ] Logs accessible
- [ ] Performance monitoring active
- [ ] Backup strategy implemented

Your Kotak Neo Trading platform is now ready for production use on Render!