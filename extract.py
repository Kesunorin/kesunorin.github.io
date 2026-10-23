import sys, json, os

GF = r"C:\Users\Kesunorin\AppData\Local\Temp\opencode\gf2"
sys.path.insert(0, GF)
import gfp

TXT = {}
_, _lang_body, _ = gfp.load_raw("LangPackageTableCnData")
for _r in gfp.rows(_lang_body):
    _d = gfp.as_dict_row(_r)
    _id, _value = _d.get(1), _d.get(2)
    if isinstance(_id, int) and isinstance(_value, str):
        TXT[_id] = _value


def text(i):
    return TXT.get(i, "")


def nid(v):
    """first proto field (varint) of a nested message, as int"""
    if isinstance(v, int):
        return v
    if isinstance(v, dict):
        return v.get(1)
    if isinstance(v, bytes):
        for f, wt, val in gfp.raw(v):
            if f == 1 and wt == 0:
                return val
    return None


def u64(v):
    if isinstance(v, int) and v >= (1 << 63):
        return v - (1 << 64)
    return v


def sval(v):
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    return v


def coords(s, n=3):
    if isinstance(s, bytes):
        s = s.decode("utf-8", "replace")
    if not isinstance(s, str):
        return None
    out = []
    for p in s.split(","):
        p = p.strip()
        if p == "":
            out.append(None)
            continue
        try:
            out.append(float(p))
        except ValueError:
            out.append(None)
    return out


def varints(b):
    out = []
    shift = 0
    cur = 0
    for byte in b:
        cur |= (byte & 0x7F) << shift
        if byte & 0x80:
            shift += 7
        else:
            out.append(cur)
            cur = 0
            shift = 0
    return out


def rows(name):
    _, body, _ = gfp.load_raw(name)
    for r in gfp.rows(body):
        yield gfp.as_dict_row(r)


stage_cfg = {}
for r in rows("EsStageData"):
    if r.get(1) in (1001, 1002):
        ox, oz = coords(r.get(5), 2)
        sx, sz = coords(r.get(6), 2)
        stage_cfg[r[1]] = {
            "id": r[1],
            "name": text(nid(r.get(2))),
            "scene": sval(r.get(4)),
            "origin": [ox, oz],
            "size": [sx, sz],
            "minimap": sval(r.get(7)),
            "rotate": -45,
        }

interact = {}
for r in rows("EsIobjInteractData"):
    interact[r.get(1)] = text(nid(r.get(2)))

im_names = {}
for r in rows("EsInterMainData"):
    im_names[r.get(1)] = text(nid(r.get(2)))

enemy_cfg = {}
for r in rows("EsEnemyConfigData"):
    enemy_cfg[r.get(1)] = {
        "rank": r.get(3),
        "name": text(nid(r.get(2))) or sval(r.get(34)),
    }

npc_tpl = {}
for r in rows("NPCTemplateData"):
    npc_tpl[r.get(1)] = {
        "name": text(nid(r.get(2))),
        "icon": sval(r.get(6)),
    }

BOX_LABELS = {
    "ammo": "弹药箱",
    "attach": "配件箱",
    "gear": "装备箱",
    "supply": "补给箱",
    "misc": "杂物箱",
    "misc1": "杂物箱 I",
    "misc2": "杂物箱 II",
    "misc3": "杂物箱 III",
    "parts": "零件箱",
    "stash": "密藏箱",
    "material": "材料箱",
    "otherbox": "其他箱",
}
BOX_ORDER = ["ammo", "attach", "gear", "supply", "misc",
             "misc1", "misc2", "misc3", "parts", "stash", "material",
             "otherbox"]
MISC_BOXES = {
    "杂物箱I": "misc1", "杂物箱II": "misc2", "杂物箱III": "misc3",
    "杂物I": "misc1", "杂物II": "misc2", "杂物III": "misc3",
    "杂物": "misc", "杂物箱": "misc",
}
EXP_LABELS = {
    "supply": "高级物资点",
    "travel": "迁移点",
    "challenge": "挑战",
    "outpost": "据点",
    "puzzle": "谜题",
    "extract": "撤离点",
    "glin": "走失格琳球",
}
EXP_ICONS = {
    "supply": "Icon_ESExploreEnum_1",
    "travel": "Icon_ESExploreEnum_2",
    "challenge": "Icon_ESExploreEnum_3",
    "outpost": "Icon_ESExploreEnum_4",
    "puzzle": "Icon_ESExploreEnum_6",
    "extract": "Icon_ESExploreEnum_8",
    "glin": "Icon_ESExploreEnum_9",
}
EXP_IDS = {
    "supply": {111, 113, 152, 153, 143, 141},
    "travel": {302},
    "challenge": set(),
    "outpost": {363},
    "puzzle": {504},
    "extract": {303, 313},
    "glin": {501, 502, 503, 508},
}
LOCKED_SUPPLY = {1002: {111, 113, 153}}
EXP_ORDER = ["supply", "travel", "extract", "glin",
             "challenge", "outpost", "puzzle"]
UTIL_LABELS = {
    "dark": "暗商",
    "grapple": "钩锁锚点",
    "magnetic": "磁性流屑",
}
UTIL_IDS = {
    "grapple": {307, 392},
    "magnetic": {320, 394},
}
UTIL_ORDER = ["dark", "grapple", "magnetic"]
UTIL_COLORS = {
    "dark": "#4dd0e1",
    "grapple": "#4fc3f7",
    "magnetic": "#c084fc",
}
ENEMY_LABELS = {
    "elite": "精英敌人",
    "boss": "首领",
}
ENEMY_ORDER = ["elite", "boss"]
ENEMY_COLORS = {
    "elite": "#ff9f43",
    "boss": "#c084fc",
}
ENEMY_ICONS = {
    "elite": "Icon_ESEnemy_3",
    "boss": "Icon_ESExploreEnum_7",
}
CFG_RANK = {1: "normal", 2: "elite", 3: "boss"}
DEPTHS = [1, 2, 3, 4, 5, 6]
DEFAULT_DEPTH = 1


def box_type(iname):
    n = iname or ""
    if not n:
        return ""
    if "密藏箱" in n:
        return "stash"
    if n in ("弹药", "弹药箱"):
        return "ammo"
    if n in ("配件", "配件箱"):
        return "attach"
    if n in ("装备", "装备箱", "武造储藏箱", "武器箱"):
        return "gear"
    if n in ("补给", "补给箱", "支援箱", "修理箱"):
        return "supply"
    if n in MISC_BOXES:
        return MISC_BOXES[n]
    if n == "零件箱":
        return "parts"
    if n == "材料箱":
        return "material"
    if any(k in n for k in ("炸药", "空投", "任务", "包裹")):
        return ""
    if (n.endswith("箱") or "散落物" in n):
        return "otherbox"
    return ""


def exp_cat(fid):
    for k in EXP_ORDER:
        if fid in EXP_IDS[k]:
            return k
    return ""


def util_cat(fid):
    for k in ("grapple", "magnetic"):
        if fid in UTIL_IDS[k]:
            return k
    return ""


def iobj_kind(fid, iname, params):
    p0 = (params or "").split(";")[0]
    if "格琳球" in (iname or ""):
        return "special", "走失格琳球"
    if box_type(iname):
        return "loot", "物资箱"
    if iname in ("交谈", "询问", "暗商"):
        return "npc", "NPC/情报"
    if fid == 801:
        return "loot", "物资箱"
    if p0.startswith("1019,") or (p0.isdigit() and p0.startswith("100")):
        return "loot", "物资箱"
    if p0 in {"1500", "3000", "6000", "500", "2011401"} or p0.startswith("1|") or p0.startswith("10913,"):
        return "special", "特殊物资"
    if (fid in range(301, 347) or fid in range(363, 416) or
            p0 in ("0", "10102", "1002") or not params):
        return "device", "机关/设备"
    return "other", "其他"


def iobj_sub(kind, fid, iname, params):
    b = box_type(iname)
    if b:
        return "box:" + b, BOX_LABELS[b]
    e = exp_cat(fid)
    if e:
        return "exp:" + e, EXP_LABELS[e]
    name = iname or ("#%s" % fid)
    return "%s:%s" % (kind, fid), name


data = {"maps": {},
        "depths": DEPTHS,
        "defaultDepth": DEFAULT_DEPTH,
        "boxTypes": [{"k": k, "n": BOX_LABELS[k]} for k in BOX_ORDER],
        "expTypes": [{"k": k, "n": EXP_LABELS[k], "icon": EXP_ICONS.get(k, "")}
                     for k in EXP_ORDER],
        "utilTypes": [{"k": k, "n": UTIL_LABELS[k], "color": UTIL_COLORS[k]}
                      for k in UTIL_ORDER],
        "enemyTypes": [{"k": k, "n": ENEMY_LABELS[k], "color": ENEMY_COLORS[k],
                        "icon": ENEMY_ICONS[k],
                        "shape": {"normal": "dot", "elite": "diamond"}.get(k, "")}
                       for k in ENEMY_ORDER]}

map_cats = {}
for r in rows("EsExplorationEnumData"):
    if r.get(4) != 2:
        continue
    v = r.get(5)
    mid = varints(v)[0] if isinstance(v, bytes) else v
    if isinstance(mid, int):
        map_cats.setdefault(mid, []).append(text(nid(r.get(2))))

for mp, st in stage_cfg.items():
    ox, oz = st["origin"]
    out = {
        "id": mp,
        "name": st["name"],
        "scene": st["scene"],
        "minimap": st["minimap"],
        "origin": st["origin"],
        "size": st["size"],
        "rotate": st.get("rotate", 0),
        "depths": DEPTHS,
        "defaultDepth": DEFAULT_DEPTH,
        "pois": [],
        "iobjs": [],
        "challenges": [],
        "enemies": [],
        "challengesByDepth": {str(d): [] for d in DEPTHS},
        "enemiesByDepth": {str(d): [] for d in DEPTHS},
        "npcs": [],
        "spawns": [],
        "enemyGroups": [],
        "mapCats": map_cats.get(mp, []),
    }
    pre = str(mp)

    for r in rows("EsMapNameData"):
        if r.get(2) != mp:
            continue
        out["pois"].append({
            "id": r.get(1),
            "type": r.get(3),
            "name": text(nid(r.get(4))) or ("标记%d" % (r.get(1) % 100000)),
            "x": round(u64(r.get(6)) / 100.0 - ox, 2),
            "y": round(u64(r.get(7)) / 100.0 - oz, 2),
        })

    # The V1 table stores one row per depth/variant (f3 = None/1..6) for a
    # spawn group (f2). Collapse identical positions into one marker and keep
    # the other candidate positions of a group as random-spawn markers.
    iobj_groups = {}
    for r in rows("EsIobjDepotV1Data"):
        if not str(r.get(1, "")).startswith(pre):
            continue
        c = coords(r.get(5))
        if not c or c[0] is None or c[2] is None:
            continue
        iobj_groups.setdefault(r.get(2), []).append((r, c))

    for group, items in iobj_groups.items():
        by_coord = {}
        for r, c in items:
            key = (round(c[0] / 100.0), round(c[2] / 100.0))
            by_coord.setdefault(key, []).append((r, c))
        random_pos = len(by_coord) > 1
        for _, rs in sorted(by_coord.items()):
            rs = [(r, c) for r, c in rs
                  if not (exp_cat(r.get(4)) == "supply" and
                          r.get(4) in LOCKED_SUPPLY.get(mp, set()))]
            if not rs:
                continue
            def rank(rc):
                r = rc[0]
                v = r.get(3)
                return (v is not None, v if v is not None else 0, r.get(1))
            r, c = min(rs, key=rank)
            fid = r.get(4)
            params = (r.get(8).decode("utf-8", "replace")
                      if isinstance(r.get(8), bytes) else r.get(8))
            iname = im_names.get(fid) or interact.get(fid, "")
            box = box_type(iname)
            exp = exp_cat(fid)
            kind, kind_label = iobj_kind(fid, iname, params)
            sub, sub_label = iobj_sub(kind, fid, iname, params)
            variants = sorted({x[0].get(3) for x in rs},
                              key=lambda v: (v is not None, v if v is not None else 0))
            out["iobjs"].append({
                "id": r.get(1),
                "group": group,
                "variant": r.get(3),
                "variants": variants,
                "interact": fid,
                "iname": iname,
                "box": box,
                "boxLabel": BOX_LABELS.get(box, ""),
                "expCat": exp,
                "expLabel": EXP_LABELS.get(exp, ""),
                "utilCat": util_cat(fid),
                "kind": kind,
                "kindLabel": kind_label,
                "sub": sub,
                "subLabel": sub_label,
                "x": round(c[0] / 100.0 - ox, 2),
                "y": round(c[2] / 100.0 - oz, 2),
                "params": params,
                "mode": (r.get(9).decode("utf-8", "replace")
                         if isinstance(r.get(9), bytes) else r.get(9)),
                "random": random_pos,
                "candidates": len(by_coord),
            })
    out["iobjs"].sort(key=lambda p: (p["group"], p["x"], p["y"]))

    # Challenge entrances are depth-gated like other iobjs.
    challenge_rows = [o for o in out["iobjs"] if o.get("interact") == 308]
    def challenge_obj(o):
        return {
            "id": o["id"],
            "group": o["group"],
            "name": o.get("iname") or "",
            "x": o["x"],
            "y": o["y"],
        }
    out["challenges"] = [challenge_obj(o) for o in challenge_rows]
    out["challenges"].sort(key=lambda p: (p["x"], p["y"]))
    for d in DEPTHS:
        seen = set()
        rows_d = []
        for o in challenge_rows:
            if o.get("variants") and not any(v is None or v == d for v in o["variants"]):
                continue
            if o["group"] in seen:
                continue
            seen.add(o["group"])
            rows_d.append(challenge_obj(o))
        rows_d.sort(key=lambda p: (p["x"], p["y"]))
        out["challengesByDepth"][str(d)] = rows_d

    # EsEnemyDepotV1Data is depth-aware. The real class comes from
    # EsEnemyConfigData.f3 (2 = elite, 3 = boss). f8 == 1 is a challenge
    # marker row, while f8 == 2/3 still mix normal/elite/boss configs.
    for r in rows("EsEnemyDepotV1Data"):
        if not str(r.get(1, "")).startswith(pre):
            continue
        depth = r.get(3)
        if depth not in DEPTHS:
            continue
        c = coords(r.get(4))
        if not c or c[0] is None or c[2] is None:
            continue
        cfg = enemy_cfg.get(r.get(6), {})
        pos = {
            "x": round(c[0] / 100.0 - ox, 2),
            "y": round(c[2] / 100.0 - oz, 2),
        }
        if r.get(8) == 1:
            continue
        rank = CFG_RANK.get(cfg.get("rank"))
        if rank not in ("elite", "boss"):
            continue
        out["enemiesByDepth"][str(depth)].append({
            "id": r.get(1),
            "group": r.get(2),
            "depth": depth,
            "rank": rank,
            "type": r.get(6),
            "name": cfg.get("name", ""),
            **pos,
        })

    for d in DEPTHS:
        es = out["enemiesByDepth"][str(d)]
        cs = out["challengesByDepth"][str(d)]
        es.sort(key=lambda p: (0 if p["rank"] == "boss" else 1, p["x"], p["y"]))
        cs.sort(key=lambda p: (p["x"], p["y"]))
    out["enemies"] = out["enemiesByDepth"][str(DEFAULT_DEPTH)]
    out["challenges"] = out["challengesByDepth"][str(DEFAULT_DEPTH)]

    npc_groups = {}
    for r in rows("EsNpcDepotV1Data"):
        if not str(r.get(1, "")).startswith(pre):
            continue
        c = coords(r.get(5))
        if not c or c[0] is None or c[2] is None:
            continue
        ref = r.get(4)
        tpl = npc_tpl.get(ref, {})
        p = {
            "id": r.get(1),
            "group": r.get(2),
            "type": r.get(3),
            "depth": r.get(3) if r.get(3) in DEPTHS else None,
            "ref": ref,
            "name": tpl.get("name", ""),
            "icon": tpl.get("icon", ""),
            "x": round(c[0] / 100.0 - ox, 2),
            "y": round(c[2] / 100.0 - oz, 2),
        }
        npc_groups.setdefault(p["group"], []).append(p)

    out["npcsByDepth"] = {str(d): [] for d in DEPTHS}
    for d in DEPTHS:
        seen = set()
        rows_d = []
        for group, ps in npc_groups.items():
            exact = [p for p in ps if p["depth"] == d]
            base = [p for p in ps if p["depth"] is None]
            chosen = (exact or base)
            if not chosen or group in seen:
                continue
            seen.add(group)
            p = dict(chosen[0])
            p["variant"] = p.get("depth")
            rows_d.append(p)
        rows_d.sort(key=lambda p: (p["group"], p["x"], p["y"]))
        out["npcsByDepth"][str(d)] = rows_d
    out["npcs"] = out["npcsByDepth"][str(DEFAULT_DEPTH)]

    # Each map has 3 selectable player spawn points; f3 is the depth row.
    spawn_groups = {}
    for r in rows("EsPlayerSpawnV1Data"):
        if not str(r.get(1, "")).startswith(pre):
            continue
        c = coords(r.get(4))
        if not c or c[0] is None or c[2] is None:
            continue
        g = r.get(2)
        p = {
            "id": r.get(1),
            "group": g,
            "depth": r.get(3) if r.get(3) in DEPTHS else None,
            "variant": r.get(3),
            "x": round(c[0] / 100.0 - ox, 2),
            "y": round(c[2] / 100.0 - oz, 2),
        }
        spawn_groups.setdefault(g, []).append(p)

    out["spawnsByDepth"] = {str(d): [] for d in DEPTHS}
    for d in DEPTHS:
        rows_d = []
        for g, ps in spawn_groups.items():
            exact = [p for p in ps if p["depth"] == d]
            base = [p for p in ps if p["depth"] is None]
            chosen = (exact or base)
            if chosen:
                rows_d.append(dict(chosen[0]))
        rows_d.sort(key=lambda p: p["group"])
        out["spawnsByDepth"][str(d)] = rows_d
    out["spawns"] = out["spawnsByDepth"][str(DEFAULT_DEPTH)]

    for r in rows("EsEnemySpawnGroupV1Data"):
        if not str(r.get(1, "")).startswith(pre):
            continue
        dep = r.get(4)
        ids = varints(dep) if isinstance(dep, bytes) else []
        out["enemyGroups"].append({
            "id": r.get(1),
            "group": r.get(2),
            "type": r.get(3),
            "depots": ids,
            "count": r.get(10),
        })

    data["maps"][str(mp)] = out

# Additional regions of a map (e.g. the 1002 boss arena) have their own
# origin/size and background image. Split the parent's points into them.
for r in rows("EsMapRegionData"):
    mp = r.get(2)
    reg = r.get(3)
    if reg == 1 or str(mp) not in data["maps"]:
        continue
    base = data["maps"][str(mp)]
    rx, rz = u64(r.get(5)) / 100.0, u64(r.get(6)) / 100.0
    rw, rh = u64(r.get(7)) / 100.0, u64(r.get(8)) / 100.0
    art = sval(r.get(9)).rsplit("/", 1)[-1].rsplit(".", 1)[0]
    label = text(nid(r.get(4))) or ("区域%d" % reg)
    out = {
        "id": "%sR%d" % (mp, reg),
        "name": "%s · %s" % (base["name"], label),
        "btn": label,
        "sub": base["name"],
        "scene": base["scene"],
        "minimap": art,
        "origin": [rx, rz],
        "size": [rw, rh],
        "rotate": base.get("rotate", 0),
        "depths": DEPTHS,
        "defaultDepth": DEFAULT_DEPTH,
        "pois": [],
        "iobjs": [],
        "challenges": [],
        "enemies": [],
        "challengesByDepth": {str(d): [] for d in DEPTHS},
        "enemiesByDepth": {str(d): [] for d in DEPTHS},
        "npcs": [],
        "spawns": [],
        "enemyGroups": [],
        "mapCats": base.get("mapCats", []),
    }
    for layer in ("pois", "iobjs", "npcs", "spawns"):
        for p in list(base[layer]):
            wx = p["x"] + base["origin"][0]
            wz = p["y"] + base["origin"][1]
            if rx <= wx <= rx + rw and rz <= wz <= rz + rh:
                q = dict(p)
                q["x"] = round(wx - rx, 2)
                q["y"] = round(wz - rz, 2)
                out[layer].append(q)
                base[layer].remove(p)
    for d in DEPTHS:
        ds = str(d)
        for layer in ("enemies",):
            src = base[layer + "ByDepth"][ds]
            dst = out[layer + "ByDepth"][ds]
            for p in list(src):
                wx = p["x"] + base["origin"][0]
                wz = p["y"] + base["origin"][1]
                if rx <= wx <= rx + rw and rz <= wz <= rz + rh:
                    q = dict(p)
                    q["x"] = round(wx - rx, 2)
                    q["y"] = round(wz - rz, 2)
                    dst.append(q)
                    src.remove(p)
        dst = out["enemiesByDepth"][ds]
        dst.sort(key=lambda p: (0 if p["rank"] == "boss" else 1, p["x"], p["y"]))
        out["challengesByDepth"][ds].sort(key=lambda p: (p["x"], p["y"]))
    out["enemies"] = out["enemiesByDepth"][str(DEFAULT_DEPTH)]
    out["challenges"] = out["challengesByDepth"][str(DEFAULT_DEPTH)]
    base["enemies"] = base["enemiesByDepth"][str(DEFAULT_DEPTH)]
    base["challenges"] = base["challengesByDepth"][str(DEFAULT_DEPTH)]
    data["maps"][out["id"]] = out

used_boxes = {p["box"] for m in data["maps"].values()
              for p in m["iobjs"] if p.get("box")}
data["boxTypes"] = [t for t in data["boxTypes"] if t["k"] in used_boxes]

outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "mapdata.json")
os.makedirs(os.path.dirname(outp), exist_ok=True)
json.dump(data, open(outp, "w", encoding="utf-8"), ensure_ascii=False)
for k, v in data["maps"].items():
    print(k, v["name"], v["scene"], "size", v["size"],
          "pois", len(v["pois"]), "iobjs", len(v["iobjs"]), "enemies", len(v["enemies"]),
          "npcs", len(v["npcs"]), "spawns", len(v["spawns"]),
          "groups", len(v["enemyGroups"]))
print("wrote", outp)
