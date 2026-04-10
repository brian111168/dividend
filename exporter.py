"""
exporter.py
PNG 截圖 + 加密 PDF 匯出
"""
from __future__ import annotations
import io
import os
import tempfile
import subprocess
import sys
import webbrowser
import os

# ── PNG：用 playwright 或 weasyprint headless 渲染 ──────────────────


import subprocess

def html_to_png_bytes(html: str, filename="report.html") -> bytes:
    path = os.path.abspath(filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    # Chrome print mode
    webbrowser.open("file://" + path + "#print")
    
def html_to_pdf_bytes(html: str, filename="report.html") -> bytes:
    path = os.path.abspath(filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    # Chrome print mode
    webbrowser.open("file://" + path + "#print")



def export_png(html: str) -> bytes:
    return html_to_png_bytes(html)


def export_pdf(html: str, password: str = "") -> bytes:
    pdf_bytes = html_to_pdf_bytes(html)
    return 
