"""utils/brand.py — SalaryIQ logo and brand helpers.

The mark is a rounded square holding three rising bars (a salary ladder)
with a teal crest on the tallest bar.
"""

INK = "#0D1B2A"
AZURE = "#2563EB"
TEAL = "#12B5A6"


def _mark(size: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" '
        f'width="{size}" height="{size}" role="img" aria-label="SalaryIQ logo">'
        '<defs><linearGradient id="sqLogoBg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{AZURE}"/><stop offset="1" stop-color="{TEAL}"/>'
        '</linearGradient></defs>'
        '<rect width="40" height="40" rx="11" fill="url(#sqLogoBg)"/>'
        '<rect x="8.5" y="22" width="6" height="10" rx="2" fill="#fff" fill-opacity=".55"/>'
        '<rect x="17" y="15.5" width="6" height="16.5" rx="2" fill="#fff" fill-opacity=".8"/>'
        '<rect x="25.5" y="8" width="6" height="24" rx="2" fill="#fff"/>'
        f'<circle cx="28.5" cy="8" r="2.6" fill="{INK}" stroke="#fff" stroke-width="1.6"/>'
        '</svg>'
    )


# Icon only, 34px. Other modules import this name.
LOGO_SVG = _mark(34)


def lockup(size: int = 34, dark_bg: bool = False) -> str:
    """Logo mark plus the SalaryIQ wordmark as one inline HTML block."""
    text = "#FFFFFF" if dark_bg else INK
    font = max(16, int(size * 0.62))
    return (
        '<span style="display:inline-flex;align-items:center;gap:10px;">'
        f'{_mark(size)}'
        f'<span style="font-family:Sora,Inter,sans-serif;font-weight:700;'
        f'font-size:{font}px;letter-spacing:-0.02em;color:{text};">'
        f'Salary<span style="color:{TEAL};">IQ</span></span></span>'
    )
