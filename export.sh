# Environment for the cluster commands in this repo. Source it (not run it) in
# the shell that drives chia:  source export.sh
# cluster/cluster.yaml substitutes these variables by name.

# The GCP project that owns the cluster VMs, the trace bucket
# (gs://a3-chia-hack26ath-7728-cbp2025) and the Vertex quota. It is also
# gcloud's configured default here. The previous value in this file,
# chia-hackathon-paper2pipeline, no longer resolves for this account --
# `chia up` failed with a compute.instances.list permission error.
export GCP_PROJECT=a3-chia-hack26ath-7728

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
