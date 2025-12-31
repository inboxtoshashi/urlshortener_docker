# EC2 Deployment Guide

## Prerequisites
- EC2 instance with Docker and Docker Compose installed
- Security group with ports 80 (or 9090) open
- Git installed

## Deployment Steps

### 1. Clone Repository on EC2
```bash
git clone <your-repo-url>
cd urlshortener_docker
```

### 2. Configure Public URL
Edit the `.env` file and update `PUBLIC_URL` with your EC2 public IP or domain:

```bash
# For EC2 public IP
PUBLIC_URL=http://YOUR_EC2_PUBLIC_IP:9090

# For domain name
PUBLIC_URL=http://yourdomain.com

# For HTTPS with domain
PUBLIC_URL=https://yourdomain.com
```

### 3. Update Security Configuration (Optional)
For production, update passwords in `.env`:
```bash
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_PASSWORD=your_secure_app_password
```

### 4. Deploy Application
```bash
docker-compose -f urlShortner.yml build
docker-compose -f urlShortner.yml up -d
```

### 5. Verify Deployment
```bash
# Check container status
docker ps

# Test health endpoints
curl http://localhost:5001/health  # Backend
curl http://localhost:9090/health  # Frontend

# Test application
curl -X POST -d "url=https://google.com" http://localhost:9090/
```

### 7. Access Application
- Open browser: `http://YOUR_EC2_PUBLIC_IP:9090`
- All generated short URLs will automatically use your EC2 IP

## Port Configuration

### Default Ports
- Frontend: 9090 → 80 (Nginx)
- Backend: 5001 (Flask)
- Database: 3306 (MySQL)
- Metrics: 9100 (Prometheus)

### To Use Port 80 (Standard HTTP)
Edit `docker-compose.yml`:
```yaml
frontend:
  ports:
    - "80:80"  # Change from 9090:80
```

And update `.env`:
```bash
PUBLIC_URL=http://YOUR_EC2_PUBLIC_IP
```

## Security Group Configuration

### Required Inbound Rules
| Type | Protocol | Port | Source |
|------|----------|------|--------|
| HTTP | TCP | 9090 | 0.0.0.0/0 |
| Custom | TCP | 5001 | 0.0.0.0/0 (or restrict) |
| MySQL | TCP | 3306 | Localhost only |

For port 80:
| Type | Protocol | Port | Source |
|------|----------|------|--------|
| HTTP | TCP | 80 | 0.0.0.0/0 |

## Automatic Updates on EC2

The application will automatically:
- ✅ Use EC2's public IP in generated URLs
- ✅ Work with domain names if configured
- ✅ Handle HTTP/HTTPS based on PUBLIC_URL setting
- ✅ Adapt to the request hostname if PUBLIC_URL is not set

## Monitoring

- **Prometheus Metrics**: `http://YOUR_EC2_IP:9100/metrics`
- **Backend Health**: `http://YOUR_EC2_IP:5001/health`
- **Frontend Health**: `http://YOUR_EC2_IP:9090/health`

## Troubleshooting

### Check Logs
```bash
docker logs url-shortener-backend
docker logs url-shortener-frontend
docker logs mysql-db
```

### Restart Services
```bash
docker-compose -f urlShortner.yml restart
```

### Clean Restart
```bash
docker-compose -f urlShortner.yml down
docker-compose -f urlShortner.yml up -d
```

### Check Environment Variables
```bash
docker exec url-shortener-backend env | grep PUBLIC_URL
```
