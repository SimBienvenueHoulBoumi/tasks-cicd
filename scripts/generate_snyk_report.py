import json
from pathlib import Path
from html import escape


def load_snyk_json(path: Path):
    """
    Charge le JSON Snyk.
    Gère à la fois un JSON unique et un fichier avec plusieurs lignes JSON (cas CLI).
    """
    if not path.exists():
        print(f"❌ Fichier Snyk introuvable: {path}")
        return None

    content = path.read_text(errors="ignore")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback : essayer ligne par ligne (comme pour Trivy)
        for line in reversed(content.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        print("❌ Aucun JSON valide trouvé dans le rapport Snyk.")
        return None


def render_html(data: dict) -> str:
    """
    Génère un rapport HTML Snyk avec Tailwind CSS (via CDN).
    """
    vulns = data.get("vulnerabilities", [])

    # Cas sans vulnérabilités : belle page "tout est vert"
    if not vulns:
        return """<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>Rapport Snyk</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center p-6">
    <main class="max-w-2xl w-full bg-slate-900/80 border border-slate-800 rounded-2xl shadow-2xl shadow-slate-900/80 p-8">
      <header class="mb-6">
        <p class="text-xs font-semibold tracking-[0.25em] text-emerald-400/80 uppercase">Snyk</p>
        <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-50">Rapport Snyk</h1>
        <p class="mt-1 text-sm text-slate-400">Analyse des dépendances de votre projet.</p>
      </header>

      <section class="mt-4 flex items-center gap-3 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-300">
          <span class="text-lg">✔</span>
        </div>
        <div>
          <p class="text-sm font-semibold text-emerald-300">Aucune vulnérabilité détectée</p>
          <p class="text-xs text-emerald-200/80">
            Snyk n’a remonté aucun problème sur ce scan. Continuez à surveiller vos dépendances à chaque build.
          </p>
        </div>
      </section>
    </main>
  </body>
</html>"""

    # Compter les vulnérabilités par sévérité
    severities = ["critical", "high", "medium", "low"]
    counts = {s: 0 for s in severities}
    for v in vulns:
        sev = (v.get("severity") or "").lower()
        if sev in counts:
            counts[sev] += 1

    def sev_badge_color(sev: str) -> str:
        return {
            "critical": "bg-rose-500/10 text-rose-300 border-rose-400/70",
            "high": "bg-red-500/10 text-red-300 border-red-400/70",
            "medium": "bg-amber-500/10 text-amber-300 border-amber-400/70",
            "low": "bg-sky-500/10 text-sky-300 border-sky-400/70",
        }.get(sev.lower(), "bg-slate-700/40 text-slate-200 border-slate-500/60")

    def sev_summary_color(sev: str) -> str:
        return {
            "critical": "text-rose-400",
            "high": "text-red-400",
            "medium": "text-amber-400",
            "low": "text-sky-300",
        }.get(sev.lower(), "text-slate-300")

    rows = []
    for v in vulns:
        sev = (v.get("severity") or "").lower()
        pkg = v.get("packageName") or v.get("moduleName") or "n/a"
        version = v.get("version") or "?"
        title = v.get("title") or v.get("name") or ""
        id_ = v.get("id") or ""
        from_chain = " → ".join(v.get("from", [])) if v.get("from") else ""
        url = v.get("url") or ""

        rows.append(f"""
        <article class="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3 sm:px-5 sm:py-4 flex flex-col sm:flex-row gap-3 sm:gap-4">
          <div class="sm:w-32 flex-shrink-0">
            <span class="inline-flex items-center justify-center rounded-full border px-3 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.18em] {sev_badge_color(sev)}">
              {escape(sev or "unknown")}
            </span>
          </div>
          <div class="flex-1 space-y-1">
            <h3 class="text-sm font-semibold text-slate-50">
              {escape(title or id_)}
            </h3>
            <p class="text-xs text-slate-400">
              ID&nbsp;: <span class="font-mono text-slate-200">{escape(id_ or "N/A")}</span>
            </p>
            <div class="mt-1 flex flex-wrap gap-2 text-[0.7rem] text-slate-300">
              <span class="inline-flex items-center rounded-full border border-slate-700/80 bg-slate-900/80 px-2.5 py-0.5">
                <span class="mr-1 text-slate-400">Package</span>
                <span class="font-mono">{escape(pkg)}@{escape(str(version))}</span>
              </span>
              {f"<span class='inline-flex items-center rounded-full border border-slate-700/80 bg-slate-900/80 px-2.5 py-0.5'><span class='mr-1 text-slate-400'>Chemin</span><span class='truncate max-w-xs'>{escape(from_chain)}</span></span>" if from_chain else ""}
            </div>
            {f"<p class='mt-1 text-[0.7rem]'><a href='{escape(url)}' target='_blank' rel='noopener noreferrer' class='text-sky-300 hover:text-sky-200 underline underline-offset-4 decoration-sky-500/70'>Voir le détail sur Snyk ↗</a></p>" if url else ""}
          </div>
        </article>
        """)

    html = f"""<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>Rapport Snyk</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="min-h-screen bg-slate-950 text-slate-50 p-4 sm:p-6">
    <main class="mx-auto max-w-5xl space-y-5">
      <header class="rounded-2xl border border-slate-800 bg-slate-900/80 px-6 py-5 shadow-2xl shadow-slate-950/70">
        <p class="text-xs font-semibold tracking-[0.25em] text-violet-400/80 uppercase">Snyk</p>
        <div class="mt-1 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 class="text-2xl font-bold tracking-tight text-slate-50">Rapport Snyk</h1>
            <p class="text-xs sm:text-sm text-slate-400">
              Analyse des vulnérabilités dans les dépendances du projet.
            </p>
          </div>
          <div class="mt-2 flex gap-2 text-[0.7rem] sm:text-xs text-slate-400">
            <span class="inline-flex items-center rounded-full border border-slate-700/80 bg-slate-900/90 px-3 py-1">
              Total&nbsp;: <span class="ml-1 font-semibold text-slate-100">{len(vulns)}</span>
            </span>
          </div>
        </div>
      </header>

      <section class="grid gap-3 sm:grid-cols-4">
        <div class="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3">
          <p class="text-[0.7rem] uppercase tracking-[0.18em] text-slate-400">Critiques</p>
          <p class="mt-1 text-xl font-semibold {sev_summary_color("critical")}">{counts["critical"]}</p>
        </div>
        <div class="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3">
          <p class="text-[0.7rem] uppercase tracking-[0.18em] text-slate-400">Hautes</p>
          <p class="mt-1 text-xl font-semibold {sev_summary_color("high")}">{counts["high"]}</p>
        </div>
        <div class="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3">
          <p class="text-[0.7rem] uppercase tracking-[0.18em] text-slate-400">Moyennes</p>
          <p class="mt-1 text-xl font-semibold {sev_summary_color("medium")}">{counts["medium"]}</p>
        </div>
        <div class="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3">
          <p class="text-[0.7rem] uppercase tracking-[0.18em] text-slate-400">Basses</p>
          <p class="mt-1 text-xl font-semibold {sev_summary_color("low")}">{counts["low"]}</p>
        </div>
      </section>

      <section class="space-y-3">
        {''.join(rows)}
      </section>
    </main>
  </body>
</html>"""
    return html


def render_html_pure(data: dict) -> str:
    """
    Variante du rapport Snyk avec du CSS pur (sans Tailwind) et un rendu clair type dashboard.
    """
    vulns = data.get("vulnerabilities", [])

    # Compter par sévérité
    severities = ["critical", "high", "medium", "low"]
    counts = {s: 0 for s in severities}
    for v in vulns:
        sev = (v.get("severity") or "").lower()
        if sev in counts:
            counts[sev] += 1

    # Lignes de tableau
    rows = []
    for v in vulns:
        sev = (v.get("severity") or "").upper()
        pkg = v.get("packageName") or v.get("moduleName") or "n/a"
        version = v.get("version") or "?"
        title = v.get("title") or v.get("name") or ""
        id_ = v.get("id") or ""
        url = v.get("url") or ""

        rows.append(
            f"<tr>"
            f"<td class='sev sev-{escape(sev.lower())}'>{escape(sev)}</td>"
            f"<td class='col-main'>"
            f"<div class='v-title'>{escape(title or id_)}</div>"
            f"<div class='v-meta'>"
            f"<span class='chip'><span class='chip-label'>ID</span><span class='chip-value'>{escape(id_ or 'N/A')}</span></span>"
            f"<span class='chip'><span class='chip-label'>Package</span><span class='chip-value'>{escape(pkg)}@{escape(str(version))}</span></span>"
            f"</div>"
        )
        if url:
            rows[-1] += (
                f"<div class='v-link'><a href='{escape(url)}' target='_blank' rel='noopener noreferrer'>Voir le détail sur Snyk ↗</a></div>"
            )
        rows[-1] += "</td></tr>"

    body_rows = "".join(rows) if rows else (
        "<tr><td colspan='2' class='no-data'>Aucune vulnérabilité détectée.</td></tr>"
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>Rapport Snyk</title>
    <style>
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        padding: 24px 16px 32px;
        background: #f3f4f6;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #111827;
      }}
      .page {{
        max-width: 1120px;
        margin: 0 auto;
        display: grid;
        grid-template-columns: minmax(0,1.4fr) minmax(0,1fr);
        gap: 16px;
      }}
      .card {{
        border-radius: 24px;
        background: #ffffff;
        border: 1px solid #e5e7eb;
        box-shadow: 0 22px 60px rgba(148,163,184,0.25);
      }}
      .card-main {{
        padding: 22px 24px 18px;
      }}
      .card-side {{
        padding: 18px 20px;
      }}
      .eyebrow {{
        margin: 0 0 4px;
        font-size: 11px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: #4f46e5;
      }}
      h1 {{
        margin: 0;
        font-size: 22px;
        letter-spacing: 0.03em;
      }}
      .subtitle {{
        margin-top: 4px;
        font-size: 13px;
        color: #6b7280;
      }}
      .summary-grid {{
        margin-top: 16px;
        display: grid;
        grid-template-columns: repeat(4, minmax(0,1fr));
        gap: 10px;
      }}
      .summary-card {{
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        background: #f9fafb;
        padding: 10px 12px;
      }}
      .summary-label {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #9ca3af;
        margin-bottom: 2px;
      }}
      .summary-value {{
        font-size: 18px;
        font-weight: 700;
      }}
      .crit {{ color: #b91c1c; }}
      .high {{ color: #dc2626; }}
      .med {{ color: #d97706; }}
      .low {{ color: #0369a1; }}

      table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 18px;
      }}
      thead th {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #9ca3af;
        padding: 0 8px 4px;
        text-align: left;
        border-bottom: 1px solid #e5e7eb;
      }}
      tbody tr + tr td {{
        border-top: 1px solid #f3f4f6;
      }}
      td {{
        padding: 8px;
        vertical-align: top;
        font-size: 13px;
      }}
      .sev {{
        width: 96px;
        font-size: 11px;
        font-weight: 600;
        text-align: center;
        border-radius: 999px;
        padding: 4px 10px;
        border: 1px solid #e5e7eb;
        background: #f9fafb;
      }}
      .sev-critical {{ background:#fef2f2; color:#b91c1c; border-color:#fecaca; }}
      .sev-high {{ background:#fef2f2; color:#dc2626; border-color:#fecaca; }}
      .sev-medium {{ background:#fffbeb; color:#d97706; border-color:#fde68a; }}
      .sev-low {{ background:#eff6ff; color:#0369a1; border-color:#bfdbfe; }}
      .col-main .v-title {{
        margin: 0 0 2px;
        font-weight: 600;
      }}
      .v-id {{
        margin: 0;
        font-size: 12px;
        color: #6b7280;
      }}
      .v-id span {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        color: #111827;
      }}
      .v-meta {{
        margin-top: 6px;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }}
      .chip {{
        border-radius: 999px;
        border: 1px solid #e5e7eb;
        background: #f9fafb;
        padding: 2px 8px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
      }}
      .chip-label {{
        font-size: 11px;
        color: #6b7280;
      }}
      .chip-value {{
        font-size: 11px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      }}
      .v-link {{
        margin-top: 6px;
        font-size: 11px;
      }}
      .v-link a {{
        color: #2563eb;
        text-decoration: none;
      }}
      .v-link a:hover {{
        text-decoration: underline;
      }}
      .no-data {{
        text-align: center;
        font-size: 13px;
        color: #6b7280;
        padding: 16px 0;
      }}
      @media (max-width: 900px) {{
        .page {{ grid-template-columns: minmax(0,1fr); }}
      }}
      @media (max-width: 640px) {{
        .header {{ padding: 18px; }}
      }}
    </style>
  </head>
  <body>
    <main class="page">
      <section class="card card-main">
        <header>
          <p class="eyebrow">Snyk</p>
          <h1>Rapport Snyk</h1>
          <p class="subtitle">Analyse des vulnérabilités dans les dépendances du projet.</p>
          <div class="summary" style="margin-top:10px;font-size:12px;color:#4b5563;">
            <span style="border-radius:999px;border:1px solid #e5e7eb;background:#f9fafb;padding:2px 8px;">
              Total : <strong>{len(vulns)}</strong>
            </span>
          </div>
          <div class="summary-grid">
            <div class="summary-card summary-critical">
              <div class="summary-label">Critiques</div>
              <div class="summary-value crit">{counts["critical"]}</div>
            </div>
            <div class="summary-card summary-high">
              <div class="summary-label">Hautes</div>
              <div class="summary-value high">{counts["high"]}</div>
            </div>
            <div class="summary-card summary-medium">
              <div class="summary-label">Moyennes</div>
              <div class="summary-value med">{counts["medium"]}</div>
            </div>
            <div class="summary-card summary-low">
              <div class="summary-label">Basses</div>
              <div class="summary-value low">{counts["low"]}</div>
            </div>
          </div>
        </header>
        <table>
          <thead>
            <tr>
              <th style="width:110px;">Gravité</th>
              <th>Vulnérabilité</th>
            </tr>
          </thead>
          <tbody>
{body_rows}
          </tbody>
        </table>
      </section>
    </main>
  </body>
</html>"""
    return html


# --- Nouvelle version "dashboard" avec CSS externe (pour Jenkins / CSP) ---

SNYK_DASHBOARD_CSS = """\
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  padding: 24px 16px 32px;
  background: #f3f4f6;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #111827;
}
.page {
  max-width: 1120px;
  margin: 0 auto;
}
.header {
  border-radius: 24px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  padding: 22px 24px 18px;
  box-shadow: 0 22px 50px rgba(148,163,184,0.25);
}
.eyebrow {
  margin: 0 0 4px;
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #4f46e5;
}
h1 {
  margin: 0;
  font-size: 22px;
  letter-spacing: 0.03em;
}
.subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #6b7280;
}
.summary-row {
  margin-top: 10px;
  font-size: 12px;
  color: #4b5563;
}
.summary-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  padding: 2px 8px;
}
.summary-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0,1fr));
  gap: 10px;
}
.summary-card {
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  padding: 10px 12px;
}
.summary-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: #9ca3af;
  margin-bottom: 2px;
}
.summary-value {
  font-size: 18px;
  font-weight: 700;
}
.crit { color: #b91c1c; }
.high { color: #dc2626; }
.med { color: #d97706; }
.low { color: #0369a1; }

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 18px;
}
thead th {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #9ca3af;
  padding: 0 8px 4px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}
tbody tr + tr td {
  border-top: 1px solid #f3f4f6;
}
td {
  padding: 8px;
  vertical-align: top;
  font-size: 13px;
}
.sev {
  width: 96px;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  border-radius: 999px;
  padding: 4px 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}
.sev-critical { background:#fef2f2; color:#b91c1c; border-color:#fecaca; }
.sev-high { background:#fef2f2; color:#dc2626; border-color:#fecaca; }
.sev-medium { background:#fffbeb; color:#d97706; border-color:#fde68a; }
.sev-low { background:#eff6ff; color:#0369a1; border-color:#bfdbfe; }
.sev-unknown { background:#e5e7eb; color:#374151; }
.v-title {
  margin: 0 0 2px;
  font-size: 14px;
  font-weight: 600;
}
.v-id {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
}
.v-id span {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  color: #111827;
}
.v-meta {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 11px;
}
.chip {
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  padding: 2px 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.chip-label {
  color: #6b7280;
}
.chip-value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
.v-link {
  margin-top: 6px;
  font-size: 11px;
}
.v-link a {
  color: #2563eb;
  text-decoration: none;
}
.v-link a:hover {
  text-decoration: underline;
}
.no-data {
  text-align: center;
  font-size: 13px;
  color: #6b7280;
  padding: 16px 0;
}
@media (max-width: 768px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
"""


def render_html_dashboard(data: dict) -> str:
    """HTML principal qui référence la feuille CSS externe."""
    vulns = data.get("vulnerabilities", [])

    # Compter par sévérité
    severities = ["critical", "high", "medium", "low"]
    counts = {s: 0 for s in severities}
    for v in vulns:
        sev = (v.get("severity") or "").lower()
        if sev in counts:
            counts[sev] += 1

    # Lignes du tableau
    rows = []
    for v in vulns:
        sev = (v.get("severity") or "").lower()
        pkg = v.get("packageName") or v.get("moduleName") or "n/a"
        version = v.get("version") or "?"
        title = v.get("title") or v.get("name") or ""
        id_ = v.get("id") or ""
        from_chain = " → ".join(v.get("from", [])) if v.get("from") else ""
        url = v.get("url") or ""

        rows.append(
            f"<tr>"
            f"<td class='sev sev-{escape(sev or 'unknown')}'>{escape((sev or 'UNKNOWN').upper())}</td>"
            f"<td class='col-main'>"
            f"<div class='v-title'>{escape(title or id_)}</div>"
            f"<p class='v-id'>ID : <span>{escape(id_ or 'N/A')}</span></p>"
            f"<div class='v-meta'>"
            f"<span class='chip'><span class='chip-label'>Package</span><span class='chip-value'>{escape(pkg)}@{escape(str(version))}</span></span>"
            f"{f'<span class=\"chip\"><span class=\"chip-label\">Chemin</span><span class=\"chip-value\">{escape(from_chain)}</span></span>' if from_chain else ''}"
            f"</div>"
            f"</td></tr>"
        )

    body_rows = "".join(rows) if rows else (
        "<tr><td colspan='2' class='no-data'>Aucune vulnérabilité détectée.</td></tr>"
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>Rapport Snyk</title>
    <link rel="stylesheet" href="snyk-report.css" />
  </head>
  <body>
    <main class="page">
      <section class="header">
        <p class="eyebrow">Snyk</p>
        <h1>Rapport Snyk</h1>
        <p class="subtitle">Analyse des vulnérabilités dans les dépendances du projet.</p>
        <div class="summary-row">
          <span class="summary-pill">Total : <strong>{len(vulns)}</strong></span>
        </div>
        <div class="summary-grid">
          <div class="summary-card">
            <div class="summary-label">Critiques</div>
            <div class="summary-value crit">{counts["critical"]}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Hautes</div>
            <div class="summary-value high">{counts["high"]}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Moyennes</div>
            <div class="summary-value med">{counts["medium"]}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Basses</div>
            <div class="summary-value low">{counts["low"]}</div>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th style="width:110px;">Gravité</th>
              <th>Vulnérabilité</th>
            </tr>
          </thead>
          <tbody>
{body_rows}
          </tbody>
        </table>
      </section>
    </main>
  </body>
</html>"""
def main():
    json_path = Path("reports/snyk/snyk-report.json")
    data = load_snyk_json(json_path)
    if not data:
        return

    # Écrit la feuille de style externe pour Jenkins / navigateur
    css_path = Path("reports/snyk/snyk-report.css")
    css_path.write_text(SNYK_DASHBOARD_CSS, encoding="utf-8")

    # Utilise la version dashboard qui référence la CSS externe
    html = render_html_dashboard(data)
    out = Path("reports/snyk/snyk-report.html")
    out.write_text(html, encoding="utf-8")
    print(f"✅ Rapport HTML Snyk généré : {out}")


if __name__ == "__main__":
    main()


