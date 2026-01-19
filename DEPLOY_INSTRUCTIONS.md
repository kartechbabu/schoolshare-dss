# Deployment Instructions

**Server:** 164.92.92.181 (Digital Ocean)
**Live URL:** http://schoolsharedss.org

---

## Initial Setup (First Time Only)

Run these commands on the server to transition from old SCP-based deployment to git-based:

```bash
ssh root@164.92.92.181

# Stop current container
docker stop dss-app

# Move data out temporarily
mv /opt/dss-app/data /opt/dss-data-temp

# Remove old code
rm -rf /opt/dss-app

# Clone new repo
git clone https://github.com/kartechbabu/schoolshare-dss.git /opt/dss-app

# Move data back
mv /opt/dss-data-temp /opt/dss-app/data

# Make deploy script executable
chmod +x /opt/dss-app/scripts/deploy.sh

# Deploy
cd /opt/dss-app
./scripts/deploy.sh
```

---

## Future Deployments

### Code-only updates

**Step 1: Push changes (local machine)**
```bash
cd /Users/46773437/Dropbox/Data/01_research/public_repositories/schoolshare-dss
git add .
git commit -m "Your change description"
git push
```

**Step 2: Deploy on server**
```bash
ssh root@164.92.92.181 "cd /opt/dss-app && ./scripts/deploy.sh"
```

### Data-only updates

No rebuild needed - data is mounted as a volume.

```bash
cd /Users/46773437/Dropbox/Data/01_research/public_repositories/schoolshare-dss

# Sync all data
rsync -avz --progress data/ root@164.92.92.181:/opt/dss-app/data/

# Or sync specific folders
scp -r data/raw/result_arts_250425/ root@164.92.92.181:/opt/dss-app/data/raw/
scp -r data/processed/ root@164.92.92.181:/opt/dss-app/data/processed/
```

### Code + Data updates

```bash
cd /Users/46773437/Dropbox/Data/01_research/public_repositories/schoolshare-dss

# Push code
git add . && git commit -m "Update" && git push

# Sync data
rsync -avz --progress data/ root@164.92.92.181:/opt/dss-app/data/

# Deploy
ssh root@164.92.92.181 "cd /opt/dss-app && ./scripts/deploy.sh"
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Deploy code | `ssh root@164.92.92.181 "cd /opt/dss-app && ./scripts/deploy.sh"` |
| Sync data | `rsync -avz --progress data/ root@164.92.92.181:/opt/dss-app/data/` |
| Check status | `ssh root@164.92.92.181 "docker ps \| grep dss"` |
| View logs | `ssh root@164.92.92.181 "docker logs dss-app --tail 50"` |
| Restart app | `ssh root@164.92.92.181 "docker restart dss-app"` |

---

## Troubleshooting

**App not loading?**
```bash
ssh root@164.92.92.181
docker logs dss-app --tail 100
```

**Health check failing?**
```bash
ssh root@164.92.92.181
curl http://localhost:8501/_stcore/health
```

**Rebuild from scratch?**
```bash
ssh root@164.92.92.181
cd /opt/dss-app
docker stop dss-app && docker rm dss-app
docker build --no-cache -t dss-app .
docker run -d -p 8501:8501 -v $(pwd)/data:/app/data:ro --name dss-app --restart unless-stopped dss-app
```
