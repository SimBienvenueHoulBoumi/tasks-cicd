import json
from html import escape
from pathlib import Path


def render_html(vulns):
    """
    Génère un rapport HTML moderne et sombre pour les vulnérabilités Trivy.
    """
    # Compter par sévérité
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    counts = {s: 0 for s in severities}
    for v in vulns:
        sev = (v.get("Severity") or "").upper()
        if sev in counts:
            counts[sev] += 1

    def sev_color(sev: str) -> str:
        return {
            "CRITICAL": "#b91c1c",
            "HIGH": "#dc2626",
            "MEDIUM": "#ea580c",
            "LOW": "#ca8a04",
        }.get(sev.upper(), "#6b7280")

    def sev_bg(sev: str) -> str:
        return {
            "CRITICAL": "rgba(127,29,29,0.35)",
            "HIGH": "rgba(127,29,29,0.25)",
            "MEDIUM": "rgba(146,64,14,0.22)",
            "LOW": "rgba(133,77,14,0.18)",
        }.get(sev.upper(), "rgba(31,41,55,0.4)")

    # Cas sans vulnérabilités : on rend quand même une page propre
    if not vulns:
        return """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Rapport Trivy</title>
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
    <div class="title">Rapport Trivy</div>
    <div class="subtitle">Scan des images container (CRITICAL / HIGH)</div>
    <div class="badge-ok">✔ Aucune vulnérabilité critique ou haute détectée</div>
  </div>
</body>
</html>"""

    rows = []
    for v in vulns:
        sev = (v.get("Severity") or "").upper()
        vuln_id = v.get("VulnerabilityID", "N/A")
        title = v.get("Title", "") or vuln_id
        pkg = v.get("PkgName", "N/A")
        installed = v.get("InstalledVersion", "?")
        fixed = v.get("FixedVersion", "N/A")
        cvss = ""
        if v.get("CVSS"):
            # Récupère une des valeurs CVSS si dispo
            metrics = next(iter(v["CVSS"].values()), {})
            cvss = str(metrics.get("V3Score") or metrics.get("V2Score") or "")
        url = v.get("PrimaryURL") or ""

        rows.append(f"""
        <tr>
          <td class="col-sev">
            <span class="badge-sev badge-{escape(sev.lower())}">
              {escape(sev)}
            </span>
          </td>
          <td class="col-main">
            <div class="vuln-title">{escape(title)}</div>
            <div class="vuln-meta">
              <span class="pill">ID: <b>{escape(vuln_id)}</b></span>
              <span class="pill">Package: <b>{escape(pkg)}</b>@{escape(str(installed))}</span>
              <span class="pill">Fix: {escape(str(fixed))}</span>
              {f"<span class='pill'>CVSS: {escape(cvss)}</span>" if cvss else ""}
            </div>
            {f"<div class='vuln-link'><a href='{escape(url)}' target='_blank' rel='noopener noreferrer'>Voir le détail ↗</a></div>" if url else ""}
          </td>
        </tr>
        """)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Rapport Trivy</title>
  <style>
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
    .badge-critical {{ background:{sev_bg("CRITICAL")}; color:{sev_color("CRITICAL")}; border-color:{sev_color("CRITICAL")}; }}
    .badge-high {{ background:{sev_bg("HIGH")}; color:{sev_color("HIGH")}; border-color:{sev_color("HIGH")}; }}
    .badge-medium {{ background:{sev_bg("MEDIUM")}; color:{sev_color("MEDIUM")}; border-color:{sev_color("MEDIUM")}; }}
    .badge-low {{ background:{sev_bg("LOW")}; color:{sev_color("LOW")}; border-color:{sev_color("LOW")}; }}

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
      <div class="title">Rapport Trivy</div>
      <div class="subtitle">Vulnérabilités sur l'image container (CRITICAL / HIGH)</div>

      <div class="grid-summary">
        <div class="summary-card summary-critical">
          <div class="summary-label">Critiques</div>
          <div class="summary-value">{counts["CRITICAL"]}</div>
        </div>
        <div class="summary-card summary-high">
          <div class="summary-label">Hautes</div>
          <div class="summary-value">{counts["HIGH"]}</div>
        </div>
        <div class="summary-card summary-medium">
          <div class="summary-label">Moyennes</div>
          <div class="summary-value">{counts["MEDIUM"]}</div>
        </div>
        <div class="summary-card summary-low">
          <div class="summary-label">Basses</div>
          <div class="summary-value">{counts["LOW"]}</div>
        </div>
      </div>

      <table>
        <thead>
          <tr>
            <th>Gravité</th>
            <th>Détail</th>
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
    json_path = Path("reports/trivy/trivy-report.json")
    if not json_path.exists():
        print("❌ Fichier Trivy introuvable.")
        return

    try:
        # Avec Trivy CLI `--format json`, le fichier contient un unique JSON valide
        data = json.loads(json_path.read_text())
        if isinstance(data, str):
            print("❌ Le fichier Trivy contient une chaîne et non un objet JSON. Contenu inattendu.")
            return
    except json.JSONDecodeError as e:
        print(f"❌ JSON Trivy invalide: {e}")
        return
    except Exception as e:
        print(f"❌ Erreur de lecture du fichier: {e}")
        return

    all_vulns = []
    for target in data.get("Results", []):
        for vuln in target.get("Vulnerabilities", []):
            if vuln.get("Severity") in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                all_vulns.append(vuln)

    html = render_html(all_vulns)
    output_path = Path("reports/trivy/trivy-report.html")
    output_path.write_text(html, encoding="utf-8")
    print(f"✅ Rapport HTML généré : {output_path}")


if __name__ == "__main__":
    main()
