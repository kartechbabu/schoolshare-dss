# Deployment Instructions

**Server:** 164.92.92.181 (Digital Ocean)
**Live URL:** http://schoolsharedss.org

---

## ⚠️ READ FIRST — Production diverges from this repo (verified 2026-06-17)

The live server is **NOT** a git checkout. It was deployed by SCP and never converted
to the git-based flow below, so `./scripts/deploy.sh` and `git pull` **do not work** on
the server (`./scripts/deploy.sh: No such file or directory`).

What's actually running in `/opt/dss-app`:

| | **Production server** (`/opt/dss-app`) | **This git repo** |
|---|---|---|
| Source control | none (plain SCP'd files, no `.git`) | git / GitHub |
| Entrypoint | **`app_maps_v2.py`** | **`app.py`** (restructured successor; not on server) |
| Dockerfile `CMD` | runs `app_maps_v2.py` | runs `app.py` |
| `src/` modules | ≈ repo, minus later fixes | newer |
| Pairing-lines feature | absent | partially built, **then reverted on `main`** |

**Do NOT blindly deploy `app.py` to prod.** The repo is structurally ahead (entrypoint
rename + a reverted feature) and `app.py` has never run in production. Deploying it
wholesale risks regressions. Keep fixes minimal until someone intentionally migrates
the server to the `app.py` codebase.

### To ship a code fix to prod TODAY (safe, surgical)

1. Make the change in **both** the repo (commit to `main`, keeps them in sync) **and**
   the server file in place.
2. Patch the server file directly, then rebuild the container:

```bash
# 1. Patch the file in place on the server (example: sed, or scp the single file)
#    e.g. scp src/utils/choropleth_map.py root@164.92.92.181:/opt/dss-app/src/utils/

# 2. Rebuild + restart + health check (data is a read-only mounted volume, untouched)
ssh root@164.92.92.181 'cd /opt/dss-app && \
  docker stop dss-app; docker rm dss-app; \
  docker build -t dss-app . && \
  docker run -d -p 8501:8501 -v $(pwd)/data:/app/data:ro --name dss-app --restart unless-stopped dss-app && \
  sleep 10 && curl -s --fail http://localhost:8501/_stcore/health && echo " HEALTH-OK"'
```

3. Hard-refresh the browser (Cmd+Shift+R) — Streamlit/CDN caching is aggressive.

To snapshot the live server for comparison:
```bash
rsync -avz --exclude data --exclude .git root@164.92.92.181:/opt/dss-app/ /tmp/dss-server-snapshot/
diff -rq --exclude=__pycache__ /tmp/dss-server-snapshot <this-repo>
```

The "Future Deployments" git-based steps below only apply **after** the one-time
migration in "Initial Setup" has actually been run on the server. As of 2026-06-17 it
has not.

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
