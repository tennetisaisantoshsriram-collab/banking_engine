"""
deploy_public.py — One command to get a live public URL.
No account. No signup. No config.

Run:  python deploy_public.py

How it works:
  1. Downloads cloudflared (Cloudflare tunnel binary) if not present
  2. Starts Streamlit on localhost:8501
  3. Opens a Cloudflare quick-tunnel → public HTTPS URL
  4. Prints the URL — share it with anyone
"""

import os, sys, re, time, signal, platform, subprocess, threading, urllib.request, shutil

PORT       = 8501
CF_DIR     = os.path.join(os.path.dirname(__file__), ".cf")
APP_FILE   = os.path.join(os.path.dirname(__file__), "app.py")
IS_WINDOWS = platform.system() == "Windows"

CF_URLS = {
    "Windows": "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe",
    "Linux":   "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
    "Darwin":  "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz",
}

CYAN  = "\033[96m"
GREEN = "\033[92m"
BOLD  = "\033[1m"
RESET = "\033[0m"
YELLOW= "\033[93m"
RED   = "\033[91m"

def banner():
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════╗
║   Banking Credit Risk Engine — Public Deployment     ║
╚══════════════════════════════════════════════════════╝{RESET}
""")

def get_cloudflared():
    system = platform.system()
    cf_bin = os.path.join(CF_DIR, "cloudflared.exe" if IS_WINDOWS else "cloudflared")
    if os.path.exists(cf_bin):
        return cf_bin

    cf_url = CF_URLS.get(system)
    if not cf_url:
        print(f"{RED}Unsupported OS: {system}{RESET}"); sys.exit(1)

    os.makedirs(CF_DIR, exist_ok=True)
    print(f"  Downloading cloudflared for {system}...")

    tmp = cf_bin + ".tmp"
    try:
        urllib.request.urlretrieve(cf_url, tmp)
    except Exception as e:
        print(f"{RED}Download failed: {e}{RESET}"); sys.exit(1)

    if system == "Darwin" and cf_url.endswith(".tgz"):
        import tarfile
        with tarfile.open(tmp) as t:
            t.extractall(CF_DIR)
        os.remove(tmp)
    else:
        os.rename(tmp, cf_bin)

    if not IS_WINDOWS:
        os.chmod(cf_bin, 0o755)

    print(f"  cloudflared ready.")
    return cf_bin

def wait_for_streamlit(timeout=60):
    import urllib.error
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"http://localhost:{PORT}/_stcore/health", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False

def start_streamlit():
    cmd = [sys.executable, "-m", "streamlit", "run", APP_FILE,
           f"--server.port={PORT}", "--server.headless=true",
           "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return proc

def start_tunnel(cf_bin):
    cmd = [cf_bin, "tunnel", "--url", f"http://localhost:{PORT}"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True, bufsize=1)
    return proc

def extract_url(line):
    m = re.search(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", line)
    return m.group(0) if m else None

def main():
    banner()

    # ── Step 1: cloudflared ─────────────────────────────
    print(f"{BOLD}[1/3] Checking Cloudflare tunnel binary...{RESET}")
    cf_bin = get_cloudflared()
    print(f"  {GREEN}✓ Ready{RESET}")

    # ── Step 2: Streamlit ───────────────────────────────
    print(f"\n{BOLD}[2/3] Starting Streamlit app on port {PORT}...{RESET}")
    st_proc = start_streamlit()
    if wait_for_streamlit():
        print(f"  {GREEN}✓ Streamlit running{RESET}")
    else:
        print(f"  {YELLOW}⚠ Streamlit slow to start — continuing anyway{RESET}")

    # ── Step 3: Tunnel ──────────────────────────────────
    print(f"\n{BOLD}[3/3] Opening Cloudflare quick-tunnel...{RESET}")
    cf_proc = start_tunnel(cf_bin)

    public_url = None
    deadline = time.time() + 60
    for line in cf_proc.stdout:
        url = extract_url(line)
        if url:
            public_url = url
            break
        if time.time() > deadline:
            break

    if not public_url:
        print(f"{RED}Could not get public URL. Try again.{RESET}")
        st_proc.terminate(); cf_proc.terminate(); sys.exit(1)

    print(f"""
{BOLD}{GREEN}╔══════════════════════════════════════════════════════╗
║   APP IS LIVE                                        ║
╠══════════════════════════════════════════════════════╣
║   {public_url:<52} ║
╚══════════════════════════════════════════════════════╝{RESET}

  {YELLOW}Share this URL with anyone — works on any device.{RESET}
  {YELLOW}URL stays active while this terminal is open.{RESET}
  {YELLOW}Press Ctrl+C to stop.{RESET}
""")

    # ── Keep alive ──────────────────────────────────────
    def cleanup(sig=None, frame=None):
        print(f"\n{YELLOW}Shutting down...{RESET}")
        cf_proc.terminate(); st_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT,  cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        cf_proc.wait()
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
