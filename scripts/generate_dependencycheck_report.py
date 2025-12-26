import json
from html import escape
from pathlib import Path


def load_dc_json(path: Path):
    """
    Charge le JSON OWASP Dependency-Check de façon robuste.
    """
    if not path.exists():
        print(f"❌ Fichier Dependency-Check introuvable: {path}")
        return None

    content = path.read_text(errors="ignore")
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"❌ JSON Dependency-Check invalide: {e}")
        return None


DC_DASHBOARD_CSS = """\
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
  color: #0f766e;
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
  width: 80px;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  border-radius: 999px;
  padding: 4px 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.sev-CRITICAL { background:#fef2f2; color:#b91c1c; }
.sev-HIGH     { background:#fef2f2; color:#dc2626; }
.sev-MEDIUM   { background:#fffbeb; color:#d97706; }
.sev-LOW      { background:#eff6ff; color:#0369a1; }
.file-name {
  margin: 0 0 2px;
  font-weight: 600;
}
.vuln-title {
  margin: 0 0 2px;
  font-size: 13px;
  font-weight: 600;
}
.vuln-id {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
}
.vuln-id span {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  color: #111827;
}
.chips {
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


def render_html(data: dict) -> str:
    """
    Génère un rapport HTML dashboard à partir du JSON Dependency-Check.
    """
    deps = data.get("dependencies", []) if data else []

    vulns = []
    for dep in deps:
        file_name = dep.get("fileName") or dep.get("name") or ""
        for v in dep.get("vulnerabilities", []) or []:
            entry = {
                "severity": v.get("severity", "UNKNOWN"),
                "id": v.get("name") or v.get("id") or "",
                "title": v.get("description") or v.get("description", "")[:120],
                "fileName": file_name,
                "cwe": (v.get("cwe") or "")[:40],
                "cvss": v.get("cvssScore") or v.get("cvssv3") or "",
            }
            vulns.append(entry)

    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    counts = {s: 0 for s in severities}
    for v in vulns:
        sev = (v.get("severity") or "").upper()
        if sev in counts:
            counts[sev] += 1

    rows = []
    for v in vulns:
        sev = (v.get("severity") or "UNKNOWN").upper()
        rows.append(
            f"<tr>"
            f"<td><span class='sev sev-{escape(sev)}'>{escape(sev)}</span></td>"
            f"<td>"
            f"<div class='file-name'>{escape(v.get('fileName') or '')}</div>"
            f"<div class='vuln-title'>{escape(v.get('title') or '')}</div>"
            f"<p class='vuln-id'>ID : <span>{escape(v.get('id') or '')}</span></p>"
            f"<div class='chips'>"
            f"<span class='chip'><span class='chip-label'>CWE</span><span class='chip-value'>{escape(v.get('cwe') or '')}</span></span>"
            f"<span class='chip'><span class='chip-label'>CVSS</span><span class='chip-value'>{escape(str(v.get('cvss') or ''))}</span></span>"
            f"</div>"
            f"</td>"
            f"</tr>"
        )

    body_rows = "".join(rows) if rows else (
        "<tr><td colspan='2' class='no-data'>Aucune vulnérabilité détectée par OWASP Dependency-Check.</td></tr>"
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>Rapport OWASP Dependency-Check</title>
    <link rel="stylesheet" href="dependency-check.css" />
  </head>
  <body>
    <main class="page">
      <section class="header">
        <p class="eyebrow">OWASP</p>
        <h1>Rapport Dependency-Check</h1>
        <p class="subtitle">Analyse des dépendances du projet.</p>
        <div class="summary-grid">
          <div class="summary-card">
            <div class="summary-label">Critiques</div>
            <div class="summary-value crit">{counts["CRITICAL"]}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Hautes</div>
            <div class="summary-value high">{counts["HIGH"]}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Moyennes</div>
            <div class="summary-value med">{counts["MEDIUM"]}</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Basses</div>
            <div class="summary-value low">{counts["LOW"]}</div>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th style="width:110px;">Gravité</th>
              <th>Dépendance / Vulnérabilité</th>
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
    json_path = Path("target/dependency-check-report.json")
    data = load_dc_json(json_path)

    out_dir = Path("reports/dependency-check")
    out_dir.mkdir(parents=True, exist_ok=True)

    # CSS externe
    (out_dir / "dependency-check.css").write_text(DC_DASHBOARD_CSS, encoding="utf-8")

    html = render_html(data)
    out_html = out_dir / "dependency-check.html"
    out_html.write_text(html, encoding="utf-8")

    print(f"✅ Rapport HTML OWASP Dependency-Check généré : {out_html}")


if __name__ == "__main__":
    main()


