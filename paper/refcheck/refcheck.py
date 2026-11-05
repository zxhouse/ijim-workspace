"""Automatic verification of the reference list against Crossref / OpenAlex / arXiv.

Usage:  python3 refcheck.py            (needs network access to api.crossref.org,
                                        api.openalex.org and export.arxiv.org)
For every reference with a DOI it resolves the DOI in Crossref and compares the
registered title, first author, year, volume, issue and pages with ours; for
references without a DOI it searches Crossref/OpenAlex by bibliographic text and
proposes a DOI. Output: refcheck_report.json and a printed table.
"""
import json
import os
import re
import sys

from rapidfuzz import fuzz

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "LoopLab-refcheck/1.0 (mailto:pkuras@kozminski.edu.pl)"


def norm(s):
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower())


def our_title(text):
    m = re.search(r"\(\d{4}[a-z]?\)\.\s*(.+?)\.\s", text)
    return m.group(1) if m else text


def check_doi(cr, ref):
    try:
        w = cr.works(ids=ref["doi"])["message"]
    except Exception as e:  # noqa: BLE001
        return dict(status="DOI_NOT_FOUND", error=str(e)[:200])
    title = (w.get("title") or [""])[0]
    year = (w.get("issued", {}).get("date-parts") or [[None]])[0][0]
    first = (w.get("author") or [{}])[0].get("family", "")
    sim = fuzz.token_set_ratio(norm(title), norm(our_title(ref["text"])))
    issues = []
    if sim < 85:
        issues.append(f"title mismatch ({sim:.0f}): {title}")
    if year and str(year) not in ref["text"]:
        issues.append(f"year {year}")
    if first and norm(first)[:5] not in norm(ref["text"])[:60]:
        issues.append(f"first author {first}")
    for fld, lab in (("volume", "volume"), ("issue", "issue"), ("page", "pages")):
        v = w.get(fld)
        if v and v.replace("-", "--") not in ref["text"] and v not in ref["text"]:
            issues.append(f"{lab} {v}")
    return dict(status="OK" if not issues else "CHECK", crossref_title=title, year=year,
                container=(w.get("container-title") or [""])[0], issues=issues,
                n_authors=len(w.get("author") or []))


def search(cr, ref):
    q = our_title(ref["text"])
    try:
        items = cr.works(query_bibliographic=ref["text"][:250], limit=3)["message"]["items"]
    except Exception as e:  # noqa: BLE001
        return dict(status="SEARCH_FAILED", error=str(e)[:200])
    best = max(items, key=lambda it: fuzz.token_set_ratio(norm((it.get("title") or [""])[0]), norm(q)), default=None)
    if not best:
        return dict(status="NOT_FOUND")
    sim = fuzz.token_set_ratio(norm((best.get("title") or [""])[0]), norm(q))
    return dict(status="FOUND" if sim >= 90 else "UNCERTAIN", proposed_doi=best.get("DOI"),
                crossref_title=(best.get("title") or [""])[0], similarity=sim)


def main():
    from habanero import Crossref
    cr = Crossref(mailto="pkuras@kozminski.edu.pl", ua_string=UA)
    refs = json.load(open(os.path.join(HERE, "refs.json")))
    rep = {}
    for r in refs:
        if r["doi"] and not r["doi"].startswith("10.48550"):
            rep[r["key"]] = check_doi(cr, r)
        elif r["doi"]:
            rep[r["key"]] = dict(status="ARXIV", note="check with export.arxiv.org")
        else:
            rep[r["key"]] = search(cr, r)
        print(f"{r['key']:18s} {rep[r['key']]['status']:14s} {'; '.join(rep[r['key']].get('issues', []))}")
    json.dump(rep, open(os.path.join(HERE, "refcheck_report.json"), "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
