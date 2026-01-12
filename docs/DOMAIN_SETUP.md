# schoolsharedss.org Domain Setup Documentation

## Overview
This document describes the steps taken to configure `schoolsharedss.org` to point to a Streamlit application running on a DigitalOcean Droplet.

**Server IP:** `164.92.92.181`
**Application:** Streamlit app running on port 8501
**Date:** December 16, 2025

---

## 1. Domain Nameserver Configuration (Squarespace)

The domain was registered with Squarespace. We updated the nameservers to use DigitalOcean's DNS:

1. Log into Squarespace → **Settings → Domains**
2. Click the domain name → **DNS** → **Domain Nameservers**
3. Click **Use Custom Nameservers**
4. Enter the following nameservers:
   - `ns1.digitalocean.com`
   - `ns2.digitalocean.com`
   - `ns3.digitalocean.com`
5. Save changes

**Note:** DNS propagation can take up to 48 hours (usually much faster).

---

## 2. DNS Records (DigitalOcean)

In the DigitalOcean control panel (**Networking → Domains → schoolsharedss.org**), the following records were configured:

| Type | Hostname | Value | TTL |
|------|----------|-------|-----|
| A | @ (schoolsharedss.org) | 164.92.92.181 | 3600 |
| A | www.schoolsharedss.org | 164.92.92.181 | 3600 |
| NS | schoolsharedss.org | ns1.digitalocean.com | 1800 |
| NS | schoolsharedss.org | ns2.digitalocean.com | 1800 |
| NS | schoolsharedss.org | ns3.digitalocean.com | 1800 |

---

## 3. Nginx Reverse Proxy Configuration

The Streamlit app runs on port 8501, but browsers expect port 80 (HTTP). An Nginx reverse proxy routes traffic from port 80 to the app.

### Existing Infrastructure
- Docker container `opt-tools-http_nginx_1` already running Nginx on port 80
- Nginx config mounted from host: `/opt/opt-tools/opt-tools-http/nginx/nginx.conf`

### Updated Nginx Configuration

**File location:** `/opt/opt-tools/opt-tools-http/nginx/nginx.conf`

```nginx
events {
    worker_connections 1024;
}
http {
    upstream api {
        server api:8000;
    }

    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_status 429;

    # Server for schoolsharedss.org - Streamlit app
    server {
        listen 80;
        server_name schoolsharedss.org www.schoolsharedss.org;

        location / {
            proxy_pass http://172.17.0.1:8501;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400;
        }
    }

    # Default server for Opt-Tools API (unchanged functionality)
    server {
        listen 80 default_server;
        server_name _;

        location / {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }
    }
}
```

### How It Works

| Request to... | Routes to... |
|---------------|--------------|
| `schoolsharedss.org` | Streamlit app (`172.17.0.1:8501`) |
| `www.schoolsharedss.org` | Streamlit app (`172.17.0.1:8501`) |
| Direct IP or any other domain | Opt-Tools API (unchanged) |

**Note:** `172.17.0.1` is the Docker bridge network gateway, allowing the Nginx container to reach the Streamlit app running on the host.

---

## 4. Useful Commands

### Verify DNS Nameservers
```bash
dig NS schoolsharedss.org +short
```
Or use: https://dnschecker.org/ns-lookup.php

### Check Nginx Configuration
```bash
docker exec opt-tools-http_nginx_1 nginx -t
```

### Reload Nginx (after config changes)
```bash
docker restart opt-tools-http_nginx_1
```

### View Nginx Logs
```bash
docker logs opt-tools-http_nginx_1 --tail 50
```

### Test Domain Routing Locally
```bash
curl -H "Host: schoolsharedss.org" http://localhost
```

### Check Running Containers
```bash
docker ps
```

### Check What's Using Port 80
```bash
sudo lsof -i :80
```

---

## 5. Docker Containers

| Container | Purpose | Ports |
|-----------|---------|-------|
| `dss-app` | Streamlit application | 8501 |
| `opt-tools-http_nginx_1` | Nginx reverse proxy | 80, 443 |
| `opt-tools-http_api_1` | Opt-Tools API | 8000 (internal) |
| `opt-tools-http_redis_1` | Redis cache | 6379 (internal) |

---

## 6. Future Improvements

### Add HTTPS (SSL/TLS)
To enable HTTPS with Let's Encrypt:

1. Install Certbot on the host
2. Obtain certificates for `schoolsharedss.org`
3. Update Nginx config to listen on port 443 with SSL
4. Redirect HTTP to HTTPS

---

## 7. Troubleshooting

### Site not loading?
1. Check DNS propagation: https://dnschecker.org
2. Verify Nginx is running: `docker ps | grep nginx`
3. Check Nginx logs: `docker logs opt-tools-http_nginx_1`
4. Test locally: `curl -H "Host: schoolsharedss.org" http://localhost`

### Nginx won't start?
1. Check config syntax: `docker exec opt-tools-http_nginx_1 nginx -t`
2. View error logs: `docker logs opt-tools-http_nginx_1`
3. Verify config file: `cat /opt/opt-tools/opt-tools-http/nginx/nginx.conf`

### Streamlit app not responding?
1. Check if container is running: `docker ps | grep dss`
2. Test directly: `curl http://localhost:8501`
3. View app logs: `docker logs dss-app`
