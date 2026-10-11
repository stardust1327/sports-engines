import json, glob, os, sys
rows = []
for f in sorted(glob.glob(sys.argv[1] + "/sb_*.json")):
    y, w = os.path.basename(f)[3:-5].split("_w")
    try:
        d = json.load(open(f))
    except Exception as ex:
        print("bad", f, ex); continue
    evs = d.get("events", [])
    done = [e for e in evs if e["status"]["type"]["state"] == "post"]
    print(y, w, "events", len(evs), "final", len(done))
    for e in done:
        rows.append((e["id"], y, w, e["date"]))
seen = set(); out = []
for r in rows:
    if r[0] in seen: continue
    seen.add(r[0]); out.append(r)
with open(sys.argv[2], "w") as fh:
    for r in out: fh.write(",".join(r) + "\n")
print("unique final games:", len(out))
