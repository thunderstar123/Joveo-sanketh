"""
GitLab Scraper — Multi-Module (Handbook + Directions)
Crawls pages in parallel batches of 20.
Usage:
    python scraper.py --module handbook
    python scraper.py --module directions
"""

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    print("❌ Missing dependency. Run: pip install langchain-text-splitters")
    exit(1)

# ============================================
# MODULE CONFIGURATIONS
# ============================================
MODULES = {
    "handbook": {
        "name": "GitLab Handbook",
        "root_url": "https://handbook.gitlab.com/handbook/",
        "domain": "handbook.gitlab.com",
        "path_prefix": "/handbook/",
        "output_file": "handbook_chunks.json",
        "stats_file": "handbook_stats.json",
        "urls_file": "handbook_urls.txt",
    },
    "directions": {
        "name": "GitLab Direction",
        "root_url": "https://about.gitlab.com/direction/",
        "domain": "about.gitlab.com",
        "path_prefix": "/direction/",
        "output_file": "directions_chunks.json",
        "stats_file": "directions_stats.json",
        "urls_file": "directions_urls.txt",
    },
}

# Config
OUTPUT_DIR = os.path.join("data", "scraped")
BATCH_SIZE = 20
UNLIMITED = False
SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})


def is_valid_url(url, module_config):
    """Check if URL belongs to the given module."""
    parsed = urlparse(url)
    if parsed.netloc not in (module_config["domain"], ''):
        return False
    if not parsed.path.startswith(module_config["path_prefix"]):
        return False
    skip = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.css', '.js', '.xml', '.json')
    return not any(parsed.path.endswith(ext) for ext in skip)


def discover_seed_urls(module_config):
    """Dynamically discover sections from the root page's navigation."""
    root_url = module_config["root_url"]
    print(f"🌐 Discovering {module_config['name']} sections from root page...")
    try:
        resp = SESSION.get(root_url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        seeds = set()
        seeds.add(root_url)

        for a in soup.find_all('a', href=True):
            full_url = urljoin(root_url, a['href'])
            parsed = urlparse(full_url)
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if not clean_url.endswith('/'):
                clean_url += '/'
            if is_valid_url(clean_url, module_config):
                seeds.add(clean_url)

        print(f"✓ Discovered {len(seeds)} seed URLs dynamically")

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        seed_file = os.path.join(OUTPUT_DIR, module_config["urls_file"])
        with open(seed_file, 'w', encoding='utf-8') as f:
            for url in sorted(seeds):
                f.write(url + '\n')
        print(f"✓ Saved URL list to {seed_file}")

        return list(seeds)

    except Exception as e:
        print(f"⚠ Failed to discover seeds ({e}), using root URL only")
        return [root_url]


def clean_text(text):
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def get_section_from_url(url, module_config):
    """Extract section name from URL based on module's path prefix."""
    path = urlparse(url).path.strip('/')
    # Remove the module prefix
    prefix = module_config["path_prefix"].strip('/')
    if path.startswith(prefix):
        path = path[len(prefix):].strip('/')
    parts = [p.replace('-', ' ').replace('_', ' ').title() for p in path.split('/') if p]
    if parts:
        return ' > '.join(parts[-2:]) if len(parts) > 1 else parts[0]
    return module_config["name"]


def discover_links(soup, current_url, module_config):
    links = set()
    for a in soup.find_all('a', href=True):
        full_url = urljoin(current_url, a['href'])
        parsed = urlparse(full_url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if not clean_url.endswith('/'):
            clean_url += '/'
        if is_valid_url(clean_url, module_config):
            links.add(clean_url)
    return links


def scrape_page(url, module_config):
    """Scrape a single page. Returns (sections_list, discovered_links) or (None, set())."""
    try:
        resp = SESSION.get(url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Discover links BEFORE decomposing anything
        discovered = discover_links(soup, url, module_config)

        # Module-specific cleanup:
        # - Handbook (handbook.gitlab.com): decompose nav/header/footer (content is in <main>)
        # - Directions (about.gitlab.com): only decompose script/style (content is in body-level divs)
        is_directions = module_config.get("domain") == "about.gitlab.com"

        if is_directions:
            # about.gitlab.com pages: content is in body divs, NOT inside <main>
            for el in soup.find_all(['script', 'style']):
                el.decompose()
            # Remove only the site-level navigation bar (top navbar)
            site_nav = soup.find('nav', class_=re.compile(r'navbar|nav-bar|site-nav|main-nav', re.I))
            if site_nav:
                site_nav.decompose()
            # Use body as root since content is scattered across body-level divs
            main = soup.body
        else:
            # Handbook pages: original logic (works perfectly)
            for el in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
                el.decompose()
            main = (
                soup.find('main') or soup.find('article') or
                soup.find('div', class_=re.compile(r'content|main|article', re.I)) or
                soup.body
            )

        if not main:
            return None, set()

        section_name = get_section_from_url(url, module_config)
        sections = []
        cur_header = section_name
        cur_text = []

        for el in main.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'td', 'th']):
            if el.name in ['h1', 'h2', 'h3', 'h4']:
                if cur_text:
                    text = clean_text('\n'.join(cur_text))
                    if len(text) > 50:
                        sections.append({'header': cur_header, 'text': text, 'url': url, 'section': section_name})
                cur_header = clean_text(el.get_text())
                cur_text = []
            else:
                t = clean_text(el.get_text())
                if t and len(t) > 10:
                    cur_text.append(t)

        if cur_text:
            text = clean_text('\n'.join(cur_text))
            if len(text) > 50:
                sections.append({'header': cur_header, 'text': text, 'url': url, 'section': section_name})

        if not sections:
            all_text = clean_text(main.get_text())
            if len(all_text) > 100:
                sections.append({'header': section_name, 'text': all_text[:5000], 'url': url, 'section': section_name})

        return sections, discovered

    except Exception:
        return None, set()


def chunk_text(text, chunk_size=2000, overlap=300):
    """Split text into chunks by semantic boundaries."""
    if not text:
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)


def run_scraper(module_key):
    """Run the scraper for a given module."""
    if module_key not in MODULES:
        print(f"❌ Unknown module: {module_key}. Choose from: {list(MODULES.keys())}")
        exit(1)

    config = MODULES[module_key]
    print(f"🔍 {config['name']} Crawler (Max Speed)")
    print("=" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    to_visit = discover_seed_urls(config)
    visited = set()
    all_chunks = []
    chunk_id = 0
    total_scraped = 0

    while to_visit:
        batch = []
        while to_visit and len(batch) < BATCH_SIZE:
            url = to_visit.pop(0)
            if url not in visited:
                batch.append(url)
                visited.add(url)
        if not batch:
            break

        total_scraped += len(batch)
        print(f"\n⚡ Batch [{total_scraped - len(batch) + 1}-{total_scraped}] ({len(batch)} pages, {len(to_visit)} queued)...")

        results = {}
        with ThreadPoolExecutor(max_workers=BATCH_SIZE) as pool:
            futures = {pool.submit(scrape_page, u, config): u for u in batch}
            for f in as_completed(futures):
                url = futures[f]
                try:
                    results[url] = f.result()
                except Exception:
                    results[url] = (None, set())

        batch_chunks = 0
        for url in batch:
            r = results.get(url, (None, set()))

            if r[0] is None:
                continue

            sections, links = r
            if sections:
                for sec in sections:
                    for j, ch in enumerate(chunk_text(sec['text'])):
                        all_chunks.append({
                            'id': f"chunk_{chunk_id}",
                            'text': ch,
                            'header': sec['header'],
                            'url': sec['url'],
                            'section': sec['section'],
                            'module': module_key,
                            'chunk_index': j,
                            'total_chunks': -1
                        })
                        chunk_id += 1
                        batch_chunks += 1

            if UNLIMITED:
                to_visit.extend(links - visited)

        print(f"  ✓ {batch_chunks} chunks from this batch (total: {len(all_chunks)} chunks, {total_scraped} pages)")

    # Save
    out = os.path.join(OUTPUT_DIR, config["output_file"])
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    stats = {
        'module': module_key,
        'module_name': config['name'],
        'total_pages_scraped': len(visited),
        'total_chunks': len(all_chunks),
        'sections': sorted(set(c['section'] for c in all_chunks)),
        'avg_chunk_length': sum(len(c['text']) for c in all_chunks) // max(len(all_chunks), 1),
    }
    with open(os.path.join(OUTPUT_DIR, config["stats_file"]), 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"✅ Done! {len(visited)} pages → {len(all_chunks)} chunks")
    print(f"   Saved to: {out}")


def main():
    # Parse --module argument
    module_key = "handbook"  # default
    if "--module" in sys.argv:
        idx = sys.argv.index("--module")
        if idx + 1 < len(sys.argv):
            module_key = sys.argv[idx + 1].lower()
        else:
            print("❌ --module requires a value: handbook or directions")
            exit(1)

    run_scraper(module_key)


if __name__ == "__main__":
    main()