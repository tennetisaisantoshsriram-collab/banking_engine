"""
Auto-deploy to Hugging Face Spaces.
Called by GitHub Actions — reads HF_TOKEN and HF_USERNAME from env.
"""
import os, sys

HF_TOKEN    = os.environ.get("HF_TOKEN", "").strip()
HF_USERNAME = os.environ.get("HF_USERNAME", "").strip()
SPACE_NAME  = "banking-credit-engine"

if not HF_TOKEN:
    print("ERROR: HF_TOKEN secret not set in GitHub repo.")
    print("Go to: Settings > Secrets > Actions > New secret > HF_TOKEN")
    sys.exit(1)
if not HF_USERNAME:
    print("ERROR: HF_USERNAME secret not set in GitHub repo.")
    sys.exit(1)

from huggingface_hub import HfApi, create_repo, upload_folder

repo_id   = f"{HF_USERNAME}/{SPACE_NAME}"
space_url = f"https://huggingface.co/spaces/{repo_id}"

print(f"Deploying to: {space_url}")

api = HfApi(token=HF_TOKEN)

# Create/ensure the space exists
print("[1/2] Creating/updating HF Space...")
create_repo(
    repo_id=repo_id,
    repo_type="space",
    space_sdk="streamlit",
    token=HF_TOKEN,
    exist_ok=True,
    private=False,
)
print("      Space ready.")

# Upload entire repo (excluding ignored files)
print("[2/2] Uploading files...")
upload_folder(
    folder_path=".",
    repo_id=repo_id,
    repo_type="space",
    token=HF_TOKEN,
    ignore_patterns=[
        ".git/*", ".git/**/*",
        ".github/*", ".github/**/*",
        ".cf/*", ".cf/**/*",
        "__pycache__/*", "**/__pycache__/*",
        "*.pyc", "*.pyo",
        "venv/*", "venv/**/*",
        "artifacts/*",
        "data/*.csv",
        "*.zip",
        ".pytest_cache/*",
        ".ipynb_checkpoints/*",
        "create_notebook.py",
    ],
    commit_message=f"Auto-deploy from GitHub Actions",
)
print("      Upload complete.")
print(f"\nLIVE URL: {space_url}")
