import json
from html import escape
from pathlib import Path


def render_html(vulns):
    """
    Génère un rapport HTML Trivy avec Tailwind CSS (via CDN).
    """
    # Compter par sévérité
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    counts = {s: 0 for s in severities}
    for v in vulns:
        sev = (v.get("Severity") or "").upper()
        if sev in counts:
            counts[sev] += 1

    def sev_badge_color(sev: str) -> str:
        return {
            "CRITICAL": "bg-rose-500/10 text-rose-300 border-rose-400/70",
            "HIGH": "bg-red-500/10 text-red-300 border-red-400/70",
            "MEDIUM": "bg-amber-500/10 text-amber-300 border-amber-400/70",
            "LOW": "bg-sky-500/10 text-sky-300 border-sky-400/70",
        }.get(sev.upper(), "bg-slate-700/40 text-slate-200 border-slate-500/60")

    def sev_summary_color(sev: str) -> str:
        return {
            "CRITICAL": "text-rose-400",
            "HIGH": "text-red-400",
            "MEDIUM": "text-amber-400",
            "LOW": "text-sky-300",
        }.get(sev.upper(), "text-slate-300")

    # Cas sans vulnérabilités
    if not vulns:
        return """<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>Rapport Trivy</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="min-h-screen bg-slate-950 text-slate-50 flex items-center justify-center p-6">
    <main class="max-w-2xl w-full bg-slate-900/80 border border-slate-800 rounded-2xl shadow-2xl shadow-slate-900/80 p-8">
      <header class="mb-6">
        <p class="text-xs font-semibold tracking-[0.25em] text-sky-400/80 uppercase">Trivy</p>
        <h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-50">Rapport Trivy</h1>
        <p class="mt-1 text-sm text-slate-400">Analyse de l’image container (CRITICAL / HIGH).</p>
      </header>

      <section class="mt-4 flex items-center gap-3 rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-3">
        <div class="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-300">
          <span class="text-lg">✔</span>
        </div>
        <div>
          <p class="text-sm font-semibold text-emerald-300">Aucune vulnérabilité critique ou haute détectée</p>
          <p class="text-xs text-emerald-200/80">
            Trivy n’a remonté aucun problème sur ce scan. Pensez à relancer l’analyse après chaque mise à jour d’image.
          </p>
        </div>
      </section>
    </main>
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
            metrics = next(iter(v["CVSS"].values()), {})
            cvss = str(metrics.get("V3Score") or metrics.get("V2Score") or "")
        url = v.get("PrimaryURL") or ""

        rows.append(f"""
        <article class="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3 sm:px-5 sm:py-4 flex flex-col sm:flex-row gap-3 sm:gap-4">
          <div class="sm:w-32 flex-shrink-0">
            <span class="inline-flex items-center justify-center rounded-full border px-3 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.18em] {sev_badge_color(sev)}>
              {escape(sev or "UNKNOWN")}
            </span>
          </div>
          <div class="flex-1 space-y-1">
            <h3 class="text-sm font-semibold text-slate-50">
              {escape(title)}
            </h3>
            <p class="text-xs text-slate-400">
              ID&nbsp;: <span class="font-mono text-slate-200">{escape(vuln_id)}</span>
            </p>
            <div class="mt-1 flex flex-wrap gap-2 text-[0.7rem] text-slate-300">
              <span class="inline-flex items-center rounded-full border border-slate-700/80 bg-slate-900/80 px-2.5 py-0.5">
                <span class="mr-1 text-slate-400">Package</span>
                <span class="font-mono">{escape(pkg)}@{escape(str(installed))}</span>
              </span>
              <span class="inline-flex items-center rounded-full border border-slate-700/80 bg-slate-900/80 px-2.5 py-0.5">
                <span class="mr-1 text-slate-400">Fix</span>
                <span class="font-mono">{escape(str(fixed))}</span>
              </span>
              {f"<span class='inline-flex items-center rounded-full border border-slate-700/80 bg-slate-900/80 px-2.5 py-0.5'><span class='mr-1 text-slate-400'>CVSS</span><span class='font-mono'>{escape(cvss)}</span></span>" if cvss else ""}
            </div>
            {f"<p class='mt-1 text-[0.7rem]'><a href='{escape(url)}' target='_blank' rel='noopener noreferrer' class='text-sky-300 hover:text-sky-200 underline underline-offset-4 decoration-sky-500/70'>Voir le détail ↗</a></p>" if url else ""}
          </div>
        </article>
        """)

    html = f"""<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <title>Rapport Trivy</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="min-h-screen bg-slate-950 text-slate-50 p-4 sm:p-6">
    <main class="mx-auto max-w-5xl space-y-5">
      <header class="rounded-2xl border border-slate-800 bg-slate-900/80 px-6 py-5 shadow-2xl shadow-slate-950/70">
        <p class="text-xs font-semibold tracking-[0.25em] text-sky-400/80 uppercase">Trivy</p>
        <div class="mt-1 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 class="text-2xl font-bold tracking-tight text-slate-50">Rapport Trivy</h1>
            <p class="text-xs sm:text-sm text-slate-400">
              Vulnérabilités détectées sur l'image container (CRITICAL / HIGH / MEDIUM / LOW).
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
          <p class="mt-1 text-xl font-semibold {sev_summary_color("CRITICAL")}">{counts["CRITICAL"]}</p>
        </div>
        <div class="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3">
          <p class="text-[0.7rem] uppercase tracking-[0.18em] text-slate-400">Hautes</p>
          <p class="mt-1 text-xl font-semibold {sev_summary_color("HIGH")}">{counts["HIGH"]}</p>
        </div>
        <div class="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3">
          <p class="text-[0.7rem] uppercase tracking-[0.18em] text-slate-400">Moyennes</p>
          <p class="mt-1 text-xl font-semibold {sev_summary_color("MEDIUM")}">{counts["MEDIUM"]}</p>
        </div>
        <div class="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-3">
          <p class="text-[0.7rem] uppercase tracking-[0.18em] text-slate-400">Basses</p>
          <p class="mt-1 text-xl font-semibold {sev_summary_color("LOW")}">{counts["LOW"]}</p>
        </div>
      </section>

      <section class="space-y-3">
        {''.join(rows)}
      </section>
    </main>
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
