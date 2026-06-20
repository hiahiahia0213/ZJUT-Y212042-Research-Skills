#!/usr/bin/env python3
"""
search_papers.py — Search arXiv + Semantic Scholar for papers on a topic.
Filters by top venues, outputs structured results, downloads PDFs.

Usage:
    python tools/search_papers.py "low-light object detection" --max 10 --download
    python tools/search_papers.py "underwater detection" --years 2025,2026 --venues CVPR,ICCV,TPAMI
"""
import argparse, json, os, sys, time, urllib.request, urllib.parse, ssl, re
from xml.etree import ElementTree as ET

ctx = ssl._create_unverified_context()
HEADERS = {"User-Agent": "paper-search-bot/1.0"}

TOP_VENUES = {
    "CVPR": "IEEE/CVF Conf. on Computer Vision and Pattern Recognition",
    "ICCV": "IEEE/CVF Intl. Conf. on Computer Vision",
    "ECCV": "European Conf. on Computer Vision",
    "AAAI": "AAAI Conf. on Artificial Intelligence",
    "NeurIPS": "Conf. on Neural Information Processing Systems",
    "ICML": "Intl. Conf. on Machine Learning",
    "TPAMI": "IEEE Trans. on Pattern Analysis and Machine Intelligence",
    "IJCV": "Intl. Journal of Computer Vision",
    "TIP": "IEEE Trans. on Image Processing",
}

def arxiv_search(query, max_results=30, years=None):
    """Search arXiv API."""
    search_q = f"all:{query}"
    params = {
        "search_query": search_q, "start": 0,
        "max_results": max_results, "sortBy": "relevance", "sortOrder": "descending",
    }
    url = f"https://export.arxiv.org/api/query?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    resp = urllib.request.urlopen(req, context=ctx, timeout=30).read().decode()
    root = ET.fromstring(resp)
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    
    papers = []
    for entry in root.findall("a:entry", ns):
        title = (entry.find("a:title", ns).text or "").strip().replace("\n", " ")
        arxiv_id = (entry.find("a:id", ns).text or "").split("/abs/")[-1]
        url_abs = f"https://arxiv.org/abs/{arxiv_id}"
        url_pdf = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        
        published = entry.find("a:published", ns)
        year = published.text[:4] if published is not None else "?"
        
        summary_el = entry.find("a:summary", ns)
        abstract = (summary_el.text or "").strip().replace("\n", " ") if summary_el is not None else ""
        
        cats = [t.get("term") for t in entry.findall("a:category", ns)]
        authors = [a.find("a:name", ns).text for a in entry.findall("a:author", ns) if a.find("a:name", ns) is not None]
        
        # Check journal reference
        journal_ref_el = entry.find("arxiv:journal_ref", {"arxiv": "http://arxiv.org/schemas/atom"})
        journal_ref = (journal_ref_el.text or "") if journal_ref_el is not None else ""
        
        # Check comment for accepted venue
        comment_el = entry.find("arxiv:comment", {"arxiv": "http://arxiv.org/schemas/atom"})
        comment = (comment_el.text or "") if comment_el is not None else ""
        
        venue = "arXiv"
        for vname in TOP_VENUES:
            if vname.lower() in journal_ref.lower() or vname.lower() in comment.lower():
                venue = vname
                break
        
        if years and year not in [str(y) for y in years]:
            continue
        
        papers.append({
            "title": title, "year": year, "venue": venue,
            "url": url_abs, "pdf_url": url_pdf, "arxiv_id": arxiv_id,
            "authors": authors[:3], "abstract": abstract[:300],
            "categories": cats, "journal_ref": journal_ref,
        })
    return papers


def semantic_scholar_search(query, max_results=10, years=None):
    """Search Semantic Scholar API for venue-published papers."""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query, "limit": max_results,
        "fields": "title,year,venue,url,externalIds,publicationDate,citationCount,abstract",
    }
    if years:
        params["year"] = f"{min(years)}-"
    
    try:
        url_full = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url_full, headers=HEADERS)
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
        data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Semantic Scholar error: {e}", file=sys.stderr)
        return []
    
    papers = []
    for p in data.get("data", []):
        title = (p.get("title") or "").encode("ascii", "ignore").decode()
        year = p.get("year", "?")
        venue = (p.get("venue") or "arXiv").encode("ascii", "ignore").decode()
        abstract = (p.get("abstract") or "").encode("ascii", "ignore").decode()
        ext_ids = p.get("externalIds") or {}
        arxiv_id = ext_ids.get("ArXiv", "")
        arxiv_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else (p.get("url") or "")
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else ""
        citations = p.get("citationCount", 0)
        
        papers.append({
            "title": title, "year": year, "venue": venue, "url": arxiv_url,
            "pdf_url": pdf_url, "arxiv_id": arxiv_id, "citations": citations,
            "abstract": abstract[:300],
        })
    return papers


def download_pdf(pdf_url, dest_dir, filename):
    """Download PDF from arXiv."""
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, filename)
    if os.path.exists(dest):
        return dest
    try:
        req = urllib.request.Request(pdf_url, headers=HEADERS)
        data = urllib.request.urlopen(req, context=ctx, timeout=60).read()
        with open(dest, "wb") as f:
            f.write(data)
        return dest
    except Exception as e:
        print(f"  Download failed: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="Search papers on arXiv + Semantic Scholar")
    parser.add_argument("query", help="Search query (topic keywords)")
    parser.add_argument("--max", type=int, default=10, help="Max results per source")
    parser.add_argument("--years", help="Comma-separated years, e.g. 2025,2026")
    parser.add_argument("--venues", help="Comma-separated venues to highlight")
    parser.add_argument("--download", action="store_true", help="Download found PDFs to papers/")
    parser.add_argument("--output", default="outputs/search_results.json", help="Output JSON path")
    args = parser.parse_args()
    
    years = [int(y.strip()) for y in args.years.split(",")] if args.years else None
    
    print(f"Searching: {args.query}")
    print(f"Years: {years or 'all'} | Max: {args.max}")
    print()
    
    # 1. Semantic Scholar (better venue info)
    print("[1/2] Searching Semantic Scholar...")
    time.sleep(2)  # Rate limit buffer
    ss_papers = semantic_scholar_search(args.query, args.max, years)
    print(f"  Found {len(ss_papers)} papers via Semantic Scholar")
    
    # 2. arXiv (better coverage)
    print("[2/2] Searching arXiv...")
    arxiv_papers = arxiv_search(args.query, args.max, years)
    print(f"  Found {len(arxiv_papers)} papers via arXiv")
    
    # Merge and deduplicate
    seen_titles = set()
    all_papers = []
    for p in ss_papers + arxiv_papers:
        key = p["title"].lower()[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            all_papers.append(p)
    
    # Prioritize: top venues first, then by year desc
    venue_rank = {v: i for i, v in enumerate(TOP_VENUES.keys())}
    all_papers.sort(key=lambda p: (venue_rank.get(p.get("venue", ""), 99), -int(p.get("year", "0") or "0"), -(p.get("citations", 0) or 0)))
    
    # Output
    print(f"\n{'='*80}")
    print(f"RESULTS: {len(all_papers)} unique papers")
    print(f"{'='*80}")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    papers_dir = os.path.join(os.path.dirname(base_dir), "papers")
    
    for i, p in enumerate(all_papers, 1):
        venue = p.get("venue", "?")
        year = p.get("year", "?")
        title = p.get("title", "?")[:80]
        arxiv_id = p.get("arxiv_id", "")
        
        # Decide: suggest 精读?
        rec = "⭐ 建议精读" if venue in ["CVPR", "ICCV", "AAAI", "NeurIPS", "ICML", "TPAMI"] else ("✓ 可读" if venue != "arXiv" else "? 预印本")
        
        print(f"\n  [{i}] [{year}] {title}")
        print(f"       Venue: {venue} | {rec}")
        print(f"       URL:   {p.get('url', '')}")
        if arxiv_id:
            print(f"       arXiv: {arxiv_id}")
        if p.get("citations"):
            print(f"       Citations: {p.get('citations')}")
        
        # Download PDF
        if args.download and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            safe_name = f"{arxiv_id}_{title[:40].replace(' ','_').replace(':','').replace('?','')}.pdf"
            safe_name = re.sub(r'[<>:"/\\|?*]', '', safe_name)
            dest = download_pdf(pdf_url, papers_dir, safe_name)
            if dest:
                size_kb = os.path.getsize(dest) // 1024
                print(f"       PDF: {safe_name} ({size_kb} KB)")
    
    # Save JSON
    out_path = os.path.join(os.path.dirname(base_dir), args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_papers, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {out_path}")
    
    return all_papers


if __name__ == "__main__":
    main()
