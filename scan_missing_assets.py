"""
scan_missing_assets.py
-----------------------
Scans your index.html and lists all JS, CSS, font, and image paths
that are referenced but likely missing locally.

Usage:
    python scan_missing_assets.py

Place this script in the SAME folder as your index.html, then run it.
It will output:
  1. A full list of all assets found
  2. Which ones are missing locally
  3. Which epam.com URLs to download them from
"""

import os
import re

# ── Config ──────────────────────────────────────────────────────────────────
HTML_FILE = "index.html"          # path to your HTML file
BASE_URL   = "https://www.epam.com"  # origin to build download URLs from
# ────────────────────────────────────────────────────────────────────────────

# Patterns to extract asset paths from HTML
PATTERNS = [
    r'<script[^>]+src=["\']([^"\']+)["\']',          # <script src="">
    r'<link[^>]+href=["\']([^"\']+)["\']',            # <link href="">
    r'url\(["\']?([^"\')\s]+\.(woff2?|ttf|eot|svg))["\']?\)',  # url() in CSS/style
    r'<img[^>]+src=["\']([^"\']+)["\']',              # <img src="">
    r'content=["\']([^"\']+\.(webp|jpg|jpeg|png|gif))["\']',   # meta images
]

# Extensions to flag as assets
ASSET_EXTENSIONS = (
    '.js', '.css', '.woff', '.woff2', '.ttf', '.eot',
    '.svg', '.webp', '.jpg', '.jpeg', '.png', '.gif',
    '.json', '.ico'
)

def extract_paths(html):
    paths = set()
    for pattern in PATTERNS:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            path = match.group(1).strip()
            # Skip data URIs, external http URLs (except same-origin), and empty
            if path.startswith('data:'):
                continue
            if path.lower().endswith(ASSET_EXTENSIONS):
                paths.add(path)
    return sorted(paths)

def is_external(path):
    return path.startswith('http://') or path.startswith('https://')

def to_local_path(path):
    """Convert an absolute path like /etc/designs/... to a relative local path."""
    if is_external(path):
        return None
    # Strip leading slash
    return path.lstrip('/')

def check_missing(paths):
    missing = []
    present = []
    external = []

    for path in paths:
        if is_external(path):
            external.append(path)
            continue
        local = to_local_path(path)
        if os.path.exists(local):
            present.append((path, local))
        else:
            missing.append((path, local))

    return present, missing, external

def main():
    if not os.path.exists(HTML_FILE):
        print(f"❌ Could not find '{HTML_FILE}'. Make sure this script is in the same folder.")
        return

    with open(HTML_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    paths = extract_paths(html)
    present, missing, external = check_missing(paths)

    # ── Report ────────────────────────────────────────────────────────────
    print("=" * 70)
    print(f"  ASSET SCAN REPORT  —  {HTML_FILE}")
    print("=" * 70)

    print(f"\n✅ FOUND LOCALLY ({len(present)} files)")
    print("-" * 50)
    for path, local in present:
        print(f"  {local}")

    print(f"\n❌ MISSING LOCALLY ({len(missing)} files)")
    print("-" * 50)
    for path, local in missing:
        print(f"  Local path : {local}")
        download_url = BASE_URL + '/' + local
        print(f"  Download   : {download_url}")
        print()

    print(f"\n🌐 EXTERNAL / CDN ({len(external)} files — need internet)")
    print("-" * 50)
    for path in external:
        print(f"  {path}")

    # ── Generate download commands ────────────────────────────────────────
    if missing:
        print("\n" + "=" * 70)
        print("  DOWNLOAD COMMANDS (PowerShell — run from your project folder)")
        print("=" * 70)
        for path, local in missing:
            url = BASE_URL + '/' + local
            folder = os.path.dirname(local)
            if folder:
                print(f'New-Item -ItemType Directory -Force -Path "{folder}" | Out-Null')
            print(f'Invoke-WebRequest -Uri "{url}" -OutFile "{local}"')
            print()

        print("\n" + "=" * 70)
        print("  DOWNLOAD COMMANDS (curl / bash — run from your project folder)")
        print("=" * 70)
        for path, local in missing:
            url = BASE_URL + '/' + local
            folder = os.path.dirname(local)
            if folder:
                print(f'mkdir -p "{folder}"')
            print(f'curl -o "{local}" "{url}"')
            print()

    print("\n✅ Scan complete.")

if __name__ == "__main__":
    main()