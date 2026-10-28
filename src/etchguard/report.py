"""Standalone report, all locally generated; not a certified validation."""
import html
import json
from pathlib import Path


def _svg(a,b):
    def path(points):
        coords=[]
        for x,y in points:
            px=32+(x+1.05)/2.1*620
            py=38+(-y)/0.58*155
            coords.append(f"{px:.1f},{py:.1f}")
        return " ".join(coords)
    return f'''<svg viewBox="0 0 680 240" role="img" aria-label="Reference and nearest-recipe baseline profile comparison">
 <rect x="0" y="0" width="680" height="240" rx="16" fill="#101b2b"/>
 <line x1="32" y1="38" x2="652" y2="38" stroke="#516075" stroke-dasharray="5 7"/>
 <polyline fill="none" stroke="#52c7ff" stroke-width="3.5" points="{path(a)}"/>
 <polyline fill="none" stroke="#ffbf72" stroke-width="2.5" stroke-dasharray="8 5" points="{path(b)}"/>
 <text x="34" y="222" fill="#cbd5e1" font-size="13">Cyan: fixture reference | Orange: nearest-recipe prediction | unit: µm</text>
 </svg>'''


def write_html(dest, summary, expected, predicted):
    rows="".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(str(v))}</td></tr>" for k,v in summary["metrics"].items())
    decisions="".join(f'<article class="card"><h3>{html.escape(item["scenario"])}</h3><p class="{ "pass" if item["actual_exit_code"] == item["expected_exit_code"] else "fail"}">Exit {item["actual_exit_code"]} (expected {item["expected_exit_code"]})</p><small>{html.escape(", ".join(item["reasons"]) or "Checks satisfied")}</small></article>' for item in summary["cases"])
    doc=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EtchGuard | Evidence</title>
<style>body{{margin:0;background:#0c1524;color:#e9f0fb;font-family:system-ui,-apple-system,sans-serif}}main{{max-width:980px;margin:auto;padding:34px 22px}}h1{{font-size:32px;letter-spacing:-1px}}p{{line-height:1.55;color:#aebed2}}.eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-size:12px;color:#83d1ff}}.notice{{border:1px solid #95794c;border-radius:12px;padding:14px 20px;background:#282317;color:#fbd29d}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}.card{{background:#142337;border:1px solid #243b57;padding:20px;border-radius:14px}}h3{{font-size:15px}}.pass{{color:#79f0ba;font-weight:800}}.fail{{color:#f29e99;font-weight:800}}table{{border-collapse:collapse;width:100%;max-width:620px}}th,td{{text-align:left;padding:11px 15px;border-bottom:1px solid #294055}}th{{color:#9fc4dc}}code{{overflow-wrap:anywhere;color:#a3ebee}}footer{{margin-top:28px;font-size:13px;color:#89a1bb}}</style>
<main><div class="eyebrow">U3 / GOAT · individual prototype</div><h1>EtchGuard <span style="color:#7dd3fc">Evidence Report</span></h1>
<div class="notice">SYNTHETIC FIXTURE DEMO ONLY. No ViennaPS run, learned FNO/MGN, fab validation or manufacturing release is established by this report.</div>
<h2>Integrity-first release gate</h2><p>SHA-256 covers full raw file contents and file list. Recipe-key identity is preserved separately. No changes to the source team's frozen ADR are implied.</p>
<div class="grid">{decisions}</div><h2>Baseline metrics (synthetic golden only)</h2><table>{rows}</table>
<h2>Example final profile</h2>{_svg(expected,predicted)}<p>Plot is generated from two synthetic fixture records; no semiconductor physics is simulated.</p>
<h2>Lineage</h2><p>Source: <code>{html.escape(summary['source_type'])}</code></p><p>Golden fingerprint: <code>{html.escape(summary['golden_content_fingerprint'])}</code></p><p>Model: <code>nearest-recipe baseline (non-neural)</code></p>
<footer>Gate thresholds are predeclared tutorial settings. Saved registry history is a functional smoke test, not an approved deployment.</footer></main></html>'''
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(doc,encoding="utf-8")
