# CHIA cluster + GCP + Gemini auth — verified API surface

All content below is from `ucb-bar/chia` @ `main` (tree sha `16c35e92aaaf9511c6453bf94cd5cf589698f4e3`, fetched 2026-09-11) via raw.githubusercontent.com, plus the rendered docs at docs.chialoops.ai (confirmed live; the `.rst` sources in the repo are the same content). Local copies: `/private/tmp/claude-502/-Users-evanlai/d8510fae-cc23-452f-984c-f30b9aac4856/scratchpad/chia/`.

## 1. Cluster-config YAML schema (docs/user_guides/cluster_config_reference.rst)

A cluster is one YAML file passed to `chia up` / `chia down`. Deliberately Ray-cluster-launcher-like, but these Ray autoscaler keys are NOT supported: `min_workers`/`max_workers` (top-level autoscaling semantics), `upscaling_speed`, `idle_timeout_minutes`, `cluster_synced_files`, `file_mounts_sync_continuously`, `provider.type`, `provider.external_head_ip`, `provider.coordinator_address`. `${VAR}` in string values is expanded from the caller's environment at load; bare `$VAR` is left for the remote shell.

### Top-level keys (key — default — meaning)
- `cluster_name` — `"default"` — cluster identifier.
- `provider` — required — head node. Only key: `head_ip` (required): hostname/IP of the machine running the Ray head.
- `auth` — `{}` — SSH credentials:
  - `ssh_user` (default `""`)
  - `ssh_private_key` (default `None`; omit if key is in ssh-agent)
  - `ssh_proxy_command` (default `None`; e.g. `nc -X 5 -x 127.0.0.1:1055 %h %p`; applied to ssh, rsync, and tunnels)
  - `overrides` (default `{}`): per-IP dict keyed by hostname/IP or `@node_type:index` placeholder; each entry may set `ssh_user`, `ssh_private_key`, `ssh_proxy_command`, `tailnet: true`, `manage_tailscale: true`, or a `tunnel` block. CHIA auto-populates overrides for provisioned cloud nodes.
- `available_node_types` — `{}` — logical worker types (below).
- `initialization_commands` — `[]` — host-side, each in its own SSH session, outside any container.
- `setup_commands` — `[]` — global setup in the main script session on every node (inside container for dockerized workers).
- `head_env_commands` — `[]` — env activation prepended to head's main script on BOTH up and down.
- `head_setup_commands` — `[]` — head-only one-time setup during `chia up`.
- `head_teardown_commands` — `[]` — head-only, run during `chia down` before `ray stop`.
- `head_start_ray_commands` — `[]` — typically `ray stop` then `ray start --head ...`.
- `worker_start_ray_commands` — `[]` — CHIA injects `--resources` automatically (plus pinned ports + proxy env for tailnet/tunneled workers).
- `file_mounts` — `{}` — `{remote_path: local_path}` rsync'd to each node before the main script (trailing `/` on local_path copies contents, else nests).
- `rsync_exclude` — `[]`; `rsync_filter` — `[]`.
- `docker` — `None` — cluster-wide default container config; node types override.
- `aws_nodes` — `None`; `gcp_nodes` — `None` — cloud provisioning (below).
- `tailnet` — recommended for cloud workers (below).
- `tunnel_defaults` — `None` — SSH-tunnel fallback tuning; ignored when tailnet is used.

### available_node_types.<type> keys
- `resources` — `{}` — custom Ray resources advertised per worker, e.g. `{"verilator_run": 8}`. `@ChiaFunction(resources={...})` schedules onto matching workers.
- `num_workers` — `1` — fixed worker count. Fallback aliases: `max_workers` then `min_workers` (no autoscaling; if both set and differ, `max_workers` wins).
- `compatible_ips` — required if num_workers > 0 — machines this type may run on; accepts `@node_type:index` cloud placeholders. Listing a machine twice biases more workers onto it.
- `worker_env_commands` — `[]` — per-type env activation, runs on up AND down, inside container if dockerized.
- `worker_setup_commands` — `[]` — per-type one-time setup on up.
- `docker` — `None` — per-type container config.
- `balance_level` — `"cluster"` — placement: `cluster` = pack onto machine with fewest workers globally; `worker` = spread this type evenly over its own IP pool.

### docker block (top-level or per-type)
`image` (required), `container_name` (default `"chia_container"`; CHIA appends worker index `-0`, `-1`, …; include `${USER}` on shared machines), `pull_before_run` (True), `pull_timeout` (600 s), `run_options` (`[]`, raw `docker run` flags — CHIA itself adds `--net=host` and `--shm-size=8g` and NO volume mounts), `run_setup_commands` (`[]`, run inside container before the main script). Head node is never containerized. Scripts run as non-interactive login shell (`bash --login`) — `~/.bashrc` is NOT sourced; hence the ubiquitous `source ~/.bashrc && conda activate chia_env` in `*_env_commands`.

### gcp_nodes (Compute Engine provisioning)
Section-level keys: `project` (required), `zone` (default `us-central1-a`), `network` / `subnetwork` (default: the project's `default` VPC). Every other key lives under a named node type:
- `machine_type` — required — e.g. `n1-standard-1`, `e2-small`.
- `count` — required — number of instances.
- `image` — default Ubuntu image — family or full URL, e.g. `projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts`.
- `zone` — per-type zone override.
- `disk_size_gb` — image default — boot disk GB.
- `spot` — `False` — Spot/preemptible VMs (cheaper, may be reclaimed).
- `ssh_user` — `None` — login user CHIA connects as (metadata method: the local user the guest agent creates on the VM).
- `ssh_private_key` — `None` — key CHIA's SSH client uses (recommended; else ssh-agent/`~/.ssh` defaults).
- `ssh_public_key` — `None` — public key injected into VM metadata. (The GCP fully-managed example omits it with the comment "public key can be derived from the private key".)
- `use_os_login` — `False` — OS Login instead of metadata keys; you must run `gcloud compute os-login ssh-keys add` and set `ssh_user` to your OS Login posix username.
- `skip_default_setup` — `False` — skip CHIA's default git/conda/docker install.
- `setup_commands` — `[]`; `setup_timeout` — 1800 s; `ssh_timeout` — 120 s.
- `join_tailnet` — auto — true when a top-level `tailnet:` exists, else false.
- Anything else — merged into the instance definition sent to the Compute API.

GCP API auth (two distinct layers): (1) API access always from Application Default Credentials — `gcloud auth application-default login` (or `GOOGLE_APPLICATION_CREDENTIALS` → service-account JSON); identity must be able to create instances and firewall rules; needs `pip install google-cloud-compute` and the Compute Engine API enabled; a `default` VPC must exist or set `network`. (2) SSH into the instance via metadata keys (default; "ordinary keypair, the GCP analog of an AWS KeyName, not tied to any Google identity, silently ignored if the project or org enforces OS Login") or OS Login.

### aws_nodes (for contrast)
Section key `region` (default `us-west-2`); per-type: `KeyName` (required, existing EC2 key pair), `InstanceType` (required), `count` (required), `ImageId` (default Ubuntu 22.04 AMI), `ssh_user`, `ssh_private_key`, `skip_default_setup` (False), `setup_commands`, `setup_timeout` (1800), `ssh_timeout` (120), `join_tailnet` (auto); unknown keys (e.g. `BlockDeviceMappings`, `UserData`) pass through to EC2 `RunInstances`. Credentials from `~/.aws/credentials`/`~/.aws/config` (override paths via `AWS_CONFIG_FILE`, `AWS_SHARED_CREDENTIALS_FILE`).

### Cloud-node references
`@<node_type>:<index>` placeholders (0-based, `<node_type>` = key under `aws_nodes`/`gcp_nodes`) are valid anywhere an IP is: `compatible_ips` and `auth.overrides` keys.

### tunnel_defaults (SSH-tunnel fallback only; ignored under tailnet)
Fields with defaults: `gcs_tunnel_port` (16379), `ray_node_manager_port` (16800), `ray_object_manager_port` (16801), `ray_worker_port_min/max` (in example 20000/20001), `head_worker_port_min/max` (21000/21001 in example), `tool_port_min`/`max` (18000/18010), `head_tool_port_min`/`max` (8000/8010), `head_node_manager_port` (29800), `head_object_manager_port` (29801), `kill_orphaned_tunnels` (true), `pre_tunnel_commands`. `tunnel_ip` is CHIA-assigned per worker and cannot be set. Typos in field names fail loudly at load.

### tailnet section (#tailnet-tailscale-clusters)
Presence of the `tailnet:` block is the opt-in; every worker IP that is not the head machine is auto-treated as a tailnet machine and SSH to it dials through the SOCKS5 proxy (`nc -X 5 -x <socks_proxy> %h %p`; head needs OpenBSD netcat). Fields:
- `head_tailnet_ip` — required unless `manage_all: true` (then discovered at bring-up) — the head's tailscale 100.x IP.
- `socks_proxy` — default `127.0.0.1:1055` — tailscaled `--socks5-server` on every machine.
- `auth_key` — reusable (ideally ephemeral, pre-authorized) tailscale key `tskey-auth-...`; required for cloud/managed workers; reference as `${TS_AUTHKEY}`.
- `manage_all` — CHIA runs tailscale on EVERY machine incl. head; every worker must then be listed by an ordinary SSH-reachable IP (a `100.64.0.0/10` address fails loudly at config load); opt-out per machine with `manage_tailscale: false` in `auth.overrides`.
- `tailscale_version` — pinned tarball version.
- `tailscale_dir` — install/state dir on managed machines, default `/tmp/<cluster_name>/tailscale`; path length checked at load (~107-char Unix socket limit); `/tmp` state may not survive reboots — next `chia up` rejoins via the reusable auth key.
- Port fields (defaults): `head_advertise_ip` (127.200.0.1), `gcs_port` (6379 — must match `--port` in `head_start_ray_commands`), `connect_proxy_port` (13129 — relay's HTTP CONNECT listener that Ray's `grpc_proxy` points at), `head_node_manager_port` (23744), `head_object_manager_port` (23745), `head_tool_port_min/max` (23760/23770), `head_worker_port_min/max` (23808/23935), `worker_block_base` (24000), `worker_block_size` (256), `tool_port_count` (11), `worker_port_count` (128). Port blocks are indexed per machine (reused across machines); up to 162 workers per single machine at defaults; cluster size unbounded. A machine's Ray worker-port range must exceed its CPU count (Ray prestarts one worker per CPU). Defaults live in `TailnetConfig` in `chia/cluster/config.py`; the relay is `chia/cluster/tailnet.py`.
- Constraints: all workers must be tailnet workers or colocated on the head machine; mixing with SSH-tunneled/cloud-tunnel workers rejected at config load; `chia up --add` not supported for tailnet clusters (re-run `chia up`; existing workers detected and skipped); throughput bounded by userspace wireguard-go.
- CHIA injects `--node-ip-address`, pinned ports, and `grpc_proxy` env into head/worker `ray start` automatically; starts relays before workers; stops them on `chia down`.
- Per NETWORKING.md, injected env on every ray start: `RAY_grpc_enable_http_proxy=1`, `grpc_proxy=http://127.0.0.1:13129`, `no_grpc_proxy=<own advertise IP(s)>,127.0.0.1,localhost`. Workers advertise loopback IPs `127.0.0.2`, `127.0.0.3`, …; head fixed at `127.200.0.1`.
- Driver on the head (before running any flow, from README): `export RAY_ADDRESS=127.200.0.1:6379; export RAY_grpc_enable_http_proxy=1; export grpc_proxy=http://127.0.0.1:13129; export no_grpc_proxy=127.200.0.1,127.0.0.1,localhost`. Flows that host tools on the head driver should export `CHIA_TOOL_ADVERTISE_HOST=<head_advertise_ip>` and `CHIA_TOOL_BASE_PORT`/`CHIA_TOOL_MAX_PORT` matching the `head_tool_port_*` range.

## 2. Verbatim: examples/tailscale/cluster_gcp_fullymanaged.yaml (the fully-managed GCP cluster)

```yaml
# Fully managed tailnet cluster, GCP edition: CHIA runs tailscale on EVERY
# machine — the head (which also hosts a colocated worker), an on-prem
# worker, and a Compute Engine worker — no manual tailscaled anywhere.
# The gcp_nodes analog of cluster_ec2_fullymanaged.yaml. Environment
# variables to set before `chia up` / `chia down`:
#   HEAD_IP      how CHIA SSHes to the head (its real IP/hostname)
#   WORKER_IP    the on-prem worker's real IP/hostname (NOT its tailscale
#                address — tailscale can't be bootstrapped over tailscale,
#                so managed machines must be ordinarily SSH-reachable)
#   TS_AUTHKEY   reusable tailscale auth key, e.g.:
#                export TS_AUTHKEY=$(cat examples/tailscale/keyfile)
#   GCP_PROJECT  the GCP project the VM is created (and billed) in
#   GCP_SSH_KEY  private key whose .pub is injected into the VM's metadata
#                and which CHIA's SSH client uses, e.g. ${HOME}/.ssh/id_ed25519
#
# GCP API access comes from Application Default Credentials on the machine
# running `chia up`: `gcloud auth application-default login` (+ `gcloud auth
# application-default set-quota-project $GCP_PROJECT`), or point
# GOOGLE_APPLICATION_CREDENTIALS at a service-account key. Needs
# `pip install google-cloud-compute`, the Compute Engine API enabled, and an
# identity that can create instances and firewall rules in the project.
# Unlike EC2 there is no cloud-registered key pair: CHIA injects
# `<ssh_user>:<GCP_SSH_KEY>.pub` via instance metadata and the guest agent
# creates the user (set `use_os_login: true` instead if your org enforces OS
# Login — then register the key with `gcloud compute os-login ssh-keys add`
# and set ssh_user to your OS Login posix username).

cluster_name: TailscaleFullyManagedGCP

tailnet:
    manage_all: true
    auth_key: ${TS_AUTHKEY}
    # head_tailnet_ip is omitted — discovered when CHIA joins the head.
    # A non-default proxy port keeps this cluster's daemons fully
    # independent of any personally-run tailscaled (which typically
    # serves 1055). Binaries/state live in /tmp/<cluster_name>/tailscale.
    socks_proxy: 127.0.0.1:1155

provider:
    head_ip: ${HEAD_IP}

auth:
    ssh_user: ${USER}

gcp_nodes:
    project: ${GCP_PROJECT}
    zone: us-central1-a               # default zone; per-type `zone:` overrides
    # network / subnetwork default to the project's `default` VPC.
    gcp_worker:
        machine_type: e2-small
        count: 1
        image: projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts
        disk_size_gb: 24
        spot: false                   # true = Spot VM (cheaper, may be reclaimed)
        ssh_user: chia                # local user the guest agent creates on the VM
        ssh_private_key: ${GCP_PRIVATE_KEY_PATH} # public key can be derived from the private key

available_node_types:

    head_worker:
        resources: {"head_worker": 4}
        num_workers: 1
        compatible_ips: ["${HEAD_IP}"]
        worker_env_commands: ["source ~/.bashrc && conda activate chia_env"]

    tailscale_worker:
        resources: {"tailscale_worker": 4}
        num_workers: 1
        compatible_ips: ["${WORKER_IP}"]
        worker_env_commands: ["source ~/.bashrc && conda activate chia_env"]

    gcp_worker:
        resources: {"gcp_worker": 2}
        num_workers: 1
        compatible_ips: ["@gcp_worker:0"]
        worker_env_commands: ["source ~/.bashrc && conda activate chia_env"]

head_env_commands: ["source ~/.bashrc && conda activate chia_env"]

head_start_ray_commands:
    - ray stop
    - ray start --head --port=6379 --dashboard-agent-listen-port=0 --resources='{"head":4}'

worker_start_ray_commands:
    - ray stop
    - ray start --address=$RAY_HEAD_IP:6379 --dashboard-agent-listen-port=0
```

NOTE (real inconsistency in the file): the header comment names the env var `GCP_SSH_KEY` but the yaml body actually uses `ssh_private_key: ${GCP_PRIVATE_KEY_PATH}`. If you copy this file, export `GCP_PRIVATE_KEY_PATH`.

The EC2 twin `cluster_ec2_fullymanaged.yaml` (`cluster_name: TailscaleFullyManaged`) is identical except the cloud block: `aws_nodes: {region: us-east-1, ec2_worker: {KeyName: ${AWS_KEYPAIR}, InstanceType: t3.small, count: 1, ImageId: ami-0d001f8052688dc45  # Ubuntu 22.04 (us-east-1), ssh_user: ubuntu, BlockDeviceMappings: [{DeviceName: /dev/sda1, Ebs: {VolumeSize: 24, VolumeType: gp3}}]}}` and env vars `AWS_KEYPAIR` / `AWS_KEYPAIR_PEM`. The unmanaged example `cluster.yaml` (`cluster_name: TailscaleExample`) instead has `tailnet: {head_tailnet_ip: ${HEAD_TAILNET_IP}, socks_proxy: 127.0.0.1:1055}` and env vars `HEAD_IP`, `HEAD_TAILNET_IP`, `WORKER_TAILNET_IP`; `examples/tailscale/.gitignore` contains only `keyfile`.

## 3. Exact `chia up` workflow

GCP prerequisites (from the yaml header + cluster ref):
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project $GCP_PROJECT
# (or GOOGLE_APPLICATION_CREDENTIALS=/path/sa-key.json)
pip install google-cloud-compute
# Compute Engine API enabled in the project; identity able to create instances + firewall rules; default VPC exists (or set gcp_nodes.network)
```
(The literal `gcloud services enable compute.googleapis.com` command does NOT appear verbatim anywhere in the repo/docs — the docs just say "the Compute Engine API enabled". The `services enable` command that IS written out is `gcloud services enable aiplatform.googleapis.com --project <project>` in google_auth.rst.)

Tailscale prerequisite: reusable, pre-authorized (ideally ephemeral) auth key from the tailscale admin console (Settings → Keys), `export TS_AUTHKEY=...`. Plus a conda env with matching `ray` and `chia` on every machine (example assumes name `chia_env`).

Commands:
```bash
chia up examples/tailscale/cluster_gcp_fullymanaged.yaml     # add --dry-run to preview node assignments + exact per-worker scripts
chia up my_cluster.yaml --add    # non-tailnet only: add new workers / restart dead ones (tailnet: re-run chia up; existing workers skipped)
chia down examples/tailscale/cluster_gcp_fullymanaged.yaml   # workers first (parallel), then head; stops managed tailscaled daemons (head's last)
ray status                        # on the head, verify advertised resources
chia job submit --address http://127.0.0.1:8265 -- python loop.py   # dashboard-based job submission (non-default port example uses 8365)
```

`chia up` sequence: set up head → assign each declared worker to a machine (constrained `compatible_ips` types first; `assign_nodes` in `chia/cluster/config.py`) → provision + connect cloud nodes (join tailnet + start per-machine relays, or SSH tunnels on fallback) → set up workers (parallel across machines, sequential within a machine).

Head bring-up (host over SSH, never containerized): 1) `initialization_commands` each in own SSH session; 2) `file_mounts` rsync; 3) single SSH session running `head_env_commands` → `setup_commands` → `head_setup_commands` → `head_start_ray_commands`.

Worker bring-up (bare): 1) `initialization_commands`; 2) rsync; 3) single session: `<type>.worker_env_commands` → `setup_commands` → `<type>.worker_setup_commands` → `export RAY_HEAD_IP=...` → `worker_start_ray_commands` (--resources injected). Dockerized: docker pull/run/`run_setup_commands` on host first, then the same main script inside the container. Tailnet workers additionally: join tailnet if managed, start per-machine relay, inject `grpc_proxy` env; tunneled workers: `pre_tunnel_commands` once per physical IP + reverse SSH tunnel.

How a loop uses the running cluster: a driver runs on the head (or via `chia job submit`), calls `@ChiaFunction(resources={"gcp_worker": 1}) def f(...)` and `get(f.chia_remote(args, _chia_tag=...))` (`from chia.base.ChiaFunction import ChiaFunction, get` — see `examples/tailscale/loop.py`). On a tailnet cluster the driver first exports `RAY_ADDRESS=127.200.0.1:6379`, `RAY_grpc_enable_http_proxy=1`, `grpc_proxy=http://127.0.0.1:13129`, `no_grpc_proxy=127.200.0.1,127.0.0.1,localhost`. A `chia job submit` driver does not inherit your shell — forward env via `--runtime-env-json '{"env_vars": {...}}'`.

Teardown (`chia down`): workers first in parallel — containerized: `docker exec` (`worker_env_commands`; `ray stop`) then `docker stop` + `docker rm -f`; bare: single SSH session (`worker_env_commands`; `ray stop`, skipped if the worker shares the head machine). Then head: `head_env_commands` → `head_teardown_commands` → `ray stop`. Managed tailscaled daemons are stopped (head last); tailscale state persists in `tailscale_dir` so re-ups rejoin without consuming the auth key unless cleaned.

## 4. Gemini via GCP account (docs/user_guides/google_auth.rst)

Two supported Gemini backends; both keep credentials on the host, bind-mounted into LLM worker containers (see `examples/memcpy/cluster.yaml`, `examples/circt_issue_solver/cluster_*.yaml`).

### A. Antigravity CLI (`agy`) — class `chia.models.antigravity.AntigravityLLM`
- Install/sign-in: `curl -fsSL https://antigravity.google/cli/install.sh | bash` (installs `~/.local/bin/agy`), then `agy` (interactive Google OAuth; pick location `global`|`us`|`eu` — pick `global`, Gemini Pro is global-only; `us` gives "Selected model is not supported in the selected location" on some `gemini-*-pro*`). Switch accounts via `/logout` + `/login` inside `agy`. OAuth only — no API-key path.
- Creds on disk: `~/.gemini/antigravity-cli/antigravity-oauth-token` (refresh token) and `~/.gemini/antigravity-cli/settings.json` → `{"gcp": {"project": "<your-project-id>", "location": "global"}}`.
- Container: image `ghcr.io/ucb-bar/chia-antigravity:latest` reads `/home/ray/.gemini`. Node-type YAML: `resources: {"antigravity_creds": 1}`, `run_options: ["--user $(id -u):$(id -g)", "-v ${HOME}/.gemini:/home/ray/.gemini"]`, `run_setup_commands: ['echo "user:x:$(id -u):$(id -g)::/home/ray:/bin/bash" >> /etc/passwd']`. Mount must be writable (agy refreshes token, writes logs + per-conversation SQLite under `antigravity-cli/`); mount the whole `~/.gemini` tree; the host dir must exist before `chia up`. `AntigravityLLM` resolves `~/.gemini` on the worker that runs the prompt.
- Model ids: `agy models`; e.g. `gemini-3.1-pro-high` (suffix `-high`/`-low` = agy reasoning-effort tier). Verify: `docker exec <container> agy --print "Reply with exactly PONG"`.

### B. OpenCode + Vertex AI — class `chia.models.opencode.OpenCodeLLM`, provider `google-vertex`
- Host: `gcloud auth application-default login` (writes `~/.config/gcloud/application_default_credentials.json`) + `gcloud auth application-default set-quota-project <project>` (required for user credentials, else 403) + `gcloud services enable aiplatform.googleapis.com --project <project>`. ADC identity (check with the tokeninfo curl in the doc) needs the Vertex AI User role. Service-account alternative: mount the key + `GOOGLE_APPLICATION_CREDENTIALS=/home/ray/sa-key.json`.
- Container: image `ghcr.io/ucb-bar/chia-opencode:latest` (no gcloud needed; the auth library reads the ADC file). Node-type YAML: `resources: {"opencode_creds": 1}`, `run_options: ["-v ${HOME}/.config/gcloud:/home/ray/.config/gcloud", "-e GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}", "-e VERTEX_LOCATION=global"]`. Export `GOOGLE_CLOUD_PROJECT` before `chia up` so the substitution has a value. Env vars are read from the opencode process env, NOT `gcloud config`. Read-only mount is fine.
- Driver code (exact snippet from the doc):
```python
from chia.models.opencode import OpenCodeLLM, AdditionalModelProvider

vertex = AdditionalModelProvider(
    id="google-vertex", npm="@ai-sdk/google-vertex", name="Google Vertex AI",
    models=["gemini-3.1-pro-preview"],
    options={"project": "<project>", "location": "global"},
)
llm = OpenCodeLLM(model="google-vertex/gemini-3.1-pro-preview",
                  additional_providers=[vertex])
```
Config values take precedence over `GOOGLE_CLOUD_PROJECT`/`VERTEX_LOCATION` (env is fallback). Model string format: `google-vertex/<vertex model id>`, e.g. `google-vertex/gemini-3.1-pro-preview`. Job submission forwards env: `chia job submit --runtime-env-json "{\"env_vars\": {\"MEMCPY_OPENCODE_MODEL\": \"google-vertex/gemini-3.1-pro-preview\", \"GOOGLE_CLOUD_PROJECT\": \"$GOOGLE_CLOUD_PROJECT\"}}" -- python $PWD/examples/memcpy/memcpy_loop.py --llm opencode`. Verify: `docker exec <container> opencode run -m google-vertex/gemini-3.1-pro-preview "Reply with exactly PONG"`.

## 5. Fault tolerance / caching / data distribution

- Fault tolerance: `chia up my_cluster.yaml --add` "compares the YAML against the live cluster and only brings up workers that aren't already registered, so you can grow a running cluster (or reintegrate a machine that died) without downtime" (logical_workers.rst). Not supported on tailnet clusters — re-run plain `chia up` (existing workers detected and skipped). `spot: true` VMs "may be reclaimed". Cache/bypass are described as "improved fault tolerance by storing in-progress results".
- Caching across workers (docs/user_guides/caching_and_bypass.rst): `from chia.base.cache import start_cache, get_active_cache`. `start_cache(size=4, units="GB", cache_dir_path="/data/chia_cache", yaml_path="path/to/yaml.yaml")` on the driver after ray.init. The cache is an LRU key/value store of pickled `(tag, data)` files on disk, implemented as a remote Ray actor on the HEAD node, accessed via `chia_remote` from any worker (e.g. `get(get_active_cache().has.chia_remote(tag))`, `.read.chia_remote(tag)` → `(hit, value)`); warm-starts by scanning the cache dir, so values survive across loop runs. Writing is automatic for functions marked in YAML `cache: {fn_name: {cache: true, tags: ["iter.*"]}}` (shorthand `fn: true`), keyed by `_chia_tag`. Reading is manual via a bypass provider. Bypass YAML: `bypass: {fn: {bypass: true, tags: [regex...], data: /path}}`; `from chia.base.bypass import Bypass`; `Bypass(yaml_path=...)`, `bypass.set_provider(name, fn(tag, data_path, *args, **kwargs))`, `bypass.set_cond(name, cond)`; bypassed calls still dispatch through Ray with real resource scheduling.
- Data distribution without a shared filesystem: (a) `file_mounts` rsync to every node before the main script; (b) bypass `data:` files are "routed through a Ray actor pinned to the node that constructed the Bypass (the head), so workers on other nodes can read it without a shared filesystem"; (c) task args/results move through Ray's object store (the tailscale `loop.py` smoke test ships ~1 MiB each way); (d) tool traffic between machines rides per-port SOCKS listeners; Ray gRPC rides the per-machine HTTP CONNECT relay (NETWORKING.md, `chia/cluster/tailnet.py`).
- Related source files for deeper digging: `chia/cluster/config.py` (44 KB, `TailnetConfig`, `assign_nodes`), `chia/cluster/gcp_nodes.py` (28 KB), `chia/cluster/worker_provisioner.py` (48 KB), `chia/cluster/tailnet.py`, `chia/cluster/tunnel.py`, `chia/cluster/ray_stop.py`.

## SOURCES
https://api.github.com/repos/ucb-bar/chia/git/trees/main?recursive=1
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/tailscale/cluster_gcp_fullymanaged.yaml
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/tailscale/cluster_ec2_fullymanaged.yaml
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/tailscale/cluster.yaml
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/tailscale/README.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/tailscale/NETWORKING.md
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/tailscale/loop.py
https://raw.githubusercontent.com/ucb-bar/chia/main/examples/tailscale/.gitignore
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/user_guides/cluster_config_reference.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/user_guides/google_auth.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/user_guides/logical_workers.rst
https://raw.githubusercontent.com/ucb-bar/chia/main/docs/user_guides/caching_and_bypass.rst
https://docs.chialoops.ai/en/latest/user_guides/cluster_config_reference.html
https://docs.chialoops.ai/en/latest/user_guides/google_auth.html

## CAVEATS
1) `gcloud services enable compute.googleapis.com` never appears verbatim in repo or docs — the GCP yaml header says only "the Compute Engine API enabled"; the verbatim `services enable` command in the docs is for `aiplatform.googleapis.com` (Vertex). 2) Real inconsistency in examples/tailscale/cluster_gcp_fullymanaged.yaml: header comment documents env var `GCP_SSH_KEY` but the body uses `${GCP_PRIVATE_KEY_PATH}`. 3) tailnet port-field defaults are quoted from the docs; I did not open chia/cluster/config.py to cross-check `TailnetConfig` literals. 4) The rendered docs.chialoops.ai pages were confirmed live (google_auth.html title/headings verified; cluster_config_reference.html fetched but the WebFetch summarizer declined verbatim reproduction), so all verbatim doc text is quoted from the identical .rst sources at repo main instead — if the hosted "latest" build lags main, wording could differ slightly. 5) `connectivity-matrix.py` was downloaded but not read line-by-line (README describes it: NxN ChiaFunction dispatch + per-machine BashTool over MCP).