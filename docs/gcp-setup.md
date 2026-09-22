# GCP setup for the CHIA cluster

This document tells you how to get the $300 GCP Free Trial credit and how to prepare a project for `chia up`. It is a condensed version of the hackathon guide "Google Cloud Platform (GCP) $300 Free Trial Credit Usage Guide". Read that PDF for screenshots and for the terms of service links.

## Get the Free Trial credit

You need a Google account that has not used GCP before. You also need a payment method for identity verification. Google places a small temporary hold on the payment method and releases it later.

1. Go to console.cloud.google.com and log in. If your Workspace organization blocks GCP, use a personal account.
2. Read and agree to the Terms of Service.
3. Click "Try for free" or the "Start free" banner.
4. Agree to the Free Trial terms.
5. Make sure that your contact information is correct. Then add a credit card or a bank account.
6. Click "Start free".

The trial provisions a project named "My First Project" and a Free Trial billing account. The Free Trial billing account can only spend the $300 credit. It cannot charge your payment method.

Do not click "Activate", "Activate full account", "Upgrade", or "Upgrade billing account". An upgraded account charges your payment method for usage outside the Free Trial limits. The hackathon organizers are not responsible for those charges.

## Prepare the project for chia up

The `chia up` command provisions GCP worker nodes for a CHIA cluster. Run these commands in the shell that will bring up the cluster:

```sh
pip install google-cloud-compute   # In a python venv

gcloud auth application-default login
gcloud auth application-default set-quota-project <project>
gcloud services enable compute.googleapis.com --project <project>
```

Replace `<project>` with the project ID from the GCP console.

## SSH keys and Tailscale

Your cluster configuration YAML names the SSH keys for the instances. CHIA installs the public key on each instance as an authorized key. CHIA uses the private key to set up the logical workers over SSH. If you only give the private key file, CHIA computes the public key from it. Before you run `chia up`, add the key to your ssh-agent. This prevents a passphrase prompt during provisioning.

The guide recommends Tailscale, a mesh VPN service, to join local and GCP machines into one cluster. Tailscale is free for this use. Create an account at https://tailscale.com/. The fully managed cluster YAML in https://github.com/ucb-bar/chia/tree/main/examples/tailscale is the fastest way to start. The cluster configuration reference is at https://docs.chialoops.ai/en/latest/user_guides/cluster_config_reference.html#tailnet-tailscale-clusters.

## Gemini through GCP

CHIA can use your GCP account for Gemini model calls. Follow https://docs.chialoops.ai/en/latest/user_guides/google_auth.html. The `memcpy` and `circt_issue_solver` examples in the CHIA repository show working agent configurations:

- https://github.com/ucb-bar/chia/tree/main/examples/memcpy
- https://github.com/ucb-bar/chia/tree/main/examples/circt_issue_solver

## Budget guardrails for this project

The proposal targets $600 to $1,100 of total spend across compute and Gemini credits. The Free Trial credit covers $300 per account.

- Use `c2d` spot instances for trace runs. The proposal estimates $0.01 to $0.02 per core-hour.
- Store traces once in a regional bucket. The 105-trace training set is about 14 GiB
  compressed, so regional standard storage costs well under $1 per month. (The 160 GiB
  figure in the proposal is unverified; see README "Fact-check corrections" item 3. The
  full post-contest set on Zenodo is 72.69 GiB, and this project does not need it.)
- The bucket for this project is `gs://a3-chia-hack26ath-7728-cbp2025`, in `us-central1`
  to match the cluster zone in `cluster/cluster.yaml`. Traces live under `cbp2025/<workload>/`.
- Before the first large run, set a budget alert in the GCP console.
- Tear the cluster down after each session. Spot instances still cost credit while idle.
