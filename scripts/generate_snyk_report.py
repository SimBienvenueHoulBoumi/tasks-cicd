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
    vulns = data.get("vulnerabilities", [])

    if not vulns:
        return """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Rapport Snyk</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           background:#0f172a; color:#e5e7eb; margin:0; padding:2rem; }
    .card { background:#020617; border-radius:0.75rem; padding:2rem; max-width:60rem; margin:0 auto;
            box-shadow:0 25px 50px -12px rgba(15,23,42,0.8); }
    .title { font-size:1.75rem; font-weight:700; color:#e5e7eb; margin-bottom:0.5rem; }
    .subtitle { color:#9ca3af; margin-bottom:1.5rem; }
    .badge-ok { display:inline-flex; align-items:center; gap:0.5rem; background:#022c22; color:#6ee7b7;
                border:1px solid #10b981; border-radius:9999px; padding:0.35rem 0.9rem;
                font-size:0.9rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; }
  </style>
</head>
<body>
  <div class="card">
    <div class="title">Rapport Snyk</div>
    <div class="subtitle">Analyse de dépendances</div>
    <div class="badge-ok">✔ Aucun problème trouvé par Snyk</div>
  </div>
</body>
</html>"""

    # Compter par sévérité
    severities = ["critical", "high", "medium", "low"]
    counts = {s: 0 for s in severities}
    for v in vulns:
        sev = (v.get("severity") or "").lower()
        if sev in counts:
            counts[sev] += 1

    def sev_color(sev: str) -> str:
        return {
            "critical": "#b91c1c",
            "high": "#dc2626",
            "medium": "#ea580c",
            "low": "#ca8a04",
        }.get(sev.lower(), "#6b7280")

    def sev_bg(sev: str) -> str:
        return {
            "critical": "rgba(127,29,29,0.35)",
            "high": "rgba(127,29,29,0.25)",
            "medium": "rgba(146,64,14,0.22)",
            "low": "rgba(133,77,14,0.18)",
        }.get(sev.lower(), "rgba(31,41,55,0.4)")

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
        <tr>
          <td class="col-sev">
            <span class="badge-sev badge-{sev}">
              {escape(sev.upper())}
            </span>
          </td>
          <td class="col-main">
            <div class="vuln-title">{escape(title or id_)}</div>
            <div class="vuln-meta">
              <span class="pill">Package: <b>{escape(pkg)}</b>@{escape(str(version))}</span>
              {"<span class='pill'>Chemin: " + escape(from_chain) + "</span>" if from_chain else ""}
            </div>
            {"<div class='vuln-link'><a href='" + escape(url) + "' target='_blank' rel='noopener noreferrer'>Voir le détail sur Snyk ↗</a></div>" if url else ""}
          </td>
        </tr>
        """)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Rapport Snyk</title>
  <style>
    /* Style utilitaires inspirés de Tailwind (simplifiés) */
    :root {{
      --bg-slate-950:#020617;
      --bg-slate-900:#0f172a;
      --bg-slate-800:#1e293b;
      --border-slate-700:#334155;
      --text-slate-50:#f9fafb;
      --text-slate-300:#d1d5db;
      --text-slate-400:#9ca3af;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      background: radial-gradient(circle at top left, #1e293b 0, #020617 55%);
      color: var(--text-slate-50);
      margin:0;
      padding:2.5rem 1.25rem;
    }}
    .container {{
      max-width: 1120px;
      margin:0 auto;
    }}
    .card {{
      background: linear-gradient(145deg, rgba(15,23,42,0.96), rgba(15,23,42,0.98));
      border-radius:1.25rem;
      border:1px solid rgba(51,65,85,0.9);
      box-shadow:0 25px 60px -20px rgba(15,23,42,0.9);
      padding:2rem 2.5rem;
    }}
    .title {{
      font-size:1.9rem;
      font-weight:700;
      letter-spacing:0.03em;
      margin-bottom:0.35rem;
    }}
    .subtitle {{
      color:var(--text-slate-400);
      font-size:0.95rem;
      margin-bottom:1.75rem;
    }}
    .grid-summary {{
      display:grid;
      grid-template-columns:repeat(4,minmax(0,1fr));
      gap:0.75rem;
      margin-bottom:1.75rem;
    }}
    .summary-card {{
      padding:0.75rem 0.9rem;
      border-radius:0.9rem;
      background:rgba(15,23,42,0.85);
      border:1px solid rgba(55,65,81,0.75);
    }}
    .summary-label {{
      font-size:0.75rem;
      text-transform:uppercase;
      letter-spacing:0.08em;
      color:var(--text-slate-400);
      margin-bottom:0.25rem;
    }}
    .summary-value {{
      font-size:1.3rem;
      font-weight:700;
    }}
    .summary-critical .summary-value {{ color:#f97373; }}
    .summary-high .summary-value {{ color:#fb7185; }}
    .summary-medium .summary-value {{ color:#fb923c; }}
    .summary-low .summary-value {{ color:#eab308; }}

    table {{
      width:100%;
      border-collapse:separate;
      border-spacing:0 0.5rem;
    }}
    thead th {{
      text-align:left;
      font-size:0.75rem;
      text-transform:uppercase;
      letter-spacing:0.08em;
      color:var(--text-slate-400);
      padding:0 0.5rem 0.35rem;
    }}
    tbody tr {{
      background:linear-gradient(135deg, rgba(15,23,42,0.98), rgba(15,23,42,0.94));
      border-radius:0.9rem;
      overflow:hidden;
      border:1px solid rgba(51,65,85,0.9);
    }}
    tbody tr td {{
      padding:0.75rem 0.9rem;
      vertical-align:top;
    }}
    .col-sev {{ width:110px; }}
    .badge-sev {{
      display:inline-flex;
      align-items:center;
      justify-content:center;
      min-width:90px;
      padding:0.35rem 0.75rem;
      border-radius:9999px;
      font-size:0.75rem;
      font-weight:700;
      text-transform:uppercase;
      letter-spacing:0.08em;
      border:1px solid rgba(148,163,184,0.9);
    }}
    .badge-critical {{ background:{sev_bg("critical")}; color:{sev_color("critical")}; border-color:{sev_color("critical")}; }}
    .badge-high {{ background:{sev_bg("high")}; color:{sev_color("high")}; border-color:{sev_color("high")}; }}
    .badge-medium {{ background:{sev_bg("medium")}; color:{sev_color("medium")}; border-color:{sev_color("medium")}; }}
    .badge-low {{ background:{sev_bg("low")}; color:{sev_color("low")}; border-color:{sev_color("low")}; }}

    .vuln-title {{
      font-size:0.95rem;
      font-weight:600;
      margin-bottom:0.35rem;
    }}
    .vuln-meta {{
      display:flex;
      flex-wrap:wrap;
      gap:0.35rem;
      margin-bottom:0.35rem;
      font-size:0.8rem;
      color:var(--text-slate-300);
    }}
    .pill {{
      border-radius:9999px;
      padding:0.15rem 0.7rem;
      background:rgba(15,23,42,0.9);
      border:1px solid rgba(55,65,81,0.9);
    }}
    .vuln-link a {{
      font-size:0.8rem;
      color:#38bdf8;
      text-decoration:none;
    }}
    .vuln-link a:hover {{
      text-decoration:underline;
    }}

    @media (max-width: 768px) {{
      .card {{ padding:1.5rem 1.25rem; }}
      .grid-summary {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
      .col-sev {{ width:80px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <div class="title">Rapport Snyk</div>
      <div class="subtitle">Analyse des vulnérabilités dans les dépendances du projet</div>

      <div class="grid-summary">
        <div class="summary-card summary-critical">
          <div class="summary-label">Critiques</div>
          <div class="summary-value">{counts["critical"]}</div>
        </div>
        <div class="summary-card summary-high">
          <div class="summary-label">Hautes</div>
          <div class="summary-value">{counts["high"]}</div>
        </div>
        <div class="summary-card summary-medium">
          <div class="summary-label">Moyennes</div>
          <div class="summary-value">{counts["medium"]}</div>
        </div>
        <div class="summary-card summary-low">
          <div class="summary-label">Basses</div>
          <div class="summary-value">{counts["low"]}</div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Gravité</th>
            <th>Vulnérabilité</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>"""

    return html


def main():
    json_path = Path("reports/snyk/snyk-report.json")
    data = load_snyk_json(json_path)
    if not data:
        return

    html = render_html(data)
    out = Path("reports/snyk/snyk-report.html")
    out.write_text(html, encoding="utf-8")
    print(f"✅ Rapport HTML Snyk généré : {out}")


if __name__ == "__main__":
    main()


