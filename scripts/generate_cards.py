#!/usr/bin/env python3
"""Generate profile cards as static SVGs from GitHub data. Stdlib only.
Usage: GITHUB_TOKEN=... USERNAME=you python scripts/generate_cards.py
       python scripts/generate_cards.py --demo     (no network, fake data)
"""
import base64, datetime as dt, html, json, os, sys, urllib.request

OUT = os.environ.get("OUT_DIR", "assets")
USER = os.environ.get("GH_USER") or "tharun-37"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

LANG_COLORS = {"Python": "#3776ab", "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Java": "#b07219",
               "HTML": "#e34c26", "CSS": "#8b5cf6", "Kotlin": "#a97bff", "C": "#9aa4b2", "C++": "#f34b7d",
               "PHP": "#8892bf", "Jupyter Notebook": "#f37726", "Shell": "#4eaa25", "PowerShell": "#5391fe"}
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',sans-serif"
E = html.escape

QUERY = """query($login:String!,$q:String!){ search(query:$q,type:ISSUE,first:100){ issueCount nodes{... on PullRequest{ repository{ nameWithOwner stargazerCount primaryLanguage{name} } }} }
 user(login:$login){
 forks: repositories(ownerAffiliations:OWNER,isFork:true,first:100){nodes{parent{nameWithOwner}}}
 name login bio avatarUrl createdAt followers{totalCount}
 repositories(ownerAffiliations:OWNER,privacy:PUBLIC,isFork:false,first:100,orderBy:{field:PUSHED_AT,direction:DESC}){
  totalCount nodes{ name description stargazerCount forkCount primaryLanguage{name}
   languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}} } }
 pinnedItems(first:6,types:REPOSITORY){nodes{... on Repository{ name description stargazerCount forkCount primaryLanguage{name} }}}
 contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}
}}"""

def gql():
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER, "q": f"author:{USER} is:pr is:merged -user:{USER}"}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-cards"})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in d: raise SystemExit(d["errors"])
    u = d["data"]["user"]; u["merged"] = d["data"]["search"]
    return u

def avatar_b64(url):
    req = urllib.request.Request(url + ("&" if "?" in url else "?") + "s=240", headers={"User-Agent": "profile-cards"})
    raw = urllib.request.urlopen(req, timeout=30).read()
    return "data:image/png;base64," + base64.b64encode(raw).decode()

def demo():
    import random; random.seed(3)
    today = dt.date.today(); days = []
    for i in range(7 * 26 + today.weekday() + 1)[::-1]:
        d = today - dt.timedelta(days=i)
        days.append({"date": d.isoformat(), "contributionCount": random.choice([0, 0, 0, 0, 1, 2, 5, 9])})
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, len(days), 7)]
    repo = lambda n, l, s=0: {"name": n, "description": "An autonomous vision-language desktop agent that clicks and types for you across apps", "stargazerCount": s, "forkCount": 0,
        "primaryLanguage": {"name": l}, "languages": {"edges": [{"size": s or 100, "node": {"name": l}}]}}
    return {"name": "Demo User", "login": USER, "bio": "Python developer", "avatarUrl": None, "createdAt": "2020-03-01T00:00:00Z",
            "followers": {"totalCount": 2}, "repositories": {"totalCount": 14, "nodes": [
                {**repo("Mini-Project-I", "Java"), "languages": {"edges": [{"size": 500, "node": {"name": "Java"}}]}},
                {**repo("Mini-Project-II", "Kotlin"), "languages": {"edges": [{"size": 300, "node": {"name": "Kotlin"}}]}},
                {**repo("Leetcode_Solutions", "Java"), "languages": {"edges": [{"size": 400, "node": {"name": "Java"}}]}},
                {**repo("IRRIGO", "Python"), "languages": {"edges": [{"size": 6700, "node": {"name": "Python"}}, {"size": 1000, "node": {"name": "TypeScript"}}, {"size": 700, "node": {"name": "HTML"}}]}}]},
            "pinnedItems": {"nodes": []},
            "forks": {"nodes": [{"parent": {"nameWithOwner": "career-ops-hq/career-ops"}}]},
            "merged": {"issueCount": 7, "nodes": [{"repository": {"nameWithOwner": "career-ops-hq/career-ops", "stargazerCount": 9, "primaryLanguage": {"name": "JavaScript"}}}] * 5 + [{"repository": {"nameWithOwner": "RPCS3/rpcs3", "stargazerCount": 15, "primaryLanguage": {"name": "C++"}}}] * 2 + [{"repository": {"nameWithOwner": "some-long-organisation/an-extremely-long-repo-name", "stargazerCount": 1, "primaryLanguage": {"name": "Python"}}}] * 1},
            "contributionsCollection": {"contributionCalendar": {"totalContributions": 298, "weeks": weeks}}}

# ---------- helpers ----------
def frame(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs><linearGradient id="f" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c3aed"/>'
            f'<stop offset=".35" stop-color="#22d3ee"/><stop offset=".65" stop-color="#4ade80"/><stop offset="1" stop-color="#f472b6"/></linearGradient>{defs}</defs>'
            f'<rect width="{w}" height="{h}" rx="20" fill="url(#f)"/><rect x="3" y="3" width="{w-6}" height="{h-6}" rx="18" fill="#0b0b16"/>{body}</svg>')

def t(x, y, s, size=13, fill="#f5f3ff", weight=400, mono=False, anchor="start", spacing=None, opacity=None):
    extra = (f' letter-spacing="{spacing}"' if spacing else "") + (f' fill-opacity="{opacity}"' if opacity else "")
    return (f'<text x="{x}" y="{y}" font-family="{MONO if mono else SANS}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{extra}>{E(str(s))}</text>')

def wrap(text, width=36, lines=2):
    out, cur = [], ""
    for w in text.split():
        if len(cur) + len(w) + (1 if cur else 0) <= width: cur = (cur + " " + w).strip()
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    if len(out) > lines:
        out = out[:lines]; out[-1] = out[-1][:max(0, width - 3)].rstrip() + "..."
    return out
def clip(x, n): return x if len(x) <= n else x[:n - 3] + "..."
def plural(n, w): return f"{n} {w}" + ("" if n == 1 else "s")
def label(x, y, s): return t(x, y, s.upper(), 12, "#7dd3fc", 700, True, spacing=".2em")
def col(lang): return LANG_COLORS.get(lang, "#a5b4fc")

def languages(u):
    tot = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            tot[e["node"]["name"]] = tot.get(e["node"]["name"], 0) + e["size"]
    s = sum(tot.values()) or 1
    return [(k, round(100 * v / s)) for k, v in sorted(tot.items(), key=lambda kv: -kv[1])]

def streaks(days):
    cur = best = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        best = max(best, run)
    cur = 0
    for d in reversed(days):
        if d["contributionCount"]: cur += 1
        elif d is days[-1]: continue          # today may still be empty
        else: break
    return cur, best

def avatar_img(href, x, y, w, h, clip):
    if not href: return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#17172a" clip-path="url(#{clip})"/>'
    return f'<image href="{href}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" clip-path="url(#{clip})"/>'

# ---------- cards ----------
def card_id(u, langs, stats, av):
    top = [l for l, _ in langs[:2]]
    tagline = " \u00b7 ".join(top) + " developer" if top else "Developer"
    since = u["createdAt"][:4]
    tiles = [("stars", stats["stars"]), ("followers", u["followers"]["totalCount"]),
             ("contributions", stats["total"]), ("day streak", stats["cur"])]
    b = f'<rect x="3" y="3" width="874" height="454" rx="18" fill="#05050c"/>'
    # tilted card
    b += '<g transform="rotate(-3 220 230)">'
    b += '<rect x="48" y="30" width="330" height="400" rx="26" fill="url(#f)"/><rect x="58" y="40" width="310" height="380" rx="18" fill="#0f0f1f"/>'
    b += t(76, 76, u["name"] or u["login"], 24, "#f5f3ff", 800) + t(350, 74, f'\u2605 {stats["stars"]}', 14, "#facc15", 700, True, "end")
    b += '<clipPath id="c1"><rect x="76" y="92" width="274" height="170" rx="12"/></clipPath>' + avatar_img(av, 76, 92, 274, 170, "c1")
    b += t(76, 296, f'COMMON \u00b7 {u["repositories"]["totalCount"]} REPOS \u00b7 SINCE {since}', 11, "#a5b4fc", 600, True, spacing=".1em")
    for i, (l, p) in enumerate(langs[:3]):
        y = 326 + i * 28
        b += f'<rect x="76" y="{y-14}" width="18" height="18" rx="5" fill="{col(l)}"/>' + t(104, y, l, 14, "#f5f3ff", 700) + t(350, y, f"{p} PWR", 12, "#a5b4fc", 600, True, "end")
    b += '</g>'
    b += label(450, 70, "Collector's edition \u00b7 " + str(dt.date.today().year))
    b += t(450, 140, "@" + u["login"], 52, "#ffffff", 800)
    b += t(450, 176, tagline, 16, "#a5b4fc")
    for i, (k, v) in enumerate(tiles):
        x, y = 450 + (i % 2) * 196, 214 + (i // 2) * 96
        b += f'<rect x="{x}" y="{y}" width="180" height="82" rx="14" fill="#11111f" stroke="#23233a"/>'
        b += t(x + 20, y + 42, v, 30, "#4ade80" if i % 2 else "#22d3ee", 800) + t(x + 20, y + 66, k.upper(), 11, "#8b8fb3", 500, True, spacing=".12em")
    return frame(880, 460, b.replace('rx="18" fill="#05050c"', 'rx="18" fill="#05050c"'))

def card_about(u, langs, stats, av):
    b = label(36, 52, "Collector card") + t(36, 104, u["name"] or u["login"], 30, "#f5f3ff", 800)
    b += t(36, 140, u["bio"] or ((langs[0][0] + " developer") if langs else "Developer"), 15, "#f5f3ff", opacity=".8")
    b += t(36, 186, f'{u["followers"]["totalCount"]} followers \u00b7 {u["repositories"]["totalCount"]} repositories \u00b7 \u2605 {stats["stars"]} stars', 12, "#a5b4fc", mono=True)
    b += '<circle cx="782" cy="115" r="66" fill="#22d3ee"/><clipPath id="c2"><circle cx="782" cy="115" r="62"/></clipPath>' + avatar_img(av, 720, 53, 124, 124, "c2")
    return frame(880, 230, b)

def card_repo(i, r):
    lang = (r.get("primaryLanguage") or {}).get("name", "")
    b = label(28, 44, f"Card {i:02d}") + t(28, 84, clip(r["name"], 26), 19, "#f5f3ff", 800, True)
    for k, ln in enumerate(wrap(r["description"] or "A project in progress.", 38, 2)):
        b += t(28, 114 + k * 20, ln, 14, "#f5f3ff", opacity=".78")
    b += t(28, 176, f'\u2605 {r["stargazerCount"]}', 13, "#a5b4fc", 700, True) + t(84, 176, f'\u2442 {r["forkCount"]}', 13, "#a5b4fc", 700, True)
    if lang: b += f'<rect x="146" y="162" width="16" height="16" rx="4" fill="{col(lang)}"/>' + t(170, 176, lang, 13, "#a5b4fc", 700, True)
    return frame(430, 204, b)

def card_stack(langs):
    b = label(28, 44, "Powers")
    for i, (l, p) in enumerate(langs[:5]):
        y = 92 + i * 40
        b += f'<rect x="28" y="{y-14}" width="20" height="20" rx="6" fill="{col(l)}"/>' + t(58, y + 2, clip(l, 11), 15, "#f5f3ff", 700)
        b += f'<rect x="166" y="{y-7}" width="190" height="10" rx="5" fill="#2a2a45"/><rect x="166" y="{y-7}" width="{max(8, 1.9*p)}" height="10" rx="5" fill="{col(l)}"/>'
        b += t(402, y + 3, f"{p}%", 14, "#a5b4fc", 700, True, "end")
    return frame(430, 300, b)

def contributions(u):
    forked = {(f.get("parent") or {}).get("nameWithOwner") for f in u["forks"]["nodes"]}
    agg = {}
    for pr in u["merged"]["nodes"]:
        r = pr.get("repository") if pr else None
        if not r: continue
        a = agg.setdefault(r["nameWithOwner"], {"n": 0, "lang": (r.get("primaryLanguage") or {}).get("name", "")})
        a["n"] += 1
    # Only keep repos that are forked AND have at least 1 merged PR
    rows = [(name, a) for name, a in sorted(agg.items(), key=lambda kv: -kv[1]["n"]) if name in forked and a["n"] > 0]
    return rows[:5], u["merged"]["issueCount"], len(rows), forked

def card_contrib(u):
    rows, total, nrepos, forked = contributions(u)
    b = label(28, 44, "Open source projects") + t(402, 44, f"{total} merged \u00b7 {nrepos} repos", 12, "#a5b4fc", 700, True, "end")
    if not rows:
        b += t(28, 110, "No merged pull requests yet", 15, "#f5f3ff", 700)
    for i, (name, a) in enumerate(rows):
        y = 92 + i * 40
        b += f'<rect x="28" y="{y-14}" width="20" height="20" rx="6" fill="{col(a["lang"])}"/>' + t(58, y, clip(name, 27), 14, "#f5f3ff", 700)
        sub = (f'{a["n"]} merged PR' + ("" if a["n"] == 1 else "s")) if a["n"] else "no PR yet"
        tag = '<tspan fill="#c4b5fd">  \u00b7 forked</tspan>' if name in forked else ""
        b += f'<text x="58" y="{y+16}" font-family="{MONO}" font-size="11" fill="#8b8fb3">{E(sub)}{tag}</text>'
        b += t(402, y + 8, a["n"] if a["n"] else "-", 22, "#4ade80" if a["n"] else "#8b8fb3", 800, False, "end")
    return frame(430, 300, b)

def card_log(days, stats):
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)][-26:]
    mx = max([d["contributionCount"] for d in days] + [1])
    b = label(36, 52, "Season \u00b7 26 weeks")
    for wi, w in enumerate(weeks):
        for di, d in enumerate(w):
            c = d["contributionCount"]
            f = "rgba(165,180,252,.1)" if not c else "#4c3a9e" if c < mx * .34 else "#7c5cf0" if c < mx * .67 else "#22d3ee"
            b += f'<rect x="{36+wi*16}" y="{86+di*16}" width="13" height="13" rx="3" fill="{f}"/>'
    for k, (name, v) in enumerate([("Current streak", plural(stats["cur"], "day")), ("Best streak", plural(stats["best"], "day")), ("Contributions this year", stats["total"])]):
        b += t(520, 92 + k * 56, name.upper(), 11, "#a5b4fc", 500, True, spacing=".1em") + t(520, 118 + k * 56, v, 24, "#ffffff", 800)
    return frame(880, 264, b)

def main():
    u = demo() if "--demo" in sys.argv else gql()
    av = None if "--demo" in sys.argv else avatar_b64(u["avatarUrl"])
    days = [d for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    cur, best = streaks(days)
    stats = {"stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
             "total": u["contributionsCollection"]["contributionCalendar"]["totalContributions"], "cur": cur, "best": best}
    langs = languages(u)
    pinned = u["pinnedItems"]["nodes"]
    repos = (pinned + [r for r in u["repositories"]["nodes"] if r["name"] not in {p["name"] for p in pinned}])[:4]
    os.makedirs(OUT, exist_ok=True)
    files = {"id.svg": card_id(u, langs, stats, av), "about.svg": card_about(u, langs, stats, av),
             "stack.svg": card_stack(langs), "contrib.svg": card_contrib(u), "log.svg": card_log(days, stats)}
    for i, r in enumerate(repos, 1): files[f"repo-{i}.svg"] = card_repo(i, r)
    for n, s in files.items():
        open(os.path.join(OUT, n), "w", encoding="utf-8").write(s)
    print("wrote", ", ".join(files), "\u2192", OUT)

if __name__ == "__main__": main()
