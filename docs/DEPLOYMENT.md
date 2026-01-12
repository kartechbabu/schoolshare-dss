# DSS App Deployment Guide

Deploy the SchoolShare Decision Support System to Digital Ocean.

**Live URL:** https://schoolsharedss.org

**Related Documentation:**
- [Domain Setup](DOMAIN_SETUP.md) - DNS and Nginx reverse proxy configuration

## Prerequisites

- Digital Ocean account with a Droplet (Ubuntu recommended)
- Docker installed on the Droplet
- SSH access to the Droplet
- Local copy of the DSS app code

## Quick Start

```bash
# 1. Copy code to droplet
scp -r app_maps_v2.py Dockerfile docker-compose.yml requirements.txt src/ .streamlit/ root@YOUR_DROPLET_IP:/opt/dss-app/

# 2. Copy data to droplet
scp -r data/ root@YOUR_DROPLET_IP:/opt/dss-app/

# 3. Copy census shapefile
ssh root@YOUR_DROPLET_IP "mkdir -p /opt/dss-app/data/census"
scp /path/to/cbg_shapes_2020.gpkg root@YOUR_DROPLET_IP:/opt/dss-app/data/census/

# 4. Build and run on droplet
ssh root@YOUR_DROPLET_IP
cd /opt/dss-app
docker build -t dss-app .
docker run -d -p 8501:8501 -v $(pwd)/data:/app/data:ro --name dss-app --restart unless-stopped dss-app
```

App available at: `http://YOUR_DROPLET_IP:8501`

---

## Detailed Steps

### Step 1: Prepare Local Environment

Ensure you have the following files in your `dss-app2` directory:

```
dss-app2/
├── app_maps_v2.py          # Main Streamlit app
├── Dockerfile              # Docker build config
├── docker-compose.yml      # Docker Compose config
├── requirements.txt        # Python dependencies
├── .streamlit/             # Streamlit config
│   └── config.toml
├── src/                    # Source modules
│   ├── config.py           # Path configuration
│   └── utils/
│       ├── choropleth_map.py
│       ├── csv_data_loader.py
│       ├── map_visualization.py
│       └── simple_map.py
└── data/                   # Data files (not in git)
    ├── processed/          # School/hospital pickles
    ├── raw/                # Optimization results
    │   ├── result_arts_250425/
    │   └── result_hospital_250507/
    └── census/             # CBG shapefiles
        └── cbg_shapes_2020.gpkg
```

### Step 2: Set Up Droplet

SSH into your droplet:

```bash
ssh root@YOUR_DROPLET_IP
```

Install Docker if not already installed:

```bash
apt-get update
apt-get install -y docker.io docker-compose
systemctl enable docker
systemctl start docker
```

Create app directory:

```bash
mkdir -p /opt/dss-app
```

### Step 3: Transfer Code Files

From your **local machine**, copy the application code:

```bash
cd /path/to/dss-app2

scp -r app_maps_v2.py Dockerfile docker-compose.yml requirements.txt src/ .streamlit/ root@YOUR_DROPLET_IP:/opt/dss-app/
```

### Step 4: Transfer Data Files

Copy the data directory (~400MB):

```bash
scp -r data/ root@YOUR_DROPLET_IP:/opt/dss-app/
```

Copy the census shapefile (~200MB) if not included in data/:

```bash
ssh root@YOUR_DROPLET_IP "mkdir -p /opt/dss-app/data/census"

scp /path/to/census_M3/data_infra_bias/cbg_shapes_2020.gpkg root@YOUR_DROPLET_IP:/opt/dss-app/data/census/
```

### Step 5: Build Docker Image

On the **droplet**:

```bash
cd /opt/dss-app
docker build -t dss-app .
```

This takes 3-5 minutes (installs geospatial dependencies).

### Step 6: Run the Container

```bash
docker run -d -p 8501:8501 \
  -v $(pwd)/data:/app/data:ro \
  --name dss-app \
  --restart unless-stopped \
  dss-app
```

Verify it's running:

```bash
docker ps
docker logs dss-app
```

### Step 7: Access the App

Open in browser: `http://YOUR_DROPLET_IP:8501`

---

## Data Directory Structure

The app expects this structure inside `/opt/dss-app/data/`:

```
data/
├── processed/
│   ├── HS_gdf_meters_clipped_48.pkl    # Texas schools
│   ├── HO_gdf_meters_clipped_48.pkl    # Texas hospitals
│   └── ... (other states)
├── raw/
│   ├── result_arts_250425/
│   │   ├── TX_48_result_dist_*.csv
│   │   └── coverages/
│   │       └── TX_48_coverage_mindist_numfacility_*.csv
│   └── result_hospital_250507/
│       └── coverages/
│           └── TX_48_coverage_mindist_numfacility_*.csv
└── census/
    └── cbg_shapes_2020.gpkg            # ~200MB CBG geometries
```

---

## Managing the Container

### View logs
```bash
docker logs dss-app
docker logs -f dss-app  # follow logs
```

### Restart container
```bash
docker restart dss-app
```

### Stop container
```bash
docker stop dss-app
```

### Remove and rebuild
```bash
docker stop dss-app
docker rm dss-app
docker build -t dss-app .
docker run -d -p 8501:8501 -v $(pwd)/data:/app/data:ro --name dss-app --restart unless-stopped dss-app
```

### Update code and redeploy

**Step 1: Copy updated files from local machine**

```bash
# Update main app file only
scp app_maps_v2.py root@YOUR_DROPLET_IP:/opt/dss-app/

# Or update multiple files (app + modules)
scp -r app_maps_v2.py src/ root@YOUR_DROPLET_IP:/opt/dss-app/

# Or update everything except data
scp -r app_maps_v2.py Dockerfile docker-compose.yml requirements.txt src/ .streamlit/ root@YOUR_DROPLET_IP:/opt/dss-app/
```

**Step 2: Rebuild and restart container on droplet**

```bash
ssh root@YOUR_DROPLET_IP "cd /opt/dss-app && docker stop dss-app && docker rm dss-app && docker build -t dss-app . && docker run -d -p 8501:8501 -v \$(pwd)/data:/app/data:ro --name dss-app --restart unless-stopped dss-app"
```

**One-liner (copy + rebuild)**

```bash
scp app_maps_v2.py root@YOUR_DROPLET_IP:/opt/dss-app/ && ssh root@YOUR_DROPLET_IP "cd /opt/dss-app && docker stop dss-app && docker rm dss-app && docker build -t dss-app . && docker run -d -p 8501:8501 -v \$(pwd)/data:/app/data:ro --name dss-app --restart unless-stopped dss-app"
```

---

## Environment Variables

The app uses these environment variables (set in Dockerfile):

| Variable | Default | Description |
|----------|---------|-------------|
| `DSS_BASE_PATH` | `/app` | Base application path |
| `DSS_DATA_PATH` | `/app/data` | Data directory |
| `DSS_CENSUS_PATH` | `/app/data/census` | CBG shapefile location |
| `DSS_PROCESSED_PATH` | `/app/data/processed` | Processed pickle files |

To override, add `-e` flags to docker run:

```bash
docker run -d -p 8501:8501 \
  -v $(pwd)/data:/app/data:ro \
  -e DSS_CENSUS_PATH=/app/data/census \
  --name dss-app \
  dss-app
```

---

## Troubleshooting

### App shows placeholder data (500 schools instead of 2,174)

**Cause**: Data volume not mounted correctly.

**Fix**: Ensure you run docker from `/opt/dss-app/` (not a subdirectory):

```bash
cd /opt/dss-app
docker run -d -p 8501:8501 -v $(pwd)/data:/app/data:ro --name dss-app dss-app
```

### Container exits immediately

**Check logs**:
```bash
docker logs dss-app
```

**Common causes**:
- Missing Python dependencies → rebuild image
- Missing data files → check data/ directory structure

### Port 8501 already in use

```bash
# Find what's using port
lsof -i :8501

# Or use different port
docker run -d -p 8502:8501 --name dss-app dss-app
```

### Map doesn't show choropleth

**Cause**: Missing `cbg_shapes_2020.gpkg` file.

**Fix**: Copy census shapefile:
```bash
scp cbg_shapes_2020.gpkg root@YOUR_DROPLET_IP:/opt/dss-app/data/census/
docker restart dss-app
```

---

## Optional: Set Up Domain & SSL

### Using nginx reverse proxy

If you have nginx on the droplet:

```nginx
# /etc/nginx/sites-available/dss
server {
    listen 80;
    server_name dss.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

Enable and get SSL:

```bash
ln -s /etc/nginx/sites-available/dss /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
certbot --nginx -d dss.yourdomain.com
```

---

## File Sizes Reference

| Item | Size |
|------|------|
| Docker image | ~1.5GB |
| `data/processed/` | ~61MB |
| `data/raw/result_arts_*/` | ~155MB |
| `data/raw/result_hospital_*/` | ~154MB |
| `cbg_shapes_2020.gpkg` | ~200MB |
| **Total data** | **~600MB** |

---

## Future Improvements (TBD)

### GitHub Actions for Automated Deployment

Set up CI/CD pipeline to automatically deploy on push to main:

- [ ] Create `.github/workflows/deploy.yml`
- [ ] Add SSH key as GitHub secret
- [ ] Auto-build Docker image on push
- [ ] Auto-deploy to droplet
- [ ] Add health check verification
- [ ] Slack/email notification on deploy

Example workflow structure:
```yaml
# .github/workflows/deploy.yml
name: Deploy to Digital Ocean
on:
  push:
    branches: [main]
    paths:
      - 'optimization_M3_Dropbox/dss-app2/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Droplet
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DROPLET_IP }}
          username: root
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/dss-app
            git pull origin main
            docker build -t dss-app .
            docker stop dss-app || true
            docker rm dss-app || true
            docker run -d -p 8501:8501 -v $(pwd)/data:/app/data:ro --name dss-app --restart unless-stopped dss-app
```

---

## Deployment Checklist

- [ ] Droplet has Docker installed
- [ ] Created `/opt/dss-app/` directory
- [ ] Copied app code (app_maps_v2.py, Dockerfile, src/, etc.)
- [ ] Copied data/processed/ (school/hospital pickles)
- [ ] Copied data/raw/result_arts_*/ (coverage CSVs)
- [ ] Copied data/raw/result_hospital_*/ (coverage CSVs)
- [ ] Copied data/census/cbg_shapes_2020.gpkg
- [ ] Built Docker image
- [ ] Container running on port 8501
- [ ] App accessible at http://DROPLET_IP:8501
- [ ] State Statistics shows real data (not placeholders)
