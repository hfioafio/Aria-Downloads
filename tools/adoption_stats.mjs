// Relevé des compteurs publics d'Aria pour docs/stats.html.
//   node tools/adoption_stats.mjs <history.json> <latest.json>
// Source : métadonnées publiques des versions GitHub de ce dépôt (nombre de téléchargements par
// fichier). Aucun identifiant, aucune donnée personnelle. Un instantané n'est ajouté que si un
// compteur a changé, ou au premier relevé d'un jour de Paris, pour que l'historique reste court.
import { existsSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { pathToFileURL } from 'node:url'

const REPO = process.env.GITHUB_REPOSITORY || 'hfioafio/Aria-Downloads'
const ADOPTION_TAG = 'adoption-counter'
const ADOPTION_KINDS = ['install', 'update', 'active', 'active-day', 'owner-update', 'owner-download']

const PARIS_DAY = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Europe/Paris',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit'
})

export function parisDay(date) {
  const parts = Object.fromEntries(PARIS_DAY.formatToParts(date).map(({ type, value }) => [type, value]))
  return `${parts.year}-${parts.month}-${parts.day}`
}

async function fetchReleases() {
  const headers = { Accept: 'application/vnd.github+json', 'User-Agent': 'aria-adoption-stats' }
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`
  const all = []
  for (let page = 1; page <= 20; page++) {
    // Sans délai maximal, une API qui ne répond plus bloquerait le job jusqu'à son timeout.
    const response = await fetch(`https://api.github.com/repos/${REPO}/releases?per_page=100&page=${page}`, {
      headers,
      signal: AbortSignal.timeout(30_000)
    })
    if (!response.ok) throw new Error(`GitHub API ${response.status}`)
    const batch = await response.json()
    if (!Array.isArray(batch)) throw new Error('GitHub API : réponse inattendue')
    all.push(...batch)
    if (batch.length < 100) break
  }
  return all
}

function count(asset) {
  const value = Number(asset?.download_count)
  return Number.isSafeInteger(value) && value >= 0 ? value : 0
}

function bucket() {
  return { arm: 0, intel: 0, total: 0 }
}

function add(target, asset) {
  const value = count(asset)
  if (/Apple-Silicon|arm64/i.test(asset.name)) target.arm += value
  else target.intel += value
  target.total += value
}

/**
 * Depuis la 2.61.0, « Aria-Installer-… » est téléchargé depuis le site et le fichier identique
 * sans « Installer » par les mises à jour. Une version sans fichier Installer reste « mixte ».
 */
export function classify(release) {
  const dmg = (release.assets || []).filter((asset) => /\.dmg$/i.test(asset.name || ''))
  if (!dmg.length) return null
  const installer = dmg.filter((asset) => /^Aria-Installer-/.test(asset.name))
  const row = {
    tag: release.tag_name,
    date: String(release.published_at || '').slice(0, 10),
    // « rc » seul, ou suivi d'un numéro : un mot qui contient « rc » n'est pas une préversion.
    pre: release.prerelease === true || /preview|beta|(?:^|[^a-z])rc(?:\d|[^a-z]|$)/i.test(release.tag_name || ''),
    site: bucket(),
    update: bucket(),
    mixed: bucket()
  }
  for (const asset of dmg) {
    if (!installer.length) add(row.mixed, asset)
    else if (installer.includes(asset)) add(row.site, asset)
    else add(row.update, asset)
  }
  return row
}

export function summarize(releases, now) {
  const rows = releases.map(classify).filter(Boolean)
  const downloads = { site: bucket(), update: bucket(), mixed: bucket() }
  for (const row of rows) {
    for (const key of ['site', 'update', 'mixed']) {
      downloads[key].arm += row[key].arm
      downloads[key].intel += row[key].intel
      downloads[key].total += row[key].total
    }
  }
  const counter = releases.find((release) => release.tag_name === ADOPTION_TAG)
  const adoption = Object.fromEntries(
    ADOPTION_KINDS.map((kind) => [kind, count((counter?.assets || []).find((a) => a.name === `${kind}.txt`))])
  )
  const latestPublic = rows
    .filter((row) => !row.pre)
    .sort((a, b) => (a.date < b.date ? 1 : -1))[0]
  return {
    at: now.toISOString(),
    day: parisDay(now),
    downloads,
    adoption,
    latest: latestPublic
      ? { tag: latestPublic.tag, site: latestPublic.site.total, update: latestPublic.update.total, mixed: latestPublic.mixed.total }
      : null,
    rows
  }
}

function signature(snapshot) {
  return JSON.stringify([snapshot.downloads, snapshot.adoption, snapshot.latest])
}

function readHistory(path) {
  if (!existsSync(path)) return { schema: 1, repo: REPO, snapshots: [] }
  const data = JSON.parse(readFileSync(path, 'utf8'))
  if (!Array.isArray(data.snapshots)) throw new Error('historique illisible')
  return data
}

// Écriture atomique : un job interrompu ne laisse jamais un historique tronqué sur stats-data.
function writeJson(path, data) {
  const temporary = `${path}.tmp`
  writeFileSync(temporary, `${JSON.stringify(data, null, 1)}\n`)
  renameSync(temporary, path)
}

async function main(historyPath, latestPath) {
  const now = new Date()
  // STATS_RELEASES_FILE : liste de versions déjà téléchargée (contrôle local, sans réseau).
  const source = process.env.STATS_RELEASES_FILE
    ? JSON.parse(readFileSync(process.env.STATS_RELEASES_FILE, 'utf8'))
    : await fetchReleases()
  const summary = summarize(source, now)
  const { rows, ...snapshot } = summary
  const history = readHistory(historyPath)
  const last = history.snapshots[history.snapshots.length - 1]
  const changed = !last || last.day !== snapshot.day || signature(last) !== signature(snapshot)
  if (changed) history.snapshots.push(snapshot)

  writeJson(historyPath, history)
  writeJson(latestPath, { ...snapshot, rows })
  console.log(
    `${changed ? 'Nouvel instantané' : 'Inchangé'} — site ${snapshot.downloads.site.total}, ` +
      `mises à jour ${snapshot.downloads.update.total}, mixtes ${snapshot.downloads.mixed.total}, ` +
      `adoption ${JSON.stringify(snapshot.adoption)}`
  )
}

// Exécuté seulement en ligne de commande : les fonctions exportées restent importables en test.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [historyPath, latestPath] = process.argv.slice(2)
  if (!historyPath || !latestPath) {
    console.error('usage: node tools/adoption_stats.mjs <history.json> <latest.json>')
    process.exit(2)
  }
  await main(historyPath, latestPath)
}
