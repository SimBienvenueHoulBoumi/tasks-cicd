import json
from pathlib import Path


def render_html(vulns):
    html = ['<html><head><title>Trivy Report</title></head><body><h1>Vulnérabilités Critiques / Hautes</h1><ul>']
    for v in vulns:
        html.append(
            f"<li><b>{v.get('VulnerabilityID', 'N/A')}</b> - "
            f"{v.get('PkgName', 'N/A')} - {v.get('Severity', 'N/A')}<br>"
            f"{v.get('Title', 'Pas de description')}</li>"
        )
    html.append('</ul></body></html>')
    return '\n'.join(html)


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
            if vuln.get("Severity") in ["CRITICAL", "HIGH"]:
                all_vulns.append(vuln)

    if not all_vulns:
        print("✅ Aucune vulnérabilité critique ou haute détectée.")
        return

    html = render_html(all_vulns)
    output_path = Path("reports/trivy/trivy-report.html")
    output_path.write_text(html, encoding="utf-8")
    print(f"✅ Rapport HTML généré : {output_path}")


if __name__ == "__main__":
    main()

