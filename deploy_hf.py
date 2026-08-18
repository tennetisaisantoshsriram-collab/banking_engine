"""
deploy_hf.py — Deploy permanently to Hugging Face Spaces.
Free. Permanent URL. One command.

Usage:
    python deploy_hf.py --token YOUR_HF_TOKEN --username YOUR_HF_USERNAME

Get free token:  https://huggingface.co/settings/tokens  (Read/Write scope)
Get free account: https://huggingface.co/join

Result:  https://huggingface.co/spaces/YOUR_USERNAME/banking-credit-engine
"""

import os, sys, argparse, textwrap

SPACE_NAME = "banking-credit-engine"
REPO_FILES = [
    "app.py",
    "requirements.txt",
    "generate_outputs.py",
    "README.md",
    "src/__init__.py",
    "src/data_loader.py",
    "src/feature_engineering.py",
    "src/models/__init__.py",
    "src/models/baseline.py",
    "src/recommender/__init__.py",
    "outputs/roc_curves.png",
    "outputs/confusion_matrix.png",
    "outputs/shap_importance.png",
    "outputs/default_by_grade.png",
    "outputs/eda_overview.png",
    "outputs/pr_curve.png",
    "data/README.txt",
]

# HF Spaces needs app.py at root — already the case.
# HF Spaces needs requirements.txt at root — already the case.

CYAN  = "\033[96m"
GREEN = "\033[92m"
BOLD  = "\033[1m"
RESET = "\033[0m"
YELLOW= "\033[93m"
RED   = "\033[91m"

def banner():
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════╗
║   Banking Credit Risk Engine — HF Spaces Deploy     ║
╚══════════════════════════════════════════════════════╝{RESET}
""")

def main():
    parser = argparse.ArgumentParser(description="Deploy to Hugging Face Spaces")
    parser.add_argument("--token",    required=True, help="HF write token from huggingface.co/settings/tokens")
    parser.add_argument("--username", required=True, help="Your Hugging Face username")
    parser.add_argument("--private",  action="store_true", help="Make the space private")
    args = parser.parse_args()

    banner()

    try:
        from huggingface_hub import HfApi, create_repo, upload_file
    except ImportError:
        print(f"{YELLOW}Installing huggingface_hub...{RESET}")
        os.system(f"{sys.executable} -m pip install huggingface_hub -q")
        from huggingface_hub import HfApi, create_repo, upload_file

    api      = HfApi(token=args.token)
    repo_id  = f"{args.username}/{SPACE_NAME}"
    space_url = f"https://huggingface.co/spaces/{repo_id}"

    # ── Create space ─────────────────────────────────────
    print(f"{BOLD}[1/3] Creating HF Space: {repo_id}{RESET}")
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="streamlit",
            private=args.private,
            token=args.token,
            exist_ok=True,
        )
        print(f"  {GREEN}✓ Space ready{RESET}")
    except Exception as e:
        print(f"{RED}Failed to create space: {e}{RESET}"); sys.exit(1)

    # ── Upload files ─────────────────────────────────────
    print(f"\n{BOLD}[2/3] Uploading files...{RESET}")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploaded = 0
    for rel_path in REPO_FILES:
        local_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(local_path):
            print(f"  {YELLOW}⚠ Skip (not found): {rel_path}{RESET}")
            continue
        try:
            upload_file(
                path_or_fileobj=local_path,
                path_in_repo=rel_path,
                repo_id=repo_id,
                repo_type="space",
                token=args.token,
            )
            print(f"  {GREEN}✓{RESET} {rel_path}")
            uploaded += 1
        except Exception as e:
            print(f"  {RED}✗ {rel_path}: {e}{RESET}")

    # ── Done ─────────────────────────────────────────────
    print(f"""
{BOLD}[3/3] Deployment complete! ({uploaded} files uploaded){RESET}

{BOLD}{GREEN}╔══════════════════════════════════════════════════════╗
║   PERMANENT LIVE URL                                 ║
╠══════════════════════════════════════════════════════╣
║   {space_url:<52} ║
╚══════════════════════════════════════════════════════╝{RESET}

  {YELLOW}Note: First build takes ~3-5 minutes on HF Spaces.{RESET}
  {YELLOW}After that, it stays live permanently for free.{RESET}
""")

if __name__ == "__main__":
    main()
