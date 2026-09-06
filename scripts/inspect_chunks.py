"""
Quick chunk inspection script — prints exactly how the ingestion
pipeline breaks your documents into sections and chunks.

Usage:
    python -m tests.inspect_chunks
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from rag.ingest import extract_sections, text_splitter

PROJECT_ROOT = Path(__file__).parent.parent
UPLOADS_DIR = PROJECT_ROOT / "uploads"


def inspect_file(file_path: Path):
    print(f"\n{'=' * 80}")
    print(f"  FILE: {file_path.name}")
    print(f"{'=' * 80}")

    sections = extract_sections(str(file_path))
    print(f"\n  Extracted {len(sections)} raw sections from parser\n")

    total_chunks = 0
    for s_idx, section in enumerate(sections):
        chunks = text_splitter.split_text(section["text"])
        total_chunks += len(chunks)

        print(f"  -- Section {s_idx}: \"{section['section']}\" "
              f"({len(chunks)} chunk{'s' if len(chunks) != 1 else ''}) --")

        for c_idx, chunk in enumerate(chunks):
            size = len(chunk)
            tag = ""
            if size < 10:
                tag = " ⚠️ TINY"
            elif size > 1000:
                tag = " ⚠️ OVERSIZED"

            preview = chunk.replace("\n", " ↵ ")
            if len(preview) > 120:
                preview = preview[:120] + "..."

            print(f"    [{c_idx}] ({size:4d} chars){tag}  {preview}")

        print()

    print(f"  TOTAL: {total_chunks} chunks across {len(sections)} sections")
    print(f"  Sizes: ", end="")
    all_sizes = []
    for section in sections:
        for chunk in text_splitter.split_text(section["text"]):
            all_sizes.append(len(chunk))
    if all_sizes:
        print(f"min={min(all_sizes)}, max={max(all_sizes)}, "
              f"avg={sum(all_sizes)//len(all_sizes)}, "
              f"tiny(<10)={sum(1 for s in all_sizes if s < 10)}")
    print()


if __name__ == "__main__":
    files = sorted(UPLOADS_DIR.iterdir())
    if not files:
        print("No files found in uploads/")
    else:
        print(f"Found {len(files)} files in uploads/\n")
        for f in files:
            if f.is_file():
                inspect_file(f)
