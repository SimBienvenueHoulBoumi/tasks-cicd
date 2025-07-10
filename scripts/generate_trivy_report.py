import json
from pathlib import Path

def render_html(vulns):
    html = ['<html><head><title>Trivy Report</title></head><body><h1>Vulnérabilités Critiques / Hautes</h1><ul>']
    for v in vulns:
        html.append(f"<li><b>{v['VulnerabilityID']}</b> - {v['PkgName']} - {v['Severity']}<br>{v.get('Title', 'Pas de description')}</li>")
    html.append('</ul></body></html>')
    return '\n'.join(html)

def main():
    json_path = Path("reports/trivy/trivy-report.json")
    if not json_path.exists():
        print("❌ Fichier Trivy introuvable.")
        return

    try:
        with json_path.open() as f:
            # On lit toutes les lignes, et on prend uniquement la dernière ligne JSON valide
            lines = f.read().splitlines()
            for line in reversed(lines):
                try:
                    data = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
            else:
                print("❌ Aucun JSON valide trouvé dans le fichier.")
                return

    except Exception as e:
        print(f"❌ Erreur de lecture du fichier: {e}")
        return

    all_vulns = []
    for target in data.get("Results", []):
        for vuln in target.get("Vulnerabilities", []):
            if vuln.get("Severity") in ["CRITICAL", "HIGH"]:
                all_vulns.append(vuln)

    if not all_vulns:
        print("✅ Aucune vulnérabilité critique ou haute détectée.")
        return

    html = render_html(all_vulns)
    output_path = Path("reports/trivy/trivy-report.html")
    output_path.write_text(html)
    print(f"✅ Rapport HTML généré : {output_path}")

if __name__ == "__main__":
    main()
