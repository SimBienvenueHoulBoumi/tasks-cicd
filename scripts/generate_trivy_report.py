import json
from html import escape
from pathlib import Path


def render_html(vulns):
    """
    Génère un rapport HTML Trivy avec du CSS pur (sans Tailwind) et CSS EXTERNE.
    """
    # Compter par sévérité
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    counts = {s: 0 for s in severities}
    for v in vulns:
        sev = (v.get("Severity") or "").upper()
        if sev in counts:
            counts[sev] += 1

    # Construire les lignes
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
            metrics = next(iter(v["CVSS"].values()), {})
            cvss = str(metrics.get("V3Score") or metrics.get("V2Score") or "")
        url = v.get("PrimaryURL") or ""

        rows.append(
            f"<tr>"
            f"<td class='sev sev-{escape(sev.lower())}'>{escape(sev or 'UNKNOWN')}</td>"
            f"<td class='col-main'>"
            f"<div class='v-title'>{escape(title)}</div>"
            f"<p class='v-id'>ID : <span>{escape(vuln_id)}</span></p>"
            f"<div class='v-meta'>"
            f"<span class='chip'><span class='chip-label'>Package</span><span class='chip-value'>{escape(pkg)}@{escape(str(installed))}</span></span>"
            f"<span class='chip'><span class='chip-label'>Fix</span><span class='chip-value'>{escape(str(fixed))}</span></span>"
        )
        if cvss:
            rows[-1] += (
                f"<span class='chip'><span class='chip-label'>CVSS</span><span class='chip-value'>{escape(cvss)}</span></span>"
            )
        rows[-1] += "</div>"
        if url:
            rows[-1] += (
                f"<p class='v-link'><a href='{escape(url)}' target='_blank' rel='noopener noreferrer'>Voir le détail ↗</a></p>"
            )
        rows[-1] += "</td></tr>"

    body_rows = "".join(rows) if rows else (
        "<tr><td colspan='2' class='no-data'>Aucune vulnérabilité détectée.</td></tr>"
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>Rapport Trivy</title>
    <link rel="stylesheet" href="trivy-report.css" />
  </head>
  <body>
    <main class="page">
      <section class="header">
        <p class="eyebrow">Trivy</p>
        <h1>Rapport Trivy</h1>
        <p class="subtitle">Vulnérabilités détectées sur l'image container.</p>
        <div class="summary-grid">
          <div class="summary-card summary-critical">
            <div class="summary-label">Critiques</div>
            <div class="summary-value crit">{counts["CRITICAL"]}</div>
          </div>
          <div class="summary-card summary-high">
            <div class="summary-label">Hautes</div>
            <div class="summary-value high">{counts["HIGH"]}</div>
          </div>
          <div class="summary-card summary-medium">
            <div class="summary-label">Moyennes</div>
            <div class="summary-value med">{counts["MEDIUM"]}</div>
          </div>
          <div class="summary-card summary-low">
            <div class="summary-label">Basses</div>
            <div class="summary-value low">{counts["LOW"]}</div>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th style="width:110px;">Gravité</th>
              <th>Détail</th>
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


TRIVY_DASHBOARD_CSS = """\
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  padding: 24px 16px 32px;
  background: #f9fafb;
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
  color: #0369a1;
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
  border: 1px solid #e5e7eb;
  background: #f9fafb;
}
.sev-critical { background:#fef2f2; color:#b91c1c; border-color:#fecaca; }
.sev-high { background:#fef2f2; color:#dc2626; border-color:#fecaca; }
.sev-medium { background:#fffbeb; color:#d97706; border-color:#fde68a; }
.sev-low { background:#eff6ff; color:#0369a1; border-color:#bfdbfe; }
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

    # Écrit la feuille de style externe pour Jenkins / navigateur
    css_path = Path("reports/trivy/trivy-report.css")
    css_path.write_text(TRIVY_DASHBOARD_CSS, encoding="utf-8")

    html = render_html(all_vulns)
    output_path = Path("reports/trivy/trivy-report.html")
    output_path.write_text(html, encoding="utf-8")
    print(f"✅ Rapport HTML généré : {output_path}")


if __name__ == "__main__":
    main()
