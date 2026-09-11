#!/usr/bin/env bash
# One-time GCP project preparation for `chia up`.
# Mirrors step 9 of the hackathon GCP guide (docs/gcp-setup.md).
set -euo pipefail

PROJECT="${1:?usage: setup_gcp.sh <gcp-project-id>}"

# google-cloud-compute lets chia provision GCP instances.
pip install google-cloud-compute

gcloud auth application-default login
gcloud auth application-default set-quota-project "$PROJECT"
gcloud services enable compute.googleapis.com --project "$PROJECT"

echo "GCP project '$PROJECT' is ready for 'chia up'."
echo "Next: add your ssh key to the agent (ssh-add) and fill in cluster/gcp-tailscale.yaml."
