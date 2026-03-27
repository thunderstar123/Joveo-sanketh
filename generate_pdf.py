"""
GitLab → PDF Generator (Multi-Module)
Converts scraped data into a nicely structured PDF book.
Usage:
    python generate_pdf.py --module handbook
    python generate_pdf.py --module directions
"""

import json
import os
import sys
import re
from collections import defaultdict

try:
    from fpdf import FPDF
except ImportError:
    print("❌ Missing dependency. Run: pip install fpdf2")
    exit(1)

SCRAPED_DIR = os.path.join("data", "scraped")

MODULE_PDF_CONFIG = {
    "handbook": {
        "input_file": "handbook_chunks.json",
        "output_file": os.path.join("data", "GitLab_Handbook.pdf"),
        "title": "GitLab Handbook",
        "subtitle_1": "A Comprehensive Guide to GitLab's Culture,",
        "subtitle_2": "Values, Processes, and Practices",
        "source_label": "Source: handbook.gitlab.com",
        "header_label": "GitLab Handbook",
    },
    "directions": {
        "input_file": "directions_chunks.json",
        "output_file": os.path.join("data", "GitLab_Directions.pdf"),
        "title": "GitLab Direction",
        "subtitle_1": "A Comprehensive Guide to GitLab's Product",
        "subtitle_2": "Strategy, Roadmap, and Investment Themes",
        "source_label": "Source: about.gitlab.com/direction",
        "header_label": "GitLab Direction",
    },
}


class ModulePDF(FPDF):
    """Custom PDF class with headers, footers, and GitLab styling."""

    def __init__(self, header_label="GitLab"):
        super().__init__()
        self._header_label = header_label
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(130, 130, 130)
            self.cell(0, 10, self._header_label, align="L")
            self.ln(5)
            self.set_draw_color(200, 200, 200)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_cover_page(self, title, subtitle_1, subtitle_2, source_label, total_sections, total_pages):
        """Add a styled cover page."""
        self.add_page()

        # GitLab orange accent bar
        self.set_fill_color(252, 109, 38)
        self.rect(0, 0, 210, 8, "F")

        # Purple accent bar
        self.set_fill_color(107, 79, 187)
        self.rect(0, 8, 210, 3, "F")

        # Title
        self.ln(60)
        self.set_font("Helvetica", "B", 36)
        self.set_text_color(44, 44, 44)
        self.cell(0, 20, title, align="C", new_x="LMARGIN", new_y="NEXT")

        # Subtitle
        self.ln(5)
        self.set_font("Helvetica", "", 16)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, subtitle_1, align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 10, subtitle_2, align="C", new_x="LMARGIN", new_y="NEXT")

        # Divider
        self.ln(10)
        self.set_draw_color(252, 109, 38)
        self.set_line_width(0.8)
        self.line(60, self.get_y(), 150, self.get_y())
        self.ln(15)

        # Stats
        self.set_font("Helvetica", "", 11)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, f"Sections: {total_sections}  |  Source Pages: {total_pages}", align="C", new_x="LMARGIN", new_y="NEXT")

        # Source
        self.ln(5)
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(107, 79, 187)
        self.cell(0, 8, source_label, align="C", new_x="LMARGIN", new_y="NEXT")

        # Bottom bar
        self.set_fill_color(252, 109, 38)
        self.rect(0, 289, 210, 8, "F")

    def add_toc(self, sections_dict):
        """Add a table of contents page."""
        self.add_page()
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(44, 44, 44)
        self.cell(0, 15, "Table of Contents", new_x="LMARGIN", new_y="NEXT")

        self.set_draw_color(252, 109, 38)
        self.set_line_width(0.6)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(10)

        self.set_font("Helvetica", "", 10)
        self.set_text_color(60, 60, 60)

        for i, (section_name, _) in enumerate(sections_dict.items(), 1):
            if self.get_y() > 270:
                self.add_page()
                self.ln(10)
            display = section_name if len(section_name) < 70 else section_name[:67] + "..."
            self.cell(0, 7, f"  {i}.  {display}", new_x="LMARGIN", new_y="NEXT")

    def add_section_title(self, title):
        """Add a major section title."""
        self.add_page()

        self.set_fill_color(252, 109, 38)
        self.rect(10, self.get_y(), 4, 14, "F")

        self.set_x(18)
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(44, 44, 44)
        self.multi_cell(0, 14, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def add_subsection(self, header, text, url):
        """Add a subsection with header and body text."""
        if self.get_y() > 250:
            self.add_page()

        self.set_font("Helvetica", "B", 12)
        self.set_text_color(107, 79, 187)
        safe_header = header.encode('latin-1', errors='replace').decode('latin-1')
        self.multi_cell(0, 7, safe_header, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)

        safe_text = text.encode('latin-1', errors='replace').decode('latin-1')

        paragraphs = safe_text.split('\n')
        for para in paragraphs:
            para = para.strip()
            if para:
                self.multi_cell(0, 5, para, new_x="LMARGIN", new_y="NEXT")
                self.ln(2)

        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        safe_url = url.encode('latin-1', errors='replace').decode('latin-1')
        self.cell(0, 5, f"Source: {safe_url}", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)


def organize_by_section(chunks):
    """Group chunks by section, preserving order."""
    sections = defaultdict(list)
    seen = set()

    for chunk in chunks:
        section = chunk['section']
        key = (section, chunk['header'], chunk['text'][:100])
        if key not in seen:
            seen.add(key)
            sections[section].append(chunk)

    return dict(sections)


def main():
    # Parse --module argument
    module_key = "handbook"
    if "--module" in sys.argv:
        idx = sys.argv.index("--module")
        if idx + 1 < len(sys.argv):
            module_key = sys.argv[idx + 1].lower()
        else:
            print("❌ --module requires a value: handbook or directions")
            exit(1)

    if module_key not in MODULE_PDF_CONFIG:
        print(f"❌ Unknown module: {module_key}. Choose from: {list(MODULE_PDF_CONFIG.keys())}")
        exit(1)

    pdf_config = MODULE_PDF_CONFIG[module_key]

    print(f"📄 {pdf_config['title']} → PDF Generator")
    print("=" * 50)

    # Load scraped data
    input_path = os.path.join(SCRAPED_DIR, pdf_config["input_file"])
    if not os.path.exists(input_path):
        print(f"❌ Scraped data not found at {input_path}")
        print(f"   Run scraper.py first: python scraper.py --module {module_key}")
        exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    print(f"✓ Loaded {len(chunks)} chunks")

    # Organize by section
    sections = organize_by_section(chunks)
    total_pages = len(set(c['url'] for c in chunks))
    print(f"✓ Organized into {len(sections)} sections from {total_pages} pages")

    # Create PDF
    print(f"\n📝 Generating PDF...")
    pdf = ModulePDF(header_label=pdf_config["header_label"])
    pdf.alias_nb_pages()

    # Cover page
    pdf.add_cover_page(
        title=pdf_config["title"],
        subtitle_1=pdf_config["subtitle_1"],
        subtitle_2=pdf_config["subtitle_2"],
        source_label=pdf_config["source_label"],
        total_sections=len(sections),
        total_pages=total_pages,
    )

    # Table of contents
    pdf.add_toc(sections)

    # Content sections
    for i, (section_name, section_chunks) in enumerate(sections.items(), 1):
        print(f"  [{i}/{len(sections)}] {section_name} ({len(section_chunks)} entries)")

        pdf.add_section_title(section_name)

        for chunk in section_chunks:
            pdf.add_subsection(
                header=chunk['header'],
                text=chunk['text'],
                url=chunk['url']
            )

    # Save PDF
    output_pdf = pdf_config["output_file"]
    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
    pdf.output(output_pdf)

    file_size = os.path.getsize(output_pdf) / (1024 * 1024)
    print(f"\n{'=' * 50}")
    print(f"✅ PDF Generated!")
    print(f"  File: {output_pdf}")
    print(f"  Size: {file_size:.1f} MB")
    print(f"  Pages: {pdf.page_no()}")


if __name__ == "__main__":
    main()
