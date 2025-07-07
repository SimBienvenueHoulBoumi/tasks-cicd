import json
from pathlib import Path

def render_html(vulns):
    html = ['<html><head><title>Trivy Report</title></head><body><h1>Vulnérabilités Critiques / Hautes</h1><ul>']
    for v in vulns:
        html.append(f"<li><b>{v['VulnerabilityID']}</b> - {v['PkgName']} - {v['Severity']}<br>{v['Title']}</li>")
    html.append('</ul></body></html>')
    return '\n'.join(html)

def main():
    report_file = Path("reports/trivy/trivy-report.json")
    if not report_file.exists():
        print("Fichier Trivy introuvable.")
        return

    with report_file.open() as f:
        data = json.load(f)

    all_vulns = []
    for target in data.get("Results", []):
        for vuln in target.get("Vulnerabilities", []):
            if vuln.get("Severity") in ["CRITICAL", "HIGH"]:
                all_vulns.append(vuln)

    html = render_html(all_vulns)
    Path("reports/trivy/trivy-report.html").write_text(html)
    print("✅ Rapport HTML généré dans reports/trivy/trivy-report.html")

if __name__ == "__main__":
    main()
