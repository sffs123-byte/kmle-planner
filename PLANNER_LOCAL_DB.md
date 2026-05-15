# KMLE Planner Local DB Mode

This folder can run the full KMLE Planner shell from the Mac mini with a local SQLite DB.

## Local server

```bash
cd ~/.openclaw/workspace/kmle-planner-deploy
./start-planner-local.sh
```

Default URL:

```text
http://127.0.0.1:8796/
```

Runtime state lives in:

```text
.local/planner-local.sqlite
```

The browser sync layer auto-detects same-origin `/api/health`. When present, it uses local SQLite instead of Supabase `planner_user_state`.

## LaunchAgent

Install or refresh the local server service:

```bash
cd ~/.openclaw/workspace/kmle-planner-deploy
./scripts/install-planner-local-launchd.sh
```

Logs:

```text
.local/planner-local.out.log
.local/planner-local.err.log
```

## Permanent Cloudflare named tunnel

Quick tunnels are intentionally not used for production. A named tunnel requires Cloudflare account auth or a dashboard tunnel token.

Current blocker if no auth exists:

```bash
cloudflared tunnel list
# Error locating origin cert: no cert.pem
```

Two permanent options:

### Option A — Dashboard token

Create a Cloudflare Zero Trust Tunnel in the dashboard, route a hostname to:

```text
http://127.0.0.1:8796
```

Then install connector on this Mac:

```bash
sudo cloudflared service install <CLOUDFLARED_TUNNEL_TOKEN>
```

### Option B — CLI named tunnel

```bash
cloudflared tunnel logincloudflared tunnel create kmle-planner-local
cloudflared tunnel route dns kmle-planner-local <your-hostname>
cloudflared tunnel run kmle-planner-local
```

If `PLANNER_LOCAL_TOKEN` is set in `.local/planner-local.env`, open the first URL once with:

```text
https://<your-hostname>/?localToken=<token-from-.local/planner-local.env>
```

The token is then stored in browser localStorage as `kmlePlannerLocalToken.v1`.
