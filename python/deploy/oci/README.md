# OCI deployment — agent memory on Ampere A1

Deploy the cursor-dreaming-memory layer on Oracle Cloud Free Tier (ARM).

## Prerequisites

- OCI CLI configured (`~/.oci/config`)
- Ampere A1 compute instance (Ubuntu 22.04+ ARM64)
- SSH access to the instance

## 1. Provision instance (optional)

```bash
# List available shapes in your compartment
oci compute shape list --compartment-id <COMPARTMENT_OCID>

# Create instance (example — adjust image OCID for your region)
oci compute instance launch \
  --availability-domain <AD> \
  --compartment-id <COMPARTMENT_OCID> \
  --shape VM.Standard.A1.Flex \
  --shape-config '{"ocpus":1,"memoryInGBs":6}' \
  --display-name agent-memory-a1 \
  --image-id <UBUNTU_ARM_IMAGE_OCID> \
  --subnet-id <SUBNET_OCID> \
  --assign-public-ip true
```

## 2. Copy code to instance

```bash
rsync -avz python/ ubuntu@<INSTANCE_IP>:~/cursor-dreaming-memory/
scp .env ubuntu@<INSTANCE_IP>:~/cursor-dreaming-memory/.env
```

## 3. Start Postgres

On the instance:

```bash
cd ~/cursor-dreaming-memory/deploy/oci
docker compose up -d
```

Postgres listens on `localhost:5432`, database `agent_memory`.

## 4. Install Python package

```bash
cd ~/cursor-dreaming-memory
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
export AGENT_MEMORY_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_memory
uv run dream-memory init
```

## 5. Environment variables

```bash
export LINEAR_API_KEY=lin_api_...
export NOTION_API_KEY=secret_...
export AGENT_MEMORY_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_memory
```

## 6. Optional: Prefect scheduled sync

```bash
uv sync --extra prefect
uv run python deploy/oci/prefect_flow.py
```

Runs a daily Linear issue ingest for configured CHEF/GROEP tickets.

## 7. systemd service (optional)

```ini
# /etc/systemd/system/agent-memory.service
[Unit]
Description=Agent Memory Prefect Worker
After=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/cursor-dreaming-memory
EnvironmentFile=/home/ubuntu/cursor-dreaming-memory/.env
ExecStart=/home/ubuntu/.local/bin/uv run python deploy/oci/prefect_flow.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## ARM notes

- Use `psycopg[binary]` wheels (included) — no x86-only deps
- LanceDB optional extra works on aarch64 when installed via pip
- Keep memory lightweight: 1 OCPU / 6 GB RAM is sufficient for dev
