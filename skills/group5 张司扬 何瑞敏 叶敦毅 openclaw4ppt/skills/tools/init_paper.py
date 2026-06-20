#!/usr/bin/env python3
"""
init_paper.py — Initialize a paper project directory with the standard structure.

Usage:
    python tools/init_paper.py DinoRADE
    python tools/init_paper.py Dark-ISP --arxiv 2509.09183
"""
import os, sys, argparse

def init_paper(paper_name, arxiv_id=None):
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", paper_name)
    
    dirs = [
        "",
        "paper_pages",
        "paper_assets",
        "paper_assets/crop_previews",
    ]
    
    for d in dirs:
        path = os.path.join(base, d)
        os.makedirs(path, exist_ok=True)
    
    # Create README
    with open(os.path.join(base, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"# {paper_name}\n\n")
        if arxiv_id:
            f.write(f"- arXiv: [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})\n")
        f.write(f"\n## Pipeline Status\n\n")
        f.write(f"- [ ] Step 1: Download PDF\n")
        f.write(f"- [ ] Step 2: Analysis report\n")
        f.write(f"- [ ] Step 3: Render pages\n")
        f.write(f"- [ ] Step 4: Locate figures/tables\n")
        f.write(f"- [ ] Step 5: Crop assets\n")
        f.write(f"- [ ] Step 6: Render formulas\n")
        f.write(f"- [ ] Step 7: Generate PPT\n")
    
    print(f"Initialized: {base}")
    for d in dirs:
        print(f"  {os.path.join(base, d) if d else base}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("paper_name", help="Paper project name")
    parser.add_argument("--arxiv", help="arXiv ID (optional)")
    args = parser.parse_args()
    init_paper(args.paper_name, args.arxiv)
