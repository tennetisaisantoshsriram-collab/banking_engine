"""
setup_deployment.py — One-time setup assistant.
Opens all required pages automatically. Run once, then git push = auto-deploy forever.

Run:  python setup_deployment.py
"""
import os, sys, webbrowser, time, subprocess

REPO = "tennetisaisantoshsriram-collab/banking_engine"
SPACE_NAME = "banking-credit-engine"

G = "\033[92m"; Y = "\033[93m"; C = "\033[96m"; B = "\033[1m"; R = "\033[0m"

def p(msg): print(msg, flush=True)

p(f"""
{B}{C}+----------------------------------------------------------+
|   Banking Credit Risk Engine — One-Time Setup          |
|   After this: every git push = auto-deploy forever     |
+----------------------------------------------------------+{R}
""")

p(f"{B}You need to do 3 things. I'll open each page for you.{R}")
p("="*58)

# ── Step 1: HF Account ────────────────────────────────────────
p(f"\n{B}STEP 1 of 3 — Create free Hugging Face account{R}")
p(f"  {Y}(skip if you already have one){R}")
input("  Press ENTER to open huggingface.co/join in your browser...")
webbrowser.open("https://huggingface.co/join")
time.sleep(2)
p(f"  {G}> Sign up with Google or GitHub — takes 30 seconds.{R}")
input("  Done? Press ENTER to continue...")

# ── Step 2: HF Token ─────────────────────────────────────────
p(f"\n{B}STEP 2 of 3 — Create a write token{R}")
input("  Press ENTER to open your HF token settings...")
webbrowser.open("https://huggingface.co/settings/tokens")
time.sleep(2)
p(f"  {Y}Click 'New token' → name it 'github-actions' → select 'Write' → Create{R}")
p(f"  {Y}Copy the token (starts with hf_...){R}")
hf_token = input("  Paste your HF token here: ").strip()

if not hf_token.startswith("hf_"):
    p(f"  {Y}Warning: token doesn't start with 'hf_' — double-check it.{R}")

hf_username = input("  Enter your HF username (same as HuggingFace profile name): ").strip()

# ── Step 3: Add GitHub Secrets ───────────────────────────────
p(f"\n{B}STEP 3 of 3 — Add secrets to GitHub{R}")
p(f"  Opening GitHub secrets page...")
input("  Press ENTER to open GitHub Actions secrets...")
webbrowser.open(f"https://github.com/{REPO}/settings/secrets/actions/new")
time.sleep(2)

p(f"""
  {Y}Add these 2 secrets (one at a time):{R}

  Secret 1:
    Name:  HF_TOKEN
    Value: {hf_token[:8]}{'*' * (len(hf_token)-8)}

  Secret 2:
    Name:  HF_USERNAME
    Value: {hf_username}

  {Y}Click 'Add secret' after each one.{R}
""")
input("  Done adding both secrets? Press ENTER to trigger first deployment...")

# ── Trigger deploy ────────────────────────────────────────────
p(f"\n{B}Triggering deployment via git push...{R}")
try:
    base = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "chore: trigger initial HF deployment"],
        cwd=base, capture_output=True, text=True
    )
    subprocess.run(["git", "push"], cwd=base, check=True)
    p(f"  {G}Push successful!{R}")
except Exception as e:
    p(f"  {Y}Could not auto-push: {e}{R}")
    p(f"  Run manually: git push")

# ── Done ──────────────────────────────────────────────────────
live_url = f"https://huggingface.co/spaces/{hf_username}/{SPACE_NAME}"
actions_url = f"https://github.com/{REPO}/actions"

p(f"""
{B}{G}+----------------------------------------------------------+
|   SETUP COMPLETE                                       |
+----------------------------------------------------------+{R}

  {B}GitHub Actions:{R}  {actions_url}
  {B}Live URL:{R}        {live_url}

  {Y}Deployment takes ~3-5 minutes on first run.{R}
  {Y}After that, every 'git push' auto-redeploys in ~1 min.{R}

  {G}Permanent URL:{R}
  {B}{C}{live_url}{R}
""")

webbrowser.open(actions_url)
