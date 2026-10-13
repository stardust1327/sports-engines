"""Your team notes for the NFL picks: manual calls on a team's effort from
watching its games, applied to both NFL models, shown in the reports, and
graded so you can see whether they're right. Added 2026-10-12 at the owner's
request: a human factor to fine-tune the statistical metrics.

The kinds (the owner's own definitions are in team_notes.json):
  Unreliable   a team that doesn't want to win or looks lazy, whose earlier
               results came from luck rather than effort: it loses games it
               shouldn't have lost. Losing a game by itself doesn't make a team
               unreliable. Docked 3 points by default.
  Max effort   a team that plays hard and aggressive and is out there to win
               every game. Slightly boosted: 1.5 points by default.
Notes are manual, case by case: only the owner adds, changes or removes one.

How a note moves the numbers. Its points go on the noted team's predicted
margin. The models' own numbers in the picks files are never changed (they are
the "model alone" numbers); the notes are applied whenever the files are read:
  engine     the win chance moves along the engine's own scale: 7.8 points per
             unit of log-odds, fit on its 2019-2025 backtest (1,522 games)
  framework  its predicted margin moves by the points, and its win chance and
             predicted score follow its own margin scale (about 7.7)
In a close game 1.5 points is worth about 5 points of win chance and 3 points
about 10; less for a big favorite.

Timing. Every note keeps the time it was set and only counts for games that
kick off after that, like a pick logged before kickoff.

Official picks are the ones with the notes applied. The model-alone pick stays
next to it in every report and graded file, so the two can be compared.

  python3 results/team_notes.py list
  python3 results/team_notes.py set --team Rams --said "the owner's words" [--points -3] [--at 2026-10-13T04:14Z]
  python3 results/team_notes.py set --team Bills --kind max_effort --said "the owner's words" [--points 1.5]
  python3 results/team_notes.py clear --team Rams --said "the owner's words"
  python3 results/team_notes.py show --season 2026 --week 6
  python3 results/team_notes.py grade --season 2026 --week 6   (after nfl_cfbmethod/grade.py and grade_picks.py)
  python3 results/team_notes.py scorecard
"""
import argparse
import datetime
import json
import math
import os
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
NOTES_FILE = os.environ.get("TEAM_NOTES_FILE") or os.path.join(HERE, "team_notes.json")  # the env var is for tests
GRADED_NAME = "team_notes_graded.csv"

# Fit 2026-10-12: final home margin regressed on the engine's log-odds over its
# 2019-2025 backtest (1,522 games, no intercept): 7.81 points per unit.
ENGINE_PTS_PER_LOGIT = 7.8
FRAMEWORK_PTS_PER_LOGIT_FALLBACK = 7.7   # used only if a framework file can't give its own scale
# How far a final margin lands from each model's expected margin in one game
# (standard deviation; engine backtest 2019-2025, framework backtest 2022-2025).
SD_POINTS = {"engine": 13.4, "framework": 12.8}

TEAMS = ["49ers", "Bears", "Bengals", "Bills", "Broncos", "Browns", "Buccaneers", "Cardinals", "Chargers",
         "Chiefs", "Colts", "Commanders", "Cowboys", "Dolphins", "Eagles", "Falcons", "Giants", "Jaguars",
         "Jets", "Lions", "Packers", "Panthers", "Patriots", "Raiders", "Rams", "Ravens", "Saints",
         "Seahawks", "Steelers", "Texans", "Titans", "Vikings"]
PHX = ZoneInfo("America/Phoenix")
ET = ZoneInfo("America/New_York")
UTC = datetime.timezone.utc


# ------------------------------------------------------------------ notes

def parse_time(s):
    t = datetime.datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    if t.tzinfo is None:
        raise ValueError(f"time without a time zone: {s}")
    return t.astimezone(UTC)


def load(path=None):
    """Read and check the notes file. Events come back sorted by the time they were set."""
    with open(path or NOTES_FILE) as f:
        d = json.load(f)
    kinds = d["kinds"]
    for e in d["events"]:
        if e.get("action") not in ("set", "clear"):
            raise SystemExit(f"team_notes.json: unknown action in {e}")
        if e.get("team") not in TEAMS:
            raise SystemExit(f"team_notes.json: '{e.get('team')}' isn't an NFL nickname")
        if e["action"] == "set":
            if e.get("kind") not in kinds:
                raise SystemExit(f"team_notes.json: unknown kind in {e}")
            pts = float(e["points"])
            if (pts >= 0) == (kinds[e["kind"]]["default_points"] < 0) or pts == 0:
                raise SystemExit(f"team_notes.json: points {pts} have the wrong sign for '{e['kind']}' ({e['team']})")
        e["_t"] = parse_time(e["set_at"])
    d["events"] = sorted(d["events"], key=lambda e: e["_t"])
    return d


def in_force(notes, team, when):
    """The note in force for `team` at `when` (a UTC datetime), or None. A note set
    at or after kickoff doesn't count for that game."""
    cur = None
    for e in notes["events"]:
        if e["team"] == team and e["_t"] < when:
            cur = e if e["action"] == "set" else None
    return cur


def label(notes, e):
    return notes["kinds"][e["kind"]]["label"]


def note_text(notes, e, team=True):
    """'Rams: plays hard +1.5' (team=True) or 'Plays hard +1.5'."""
    lab = label(notes, e)
    return f"{e['team']}: {lab.lower()} {float(e['points']):+.1f}" if team else f"{lab} {float(e['points']):+.1f}"


def current(notes, now=None):
    """Notes in force now (or at `now`), one per team, in team order."""
    now = now or datetime.datetime.now(UTC)
    out = [in_force(notes, t, now) for t in TEAMS]
    return [e for e in out if e is not None]


def phx(t):
    return t.astimezone(PHX).strftime("%Y-%m-%d %I:%M %p").replace(" 0", " ") + " Phoenix"


# ------------------------------------------------------------- apply them

def logit(p):
    return math.log(p / (1 - p))


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def kickoffs(df):
    """Kickoff of every game as a UTC datetime: engine files have kickoff_utc,
    framework files the game day and Eastern kickoff time."""
    if "kickoff_utc" in df.columns:
        return [datetime.datetime.strptime(str(k), "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC) for k in df["kickoff_utc"]]
    if "gameday" in df.columns and "kickoff_et" in df.columns:
        return [datetime.datetime.strptime(f"{d} {k}", "%Y-%m-%d %H:%M").replace(tzinfo=ET).astimezone(UTC)
                for d, k in zip(df["gameday"], df["kickoff_et"])]
    raise SystemExit("picks file has no kickoff times (kickoff_utc, or gameday + kickoff_et)")


def framework_scale(df):
    """Points per unit of log-odds in a framework file: its margin and win chance
    both come from the same weighted score, so their ratio is fixed. Taken from
    games with a margin of 2+ points, where rounding barely matters."""
    p = pd.to_numeric(df["p_home"], errors="coerce")
    m = pd.to_numeric(df["margin_home"], errors="coerce")
    ok = p.between(0.001, 0.999) & (m.abs() >= 2)
    if not ok.any():
        return FRAMEWORK_PTS_PER_LOGIT_FALLBACK
    return float(np.median(m[ok] / np.log(p[ok] / (1 - p[ok]))))


def framework_score(pick_home, home, away, margin, total):
    """Predicted score the way prompt_football/nfl.py writes it."""
    hp, ap_ = (total + margin) / 2, (total - margin) / 2
    hs, as_ = int(math.floor(hp + 0.5)), int(math.floor(ap_ + 0.5))
    if pick_home and hs <= as_:
        hs = as_ + 1
    if not pick_home and as_ <= hs:
        as_ = hs + 1
    pick, other = (home, away) if pick_home else (away, home)
    return f"{pick} {max(hs, as_)} - {other} {min(hs, as_)}"


def apply(df, model, notes=None):
    """A copy of a picks table with the team notes applied.

    model: "engine" (nfl_cfbmethod_*_picks.csv) or "framework" (prompt_nfl_*_picks.csv).
    Adds note_text, noted_away and noted_home (True when that team has a note in
    force), note_pts_home (points on the home team's margin: its own note minus the
    away team's), p_home_noted, pick_noted, pick_prob_noted and note_flips;
    framework tables also get margin_home_noted, score_noted and confidence_noted.
    Picks without a note in force keep their own numbers in the _noted columns;
    no-picks stay no-picks. The model's own columns are left as they are."""
    if model not in ("engine", "framework"):
        raise ValueError(model)
    notes = notes or load()
    out = df.copy().reset_index(drop=True)
    kick = kickoffs(out)
    scale = ENGINE_PTS_PER_LOGIT if model == "engine" else framework_scale(out)
    cols = {c: [] for c in ("note_text", "noted_away", "noted_home", "note_pts_home", "p_home_noted", "pick_noted",
                            "pick_prob_noted", "note_flips")}
    if model == "framework":
        cols.update(margin_home_noted=[], score_noted=[], confidence_noted=[])
    for i, r in out.iterrows():
        home, away = r["home_name"], r["away_name"]
        nh, na = in_force(notes, home, kick[i]), in_force(notes, away, kick[i])
        pts = (float(nh["points"]) if nh else 0.0) - (float(na["points"]) if na else 0.0)
        cols["note_text"].append("; ".join(note_text(notes, e) for e in (na, nh) if e))
        cols["noted_away"].append(na is not None)
        cols["noted_home"].append(nh is not None)
        cols["note_pts_home"].append(pts)
        if r["status"] != "PICK":
            for c in ("p_home_noted", "pick_noted", "pick_prob_noted"):
                cols[c].append(np.nan)
            cols["note_flips"].append(False)
            if model == "framework":
                cols["margin_home_noted"].append(np.nan)
                cols["score_noted"].append(np.nan)
                cols["confidence_noted"].append(np.nan)
            continue
        p = float(r["p_home"])
        if pts:
            p2 = sigmoid(logit(p) + pts / scale)
            pick2 = home if p2 >= 0.5 else away
            prob2 = max(p2, 1 - p2)
        else:
            p2, pick2, prob2 = p, r["pick"], float(r["pick_prob"])
        cols["p_home_noted"].append(p2)
        cols["pick_noted"].append(pick2)
        cols["pick_prob_noted"].append(prob2)
        cols["note_flips"].append(bool(pick2 != r["pick"]))
        if model == "framework":
            margin = float(r["margin_home"])
            cols["margin_home_noted"].append(margin + pts)
            cols["score_noted"].append(framework_score(p2 >= 0.5, home, away, margin + pts, float(r["total"]))
                                       if pts else r["score"])
            cols["confidence_noted"].append(int(math.floor(10 * prob2 + 0.5)) if pts else r["confidence"])
    for c, v in cols.items():
        out[c] = v
    return out


def noted_teams(notes, row, when):
    """[(team, opponent, side, note)] for every noted team in a game."""
    out = []
    for side, team, opp in (("home", row["home_name"], row["away_name"]), ("away", row["away_name"], row["home_name"])):
        e = in_force(notes, team, when)
        if e:
            out.append((team, opp, side, e))
    return out


def result_of(pick, away, home, away_score, home_score):
    """W / L / T for a pick, '' while the game isn't final or there's no pick."""
    if not isinstance(pick, str) or not pick or pd.isna(away_score) or pd.isna(home_score):
        return ""
    if away_score == home_score:
        return "T"
    return "W" if pick == (home if home_score > away_score else away) else "L"


def rec(results):
    r = pd.Series(list(results), dtype=object).fillna("")
    w, l, t = int((r == "W").sum()), int((r == "L").sum()), int((r == "T").sum())
    return f"{w}-{l}-{t}" if t else f"{w}-{l}"


# ---------------------------------------------------------------- grading

def files(results_dir, season, week):
    ww = f"{week:02d}"
    names = {"engine": (f"nfl_cfbmethod_{season}_week{ww}_picks.csv", f"nfl_cfbmethod_{season}_week{ww}_graded.csv"),
             "framework": (f"prompt_nfl_{season}_week{ww}_picks.csv", f"prompt_nfl_{season}_week{ww}_graded.csv")}
    out = {}
    for model, (p, g) in names.items():
        pp, gp = os.path.join(results_dir, p), os.path.join(results_dir, g)
        out[model] = (pd.read_csv(pp, dtype={"game_id": str}) if os.path.exists(pp) else None,
                      pd.read_csv(gp, dtype={"game_id": str}) if os.path.exists(gp) else None)
    return out


def scores_by_game(*graded):
    """game_id -> (away_score, home_score) from whichever graded files have it."""
    out = {}
    for g in graded:
        if g is None:
            continue
        for r in g.itertuples():
            if pd.notna(r.away_score) and pd.notna(r.home_score) and r.game_id not in out:
                out[r.game_id] = (int(r.away_score), int(r.home_score))
    return out


def week_rows(season, week, results_dir=HERE, notes=None):
    """Graded rows for every noted team in every graded pick of a week, both models,
    plus each model's week record with and without the notes."""
    notes = notes or load()
    f = files(results_dir, season, week)
    sc = scores_by_game(f["engine"][1], f["framework"][1])
    rows, records = [], {}
    for model in ("engine", "framework"):
        picks, graded = f[model]
        if picks is None:
            continue
        if graded is None:
            records[model] = None
            continue
        a = apply(picks, model, notes)
        kick = kickoffs(a)
        scale = ENGINE_PTS_PER_LOGIT if model == "engine" else None
        res_n, res_a, flips = [], [], []
        for i, r in a.iterrows():
            if r["status"] != "PICK" or r["game_id"] not in sc:
                continue
            a_sc, h_sc = sc[r["game_id"]]
            rn = result_of(r["pick_noted"], r["away_name"], r["home_name"], a_sc, h_sc)
            ra = result_of(r["pick"], r["away_name"], r["home_name"], a_sc, h_sc)
            res_n.append(rn)
            res_a.append(ra)
            if r["note_flips"]:
                flips.append((r, rn, ra))
            for team, opp, side, e in noted_teams(notes, r, kick[i]):
                sign = 1 if side == "home" else -1
                p_alone = float(r["p_home"]) if side == "home" else 1 - float(r["p_home"])
                p_noted = float(r["p_home_noted"]) if side == "home" else 1 - float(r["p_home_noted"])
                if model == "engine":
                    exp_margin = scale * logit(p_alone)
                else:
                    exp_margin = sign * float(r["margin_home"])
                t_sc, o_sc = (h_sc, a_sc) if side == "home" else (a_sc, h_sc)
                rows.append({
                    "season": season, "week": week, "game_id": r["game_id"],
                    "kickoff_utc": kick[i].strftime("%Y-%m-%dT%H:%MZ"), "model": model,
                    "team": team, "opponent": opp, "side": side, "kind": e["kind"], "note": label(notes, e),
                    "points": float(e["points"]), "note_set_at": e["set_at"],
                    "p_team_alone": round(p_alone, 4), "p_team_noted": round(p_noted, 4),
                    "pick_alone": r["pick"], "pick_noted": r["pick_noted"], "flipped": bool(r["note_flips"]),
                    "team_score": t_sc, "opp_score": o_sc,
                    "team_result": "T" if t_sc == o_sc else ("W" if t_sc > o_sc else "L"),
                    "team_margin": t_sc - o_sc, "exp_margin_alone": round(exp_margin, 2),
                    "result_alone": ra, "result_noted": rn,
                })
        records[model] = {"noted": rec(res_n), "alone": rec(res_a), "flips": flips, "graded": len(res_n)}
    return pd.DataFrame(rows), records


GRADED_COLS = ["season", "week", "game_id", "kickoff_utc", "model", "team", "opponent", "side", "kind", "note",
               "points", "note_set_at", "p_team_alone", "p_team_noted", "pick_alone", "pick_noted", "flipped",
               "team_score", "opp_score", "team_result", "team_margin", "exp_margin_alone", "result_alone",
               "result_noted"]


def save_week(df, season, week, results_dir=HERE):
    """Replace the week's rows in team_notes_graded.csv (re-grading a week is safe)."""
    path = os.path.join(results_dir, GRADED_NAME)
    old = pd.read_csv(path, dtype={"game_id": str}) if os.path.exists(path) else pd.DataFrame(columns=GRADED_COLS)
    old = old[~((old["season"] == season) & (old["week"] == week))]
    parts = [x for x in (old, df.reindex(columns=GRADED_COLS)) if len(x)]
    new = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=GRADED_COLS)
    if len(new):
        new = new.sort_values(["season", "week", "kickoff_utc", "model", "team"]).reset_index(drop=True)
    new.to_csv(path, index=False)
    return path, new


def summarize(g, model):
    """One scorecard line from graded rows (one model)."""
    g = g[g["model"] == model]
    n = len(g)
    if not n:
        return None
    y = g["team_result"].map({"W": 1.0, "L": 0.0, "T": 0.5}).to_numpy()
    pa, pn = g["p_team_alone"].to_numpy(float), g["p_team_noted"].to_numpy(float)
    exp_w = pa.sum()
    resid = (g["team_margin"] - g["exp_margin_alone"]).to_numpy(float)
    pts_vs = float(resid.mean())
    luck_pts = 2 * SD_POINTS[model] / math.sqrt(n)
    direction = 1 if g["points"].mean() > 0 else -1
    flips = g.drop_duplicates("game_id")
    flips = flips[flips["flipped"].astype(str).str.lower() == "true"]
    if pts_vs * direction > 0:
        status = "Your way" + (", beyond luck" if abs(pts_vs) > luck_pts else ", within luck so far")
    elif pts_vs * direction < 0:
        status = "Against your note" + (", beyond luck" if abs(pts_vs) > luck_pts else ", within luck so far")
    else:
        status = "Even so far"
    return {
        "games": n, "record": rec(g["team_result"]), "exp_wins": exp_w, "wins": float(y.sum()),
        "wins_vs": float(y.sum() - exp_w), "luck_wins": 2 * math.sqrt(float((pa * (1 - pa)).sum())),
        "pts_vs": pts_vs, "luck_pts": luck_pts,
        "brier_alone": float(np.mean((pa - y) ** 2)), "brier_noted": float(np.mean((pn - y) ** 2)),
        "flips": len(flips), "flips_noted": rec(flips["result_noted"]), "flips_alone": rec(flips["result_alone"]),
        "status": status,
    }


def scorecard(results_dir=HERE, notes=None):
    """Rows for every note (team + kind) ever set, both models, plus a total per
    kind when more than one team has it. Teams with no graded games yet are
    listed with None for the numbers."""
    notes = notes or load()
    path = os.path.join(results_dir, GRADED_NAME)
    g = pd.read_csv(path, dtype={"game_id": str}) if os.path.exists(path) else pd.DataFrame(
        columns=["team", "kind", "model", "game_id", "points", "note_set_at"])
    now = datetime.datetime.now(UTC)
    teams = []
    for e in notes["events"]:
        if e["action"] == "set" and (e["team"], e["kind"]) not in [(t, k) for t, k, _ in teams]:
            teams.append((e["team"], e["kind"], e))
    out = []
    for team, kind, first in teams:
        live = in_force(notes, team, now)
        latest = [e for e in notes["events"] if e["team"] == team and e.get("kind") == kind and e["action"] == "set"][-1]
        cleared = live is None or live["kind"] != kind
        sub = g[(g["team"] == team) & (g["kind"] == kind)] if len(g) else g
        for model in ("engine", "framework"):
            out.append({"team": team, "kind": kind, "label": f"{notes['kinds'][kind]['label']} {float(latest['points']):+.1f}",
                        "since": first["_t"], "cleared": cleared, "model": model,
                        "s": summarize(sub, model) if len(sub) else None})
    kinds_used = {}
    for team, kind, _ in teams:
        kinds_used.setdefault(kind, []).append(team)
    for kind, ts in kinds_used.items():
        if len(ts) < 2:
            continue
        sub = g[g["kind"] == kind] if len(g) else g
        for model in ("engine", "framework"):
            out.append({"team": f"All {notes['kinds'][kind]['label'].lower()}", "kind": kind,
                        "label": f"{len(ts)} teams", "since": None, "cleared": False, "model": model,
                        "s": summarize(sub, model) if len(sub) else None})
    return out


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def print_scorecard(results_dir=HERE, notes=None):
    rows = scorecard(results_dir, notes)
    if not rows:
        print("No team notes yet.")
        return
    print("Team notes scorecard (graded picks with a noted team; 'luck' = the range chance alone covers 95% of the time):")
    for r in rows:
        s = r["s"]
        head = f"  {r['team']} ({r['label']}{', cleared' if r['cleared'] else ''}) vs the {r['model']}:"
        if not s:
            print(f"{head} no graded games yet")
            continue
        print(f"{head} {plural(s['games'], 'game')}, team {s['record']}; the {r['model']} alone expected {s['exp_wins']:.1f} wins "
              f"({s['wins_vs']:+.1f}, luck +/-{s['luck_wins']:.1f}); points per game vs the {r['model']} alone "
              f"{s['pts_vs']:+.1f} (luck +/-{s['luck_pts']:.1f}); win-chance accuracy (Brier, lower is better) "
              f"{s['brier_noted']:.3f} with the note vs {s['brier_alone']:.3f} without; picks the note changed "
              f"{s['flips']}" + (f" (with the note {s['flips_noted']}, model alone {s['flips_alone']})" if s["flips"] else "")
              + f". {s['status']}.")


# -------------------------------------------------------------------- CLI

def cmd_list(a):
    notes = load()
    now = current(notes)
    print("Team notes in force now:" if now else "No team notes in force.")
    for e in now:
        print(f"  {note_text(notes, e)} points (set {phx(e['_t'])})")
    print("History:")
    for e in notes["events"]:
        what = note_text(notes, e) if e["action"] == "set" else f"{e['team']}: note cleared"
        print(f"  {phx(e['_t'])}  {what}  | owner: \"{e.get('owner_said', '')}\"")


def write_event(event):
    with open(NOTES_FILE) as f:
        d = json.load(f)
    d["events"].append(event)
    tmp = NOTES_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")
    try:
        load(tmp)  # check the result before replacing the file
    except BaseException:
        os.remove(tmp)
        raise
    os.replace(tmp, NOTES_FILE)


def event_time(at):
    t = parse_time(at) if at else datetime.datetime.now(UTC)
    if t > datetime.datetime.now(UTC) + datetime.timedelta(minutes=1):
        raise SystemExit("--at is in the future")
    return t.strftime("%Y-%m-%dT%H:%MZ")


def cmd_set(a):
    notes = load()
    if a.team not in TEAMS:
        raise SystemExit(f"'{a.team}' isn't an NFL nickname ({', '.join(TEAMS)})")
    if a.kind not in notes["kinds"]:
        raise SystemExit(f"unknown kind '{a.kind}' (team_notes.json has: {', '.join(notes['kinds'])})")
    pts = a.points if a.points is not None else notes["kinds"][a.kind]["default_points"]
    write_event({"set_at": event_time(a.at), "action": "set", "team": a.team, "kind": a.kind,
                 "points": float(pts), "owner_said": a.said})
    notes = load()
    print(f"Set: {note_text(notes, in_force(notes, a.team, datetime.datetime.now(UTC) + datetime.timedelta(minutes=2)))}"
          f" (counts for games kicking off after it was set)")


def cmd_clear(a):
    notes = load()
    if in_force(notes, a.team, datetime.datetime.now(UTC) + datetime.timedelta(minutes=2)) is None:
        raise SystemExit(f"{a.team} has no note in force")
    write_event({"set_at": event_time(a.at), "action": "clear", "team": a.team, "owner_said": a.said})
    print(f"Cleared the note on the {a.team} (games already graded keep it)")


def cmd_show(a):
    notes = load()
    f = files(a.dir, a.season, a.week)
    for model in ("engine", "framework"):
        picks = f[model][0]
        if picks is None:
            print(f"{model}: no picks file for {a.season} week {a.week}")
            continue
        t = apply(picks, model, notes)
        t = t.assign(_k=kickoffs(t)).sort_values(["_k", "away_name"])
        print(f"\n{'Engine (official)' if model == 'engine' else 'Framework'}, week {a.week}, with your team notes:")
        for r in t.itertuples():
            game = f"{r.away_name} at {r.home_name}"
            if r.status != "PICK":
                print(f"  {game}: no pick ({r.reason})")
                continue
            line = f"  {game}: {r.pick_noted} {r.pick_prob_noted:.1%}"
            if r.note_text:
                line += f"   [{r.note_text}; model alone {r.pick} {float(r.pick_prob):.1%}]"
                if r.note_flips:
                    line += "  <- THE NOTE CHANGED THIS PICK"
            if model == "framework" and r.note_text:
                line += f"  score {r.score_noted}"
            print(line)


def cmd_grade(a):
    notes = load()
    df, records = week_rows(a.season, a.week, a.dir, notes)
    path, _ = save_week(df, a.season, a.week, a.dir)
    for model, rcd in records.items():
        name = "Engine" if model == "engine" else "Framework"
        if rcd is None:
            print(f"{name}: not graded yet (run {'nfl_cfbmethod/grade.py' if model == 'engine' else 'results/grade_picks.py'} first)")
            continue
        same = "same: no pick changed by a note" if not rcd["flips"] else f"{len(rcd['flips'])} pick(s) changed by a note"
        print(f"{name} week {a.week}: official (with your team notes) {rcd['noted']} | {model} alone {rcd['alone']} ({same})")
        for r, rn, ra in rcd["flips"]:
            print(f"    {r['away_name']} at {r['home_name']}: with the note {r['pick_noted']} ({rn}), alone {r['pick']} ({ra})")
    noted = df[df["model"] == "engine"] if len(df) else df
    if len(noted):
        print(f"Noted games this week (engine): " + "; ".join(
            f"{x.team} {x.team_result} {x.team_score}-{x.opp_score} vs {x.opponent} (alone {x.p_team_alone:.0%}, "
            f"with note {x.p_team_noted:.0%})" for x in noted.itertuples()))
    else:
        print("No graded picks with a noted team this week.")
    print(f"Saved {path}\n")
    print_scorecard(a.dir, notes)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    s = sub.add_parser("set")
    s.add_argument("--team", required=True, help="NFL nickname, e.g. Rams")
    s.add_argument("--kind", default="unreliable", help="a kind listed in team_notes.json (default: unreliable)")
    s.add_argument("--points", type=float, help="default: the kind's default_points (unreliable: -3.0)")
    s.add_argument("--said", required=True, help="the owner's words")
    s.add_argument("--at", help="when the owner said it (ISO time with zone); default now")
    c = sub.add_parser("clear")
    c.add_argument("--team", required=True)
    c.add_argument("--said", required=True)
    c.add_argument("--at")
    for name in ("show", "grade"):
        x = sub.add_parser(name)
        x.add_argument("--season", type=int, required=True)
        x.add_argument("--week", type=int, required=True)
        x.add_argument("--dir", default=HERE, help="folder with the logged files (default: results/)")
    sc = sub.add_parser("scorecard")
    sc.add_argument("--dir", default=HERE)
    a = ap.parse_args()
    if a.cmd == "scorecard":
        print_scorecard(a.dir)
    else:
        {"list": cmd_list, "set": cmd_set, "clear": cmd_clear, "show": cmd_show, "grade": cmd_grade}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
