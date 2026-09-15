"""
Terminal Formatting & Visual Table Utilities
Renders clean ASCII tables, execution summaries, and status banners for Review 2 demos.
"""

from typing import List, Dict, Any, Optional


class Visualizer:
    """Provides formatted console display utilities."""

    @staticmethod
    def banner(title: str, subtitle: Optional[str] = None, width: int = 72) -> str:
        border = "=" * width
        lines = [border, f"  {title}".center(width)]
        if subtitle:
            lines.append(f"  {subtitle}".center(width))
        lines.append(border)
        return "\n".join(lines)

    @staticmethod
    def section_header(title: str, char: str = "-", width: int = 72) -> str:
        return f"\n{title}\n" + (char * len(title))

    @staticmethod
    def format_table(headers: List[str], rows: List[List[Any]], alignments: Optional[List[str]] = None) -> str:
        """
        Renders a clean ASCII table with proper column alignments ('<', '>', '^').
        """
        if not rows:
            return "No data to display."

        alignments = alignments or ["<"] * len(headers)
        str_rows = [[str(cell) for cell in row] for row in rows]

        # Calculate max column widths
        col_widths = [len(h) for h in headers]
        for row in str_rows:
            for idx, cell in enumerate(row):
                if idx < len(col_widths):
                    col_widths[idx] = max(col_widths[idx], len(cell))

        # Format header
        header_cells = []
        for h, w, align in zip(headers, col_widths, alignments):
            if align == ">":
                header_cells.append(h.rjust(w))
            elif align == "^":
                header_cells.append(h.center(w))
            else:
                header_cells.append(h.ljust(w))

        header_line = " | ".join(header_cells)
        sep_line = "-+-".join("-" * w for w in col_widths)

        # Format rows
        formatted_rows = []
        for row in str_rows:
            cells = []
            for cell, w, align in zip(row, col_widths, alignments):
                if align == ">":
                    cells.append(cell.rjust(w))
                elif align == "^":
                    cells.append(cell.center(w))
                else:
                    cells.append(cell.ljust(w))
            formatted_rows.append(" | ".join(cells))

        return f"\n{header_line}\n{sep_line}\n" + "\n".join(formatted_rows) + "\n"

    @staticmethod
    def format_features(features: Dict[str, float]) -> str:
        """Renders static features in a compact 2-column format."""
        items = list(features.items())
        half = (len(items) + 1) // 2
        col1 = items[:half]
        col2 = items[half:]

        lines = ["\n[Program Static IR Features]"]
        for (k1, v1), (k2, v2) in zip(col1, col2):
            v1_str = f"{v1:.0f}" if v1.is_integer() else f"{v1:.4f}"
            v2_str = f"{v2:.0f}" if v2.is_integer() else f"{v2:.4f}"
            lines.append(f"  • {k1:<20} {v1_str:>8}    │  • {k2:<20} {v2_str:>8}")

        # If odd number of features
        if len(col1) > len(col2):
            k1, v1 = col1[-1]
            v1_str = f"{v1:.0f}" if v1.is_integer() else f"{v1:.4f}"
            lines.append(f"  • {k1:<20} {v1_str:>8}")

        return "\n".join(lines)
