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


