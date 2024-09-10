# Instructions

- `docker compose up -d`
- `python3 -m venv venv`
- `pip install -r requirements.txt`
- `export DATABASE_URL=postgresql://oso:password@localhost:5432/app_db`
- `python3 bin/seed_data.py`
- `export OSO_AUTH=e_0123456789_12345_osotesttoken01xiIn`
- `export OSO_URL=http://localhost:8081`
- (if you need to install the `oso-cloud` CLI:) `curl -L https://cloud.osohq.com/install.sh | bash`
- `oso-cloud experimental reconcile oso_remote.yaml --perform-updates`
- open `http://localhost:5050` in your browser
