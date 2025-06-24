# Render Deployment Guide for Kotak Neo Trading Application

## Quick Deployment Steps

### 1. Create Render Account
- Go to [render.com](https://render.com) and sign up
- Connect your GitHub repository

### 2. Deploy Database First
1. Click "New" → "PostgreSQL"
2. Name: `kotak-trading-db`
3. Database Name: `kotak_trading_db`
4. User: `kotak_trading_user`
5. Region: Choose closest to your users
6. Plan: Starter (free tier available)

### 3. Deploy Web Service
1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure settings:
   - **Name**: `kotak-neo-trading`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 main:app`
   - **Plan**: Starter (free tier available)

### 4. Environment Variables
Add these environment variables in Render dashboard:

**Required:**
- `DATABASE_URL`: (Auto-filled from database connection)
- `SESSION_SECRET`: Generate a secure random string (32+ characters)
- `ENVIRONMENT`: `production`

**Optional:**
- `DEMO_MODE`: `false` (for production)
- `PYTHON_VERSION`: `3.11.10`

**Example SESSION_SECRET generation:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Health Check
- Set Health Check Path to: `/health`
- This ensures Render can monitor your app

## Automatic Deployment
The `render.yaml` file enables Infrastructure as Code deployment:

```bash
# Deploy using Render Blueprint
1. Push render.yaml to your repository
2. In Render dashboard, create "Blueprint"
3. Connect to your repository
4. Render will automatically create database and web service
```

## Production Configuration

### Database Migration
The app automatically creates tables on startup:
```python
with app.app_context():
    db.create_all()
```

### Security Settings
- HTTPS enforced by default on Render
- Session cookies configured for production
- CORS headers properly set
- X-Frame-Options removed for iframe compatibility

### Scaling
- Starter plan: 512MB RAM, shared CPU
- Upgrade to Standard for dedicated resources
- Auto-scaling available on higher plans

## Custom Domain (Optional)
1. In Render dashboard, go to your web service
2. Click "Settings" → "Custom Domains"
3. Add your domain and configure DNS

## Monitoring
- Built-in logs and metrics in Render dashboard
- Health check endpoint: `/health`
- Application status: `/test`

## Troubleshooting

### Common Issues:
1. **Build failures**: Check requirements.txt compatibility
2. **Database connection**: Verify DATABASE_URL environment variable
3. **Memory issues**: Upgrade to Standard plan if needed

### Debug Commands:
```bash
# Check logs
render logs <service-name>

# Access shell (paid plans only)
render shell <service-name>
```

## Cost Estimation
- **Free Tier**: Database + Web Service (with limitations)
- **Starter Plan**: ~$7/month for database + web service
- **Production Plan**: ~$25/month for enhanced performance

## Alternative Deployment Options

### Docker Deployment
Use the included Dockerfile and docker-compose.yml:
```bash
# Local testing
docker-compose up --build

# Production deployment
docker build -t kotak-neo-trading .
docker run -p 5000:5000 --env-file .env kotak-neo-trading
```

### Manual Server Deployment
```bash
# Clone repository
git clone <your-repo-url>
cd kotak-neo-trading

# Install dependencies
pip install -r render_requirements.txt

# Set environment variables
export DATABASE_URL="your-database-url"
export SESSION_SECRET="your-secret-key"
export ENVIRONMENT="production"

# Run application
gunicorn --bind 0.0.0.0:5000 --workers 2 main_render:app
```

## Support
- Render Documentation: [render.com/docs](https://render.com/docs)
- Community: [community.render.com](https://community.render.com)
- Docker Documentation: [docs.docker.com](https://docs.docker.com)