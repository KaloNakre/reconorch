![Reconorch Banner](banner.png)

# Reconorch

A small, extensible orchestrator for CLI security scanning tools (nmap, nikto,
gobuster, and anything else you wrap as an "adapter"). Runs scans in parallel
or on a schedule using [Ray](https://www.ray.io/), and calls each tool via
Python's `subprocess` (never `shell=True`, so no shell-injection surface from
target names or args).

> ⚠️ **Authorized testing only.** Only point this at systems you own or have
> explicit written permission to test. Unauthorized scanning of systems you
> don't control may be illegal in your jurisdiction.

## What's included

- `reconorch/tools/base.py` — `ToolAdapter` base class: any CLI tool becomes
  an adapter by implementing `build_command()` and `parse_output()`.
- `reconorch/tools/nmap_adapter.py` — nmap, including NSE script support
  (`scripts: ["vuln"]` in config).
- `reconorch/tools/nikto_adapter.py`, `gobuster_adapter.py` — example adapters.
- `reconorch/orchestrator.py` — Ray-based parallel execution across targets.
- `reconorch/scheduler.py` — continuous mode, per-tool interval.
- `reconorch/storage.py` — SQLite result history.
- `reconorch/cli.py` — `reconorch scan / watch / results / check-tools`.

## Install on Kali Linux (or any Debian-based distro)

```bash
# 1. System tools this project wraps
sudo apt update
sudo apt install -y nmap nikto gobuster

# 2. Clone your repo (after you've pushed it to GitHub — see below)
git clone https://github.com/<your-username>/reconorch.git
cd reconorch

# 3. Python virtual environment (recommended, keeps deps isolated)
python3 -m venv venv
source venv/bin/activate

# 4. Install this package + its Python deps (ray, pyyaml)
pip install -e .

# 5. Copy the example config and edit targets to something you're
#    authorized to scan (defaults to 127.0.0.1)
cp config.example.yaml config.yaml
nano config.yaml   # or vim/your editor

# 6. Check which required binaries are actually on PATH
reconorch check-tools --config config.yaml

# 7. Run every enabled tool once
reconorch scan --config config.yaml

# 8. Or run continuously per each tool's configured interval
reconorch watch --config config.yaml

# 9. View saved results any time
reconorch results --config config.yaml
```

Kali ships `gobuster` and `nmap` in its default repos; `nikto` too. If any
are missing: `sudo apt install nikto` etc.

## Usage

### 1. Install required scanning tools (Kali/Debian-based)

```bash
sudo apt update
sudo apt install -y nmap nikto gobuster
```

### 2. Clone and install this project

```bash
git clone https://github.com/<your-username>/reconorch.git
cd reconorch
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Configure your targets

```bash
cp config.example.yaml config.yaml
nano config.yaml
```

Edit the `targets:` and `tools:` sections — only scan systems you own or
have explicit written permission to test.

### 4. Check that required tools are installed

```bash
reconorch check-tools --config config.yaml
```

### 5. Run a scan

```bash
# Run every enabled tool once
reconorch scan --config config.yaml

# Run just one tool
reconorch scan --config config.yaml --tool nmap-quick

# Run continuously on each tool's configured interval
reconorch watch --config config.yaml
```

### 6. View results

```bash
reconorch results --config config.yaml
reconorch results --config config.yaml --tool nmap --target local-test
```

### Example: enabling Nmap NSE scripts

```yaml
tools:
  - name: "nmap-vuln-scan"
    adapter: "reconorch.tools.nmap_adapter.NmapAdapter"
    enabled: true
    args:
      ports: "1-1000"
      flags: ["-sV", "-T4"]
      scripts: ["vuln"]
```


