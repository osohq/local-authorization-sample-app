set -eu
cd "$(dirname "$0")/.."

python3 bin/seed_data.py

oso-cloud policy -f policy.polar
# TODO: sync is disabled by default
oso-cloud experimental reconcile oso_remote.yaml --perform-updates
