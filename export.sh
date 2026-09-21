export GCP_PROJECT=chia-hackathon-paper2pipeline
export HEAD_IP=$(hostname -I | awk '{print $1}')
export THIS_MACHINE=$(hostname -I | awk '{print $1}')
export GCP_PRIVATE_KEY_PATH=/home/laievan/.ssh/id_rsa

# Shared secret for the Vertex LLM gateway (docs/llm-gateway.md). The DSE
# configs reference it as ${P2P_GATEWAY_TOKEN}, and loop/constants.py only
# forwards it into the EvolverNode actor if it is set here, in the shell that
# submits the job. Created by scripts/install_llm_gateway.sh.
if [ -f "$HOME/.config/p2p/gateway.env" ]; then
    export P2P_GATEWAY_TOKEN="$(grep P2P_GATEWAY_TOKEN "$HOME/.config/p2p/gateway.env" | cut -d= -f2-)"
fi
