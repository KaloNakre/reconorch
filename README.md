# cyberorch

A small, extensible orchestrator for CLI security scanning tools (nmap, nikto,
gobuster, and anything else you wrap as an "adapter"). Runs scans in parallel
or on a schedule using [Ray](https://www.ray.io/), and calls each tool via
Python's `subprocess` (never `shell=True`, so no shell-injection surface from
target names or args).

> ⚠️ **Authorized testing only.** Only point this at systems you own or have
> explicit written permission to test. Unauthorized scanning of systems you
> don't control may be illegal in your jurisdiction.

## What's included

- `cyberorch/tools/base.py` — `ToolAdapter` base class: any CLI tool becomes
  an adapter by implementing `build_command()` and `parse_output()`.
- `cyberorch/tools/nmap_adapter.py` — nmap, including NSE script support
  (`scripts: ["vuln"]` in config).
- `cyberorch/tools/nikto_adapter.py`, `gobuster_adapter.py` — example adapters.
- `cyberorch/orchestrator.py` — Ray-based parallel execution across targets.
- `cyberorch/scheduler.py` — continuous mode, per-tool interval.
- `cyberorch/storage.py` — SQLite result history.
- `cyberorch/cli.py` — `cyberorch scan / watch / results / check-tools`.

## Install on Kali Linux (or any Debian-based distro)

```bash
# 1. System tools this project wraps
sudo apt update
sudo apt install -y nmap nikto gobuster

# 2. Clone your repo (after you've pushed it to GitHub — see below)
git clone https://github.com/<your-username>/cyberorch.git
cd cyberorch

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
cyberorch check-tools --config config.yaml

# 7. Run every enabled tool once
cyberorch scan --config config.yaml

# 8. Or run continuously per each tool's configured interval
cyberorch watch --config config.yaml

# 9. View saved results any time
cyberorch results --config config.yaml
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
git clone https://github.com/<your-username>/cyberorch.git
cd cyberorch
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
cyberorch check-tools --config config.yaml
```

### 5. Run a scan

```bash
# Run every enabled tool once
cyberorch scan --config config.yaml

# Run just one tool
cyberorch scan --config config.yaml --tool nmap-quick

# Run continuously on each tool's configured interval
cyberorch watch --config config.yaml
```

### 6. View results

```bash
cyberorch results --config config.yaml
cyberorch results --config config.yaml --tool nmap --target local-test
```

### Example: enabling Nmap NSE scripts

```yaml
tools:
  - name: "nmap-vuln-scan"
    adapter: "cyberorch.tools.nmap_adapter.NmapAdapter"
    enabled: true
    args:
      ports: "1-1000"
      flags: ["-sV", "-T4"]
      scripts: ["vuln"]
```

## Pushing this project to GitHub (from Windows/VS Code)

```bash
git init
git add .
git commit -m "Initial commit: cyberorch scan orchestrator"
git branch -M main
git remote add origin https://github.com/<your-username>/cyberorch.git
git push -u origin main
```

Notes for Windows → Linux round-trips:
- `.gitattributes` in this repo forces LF line endings, so files you edit in
  VS Code on Windows won't break when run on Kali.
- `.gitignore` excludes `venv/`, `results.db`, and your real `config.yaml`
  (only `config.example.yaml` is tracked) — don't commit real target lists
  or scan data to a public repo.
- If you ever add a `.sh` script, run `chmod +x script.sh` on Linux after
  cloning — Git on Windows doesn't preserve the executable bit.

## Adding a new tool (e.g. amass, subfinder, sqlmap)

1. Create `cyberorch/tools/yourtool_adapter.py`, subclass `ToolAdapter`,
   implement `build_command()` (return an argv list) and `parse_output()`.
2. Add an entry to `config.yaml` under `tools:` pointing `adapter:` at the
   dotted path of your new class.
3. Done — the orchestrator, scheduler, and storage all work with it
   automatically.

## Project roadmap (see chat for full details)

This is "Project 1" in a 10-project learning path: basic multi-tool
automation → scheduling → phase-chained recon → notifications → reporting →
Docker packaging → distributed multi-machine Ray → AI-assisted findings
triage → web dashboard → LLM/AI-endpoint security testing module.
