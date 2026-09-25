# Environment for the cluster commands in this repo. Source it (not run it) in
# the shell that drives chia:  source export.sh
# cluster/cluster.yaml substitutes these variables by name.

# The GCP project that owns the cluster VMs and the Vertex quota. It is also
# gcloud's configured default here. The cluster ran on
# a3-chia-hack26ath-7728 for a short while; that project, and the trace
# bucket gs://a3-chia-hack26ath-7728-cbp2025 in it, are no longer the ones in
# use. Workers fetch traces from Google Drive (cluster/cluster.yaml), not GCS.
export GCP_PROJECT=chia-hackathon-paper2pipeline

# The same project id under the name the LLM containers read: the opencode and
# antigravity node types forward it into the container for Vertex.
export GOOGLE_CLOUD_PROJECT=$GCP_PROJECT

export HEAD_IP=$(hostname -I | awk '{print $1}')
export THIS_MACHINE=$(hostname -I | awk '{print $1}')
export GCP_PRIVATE_KEY_PATH=/home/laievan/.ssh/id_rsa

# TS_AUTHKEY is deliberately absent: the tailnet: block in cluster/cluster.yaml
# is commented out, so nothing substitutes it. Add it here if that block is
# ever enabled.

# Shared secret for the Vertex LLM gateway (docs/llm-gateway.md). The DSE
# configs reference it as ${P2P_GATEWAY_TOKEN}, and loop/constants.py only
# forwards it into the EvolverNode actor if it is set here, in the shell that
# submits the job. Created by scripts/install_llm_gateway.sh.
if [ -f "$HOME/.config/p2p/gateway.env" ]; then
    export P2P_GATEWAY_TOKEN="$(grep P2P_GATEWAY_TOKEN "$HOME/.config/p2p/gateway.env" | cut -d= -f2-)"
fi

# Where that gateway listens. Both adaevolve configs name it as
# ${P2P_GATEWAY_URL} rather than an address, because the head has changed
# address once already and a stale literal in a config is a connection
# refused rather than a config error. loop/constants.py derives the same
# value from HEAD_IP and forwards it into the EvolverNode actor; this line
# is for probing the gateway by hand from this shell.
export P2P_GATEWAY_URL="http://${HEAD_IP}:8900/v1"
