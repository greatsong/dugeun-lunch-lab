import base64
import html
from contextlib import nullcontext

import streamlit as st
import streamlit.components.v1 as components


def download(target, label, data, filename, mime, disabled=False):
    """Keep the download in the browser that generated the file."""
    if disabled:
        return
    raw = data.encode("utf-8") if isinstance(data, str) else data
    payload = base64.b64encode(raw).decode("ascii")
    with nullcontext() if target is st else target:
        components.html(
            '<html lang="ko"><head><meta charset="utf-8"><style>'
            'body{margin:0}a{display:inline-block;background:#f6faf5;border:1px solid #a5bdad;'
            'border-radius:8px;padding:8px 13px;color:#185538;text-decoration:none;'
            'font:600 15px/1.4 system-ui,sans-serif}a:hover{background:#dfeee3}'
            '</style></head><body>'
            f'<a download="{html.escape(filename, quote=True)}" href="data:{mime};base64,{payload}">'
            f'{html.escape(label)}</a></body></html>', height=43)
