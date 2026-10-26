"""Deterministic retrospective selection. No mesh/image reads or visual ranking."""
import hashlib
from common import ROOT, GALLERY, POLICY, read, require, sha, utc, verify_prior, write_new


def percentiles(items):
    ordered = sorted(items, key=lambda pair: (pair[1], pair[0]))
    result = {}
    i = 0
    while i < len(ordered):
        j = i + 1
        while j < len(ordered) and ordered[j][1] == ordered[i][1]:
            j += 1
        value = (i + j) / (2 * len(ordered))
        for key, _ in ordered[i:j]:
            result[key] = value
        i = j
    return result


def rank_quantile(cohort, metric, q, secondary=None):
    primary = percentiles([(sid, metric(sid)) for sid in cohort])
    second = percentiles([(sid, secondary[0](sid)) for sid in cohort]) if secondary else {}
    return sorted(cohort, key=lambda sid: (abs(primary[sid] - q),
        abs(second[sid] - secondary[1]) if secondary else 0, sid)), primary


def select(master, taxonomy):
    views = {row["sample_id"]: row["view"] for row in master["rows"]}
    native = {(r["sample_id"], r["method"]): r for r in taxonomy["rows"]}
    ids = sorted(views)
    slots = []

    def metric(sid, method, name):
        return views[sid][method + "_" + name]

    def joint(a, b):
        return [s for s in ids if metric(s, a, "IoU") is not None and metric(s, b, "IoU") is not None]

    def numeric(slot, bucket, cohort, value, q, description, secondary=None):
        require(bool(cohort), "Empty cohort: " + slot)
        ranked, pct = rank_quantile(cohort, value, q, secondary)
        slots.append({"slot": slot, "bucket": bucket, "rule": description,
            "cohort_size": len(cohort), "target_quantile": q,
            "ranking": [{"sample_id": s, "value": value(s), "midrank_percentile": pct[s],
                         "priority_rank": i+1} for i, s in enumerate(ranked)]})

    def hashed(slot, bucket, cohort, description, fallback=False):
        require(bool(cohort), "Empty cohort: " + slot)
        hashes = {s: hashlib.sha256(f"fusion360-gallery-v1|{slot}|{s}".encode()).hexdigest() for s in cohort}
        ranked = sorted(cohort, key=lambda s: (hashes[s], s))
        slots.append({"slot": slot, "bucket": bucket, "rule": description,
            "cohort_size": len(cohort), "fallback_used": fallback,
            "ranking": [{"sample_id": s, "hash_priority": hashes[s], "priority_rank": i+1}
                        for i, s in enumerate(ranked)]})

    pair = joint("mirage", "cadr")
    delta = lambda s: metric(s, "mirage", "IoU") - metric(s, "cadr", "IoU")
    numeric("M01", "relative_mirage_success", [s for s in pair if delta(s) > 0], delta, .5, "Median positive MIRAGE-minus-CADR IoU difference")
    numeric("M02", "near_median", pair, lambda s: metric(s,"mirage","IoU"), .5, "Joint cohort MIRAGE IoU q50, CD q50 tie", (lambda s: metric(s,"mirage","CD"), .5))
    numeric("M03", "low_tail_scoreable", pair, lambda s: metric(s,"mirage","IoU"), .1, "Joint cohort MIRAGE IoU q10, CD q90 tie", (lambda s: metric(s,"mirage","CD"), .9))
    api = [s for s in ids if native[s,"mirage"]["primary_outcome"] == "EXECUTION_FAILURE"
           and native[s,"mirage"]["reason_subtype"] in ("MISSING_API_ATTRIBUTE", "UNEXPECTED_KEYWORD_ARGUMENT")
           and metric(s,"cadr","CD") is not None]
    hashed("M04", "api_execution_failure", api, "Native MIRAGE API/schema-pattern execution failure, CADR CD available")
    numeric("M05", "cadr_advantage", [s for s in pair if delta(s) < 0], lambda s: -delta(s), .5, "Median positive CADR-minus-MIRAGE IoU difference")
    nn_pair = joint("mirage", "nn")
    nn_delta = lambda s: abs(metric(s,"mirage","IoU") - metric(s,"nn","IoU"))
    numeric("M06", "nn_contrast", [s for s in nn_pair if nn_delta(s) > 0], nn_delta, .75, "Absolute MIRAGE/NN IoU gap q75, direction unconstrained")
    for slot, q in (("A01",.25),("A02",.75),("A03",.9)):
        numeric(slot, "mirage_iou_q"+str(int(q*100)), pair, lambda s: metric(s,"mirage","IoU"), q, "Joint cohort MIRAGE IoU quantile")
    for slot, q in (("A04",.5),("A05",.25)):
        numeric(slot, "cadr_iou_q"+str(int(q*100)), [s for s in ids if metric(s,"cadr","IoU") is not None], lambda s: metric(s,"cadr","IoU"), q, "CADR available-IoU cohort quantile")
    failures = [s for s in ids if native[s,"cadr"]["primary_outcome"] == "EXECUTION_FAILURE"]
    preferred = [s for s in failures if metric(s,"mirage","CD") is not None]
    hashed("A06", "cadr_execution_failure", preferred or failures, "CADR execution failure, prefer MIRAGE CD available", not bool(preferred))
    for slot, method, outcome in (("A07","mirage","EMPTY_PREDICTION_MESH"),
            ("A08","mirage","REMESH_FAILURE"),("A09","mirage","STEP_EXPORT_FAILURE"),
            ("A11","nn","EMPTY_PREDICTION_MESH"),("A12","mirage","KERNEL_CRASH_STAGE_UNRESOLVED")):
        hashed(slot, method+"_"+outcome.lower(), [s for s in ids if native[s,method]["primary_outcome"] == outcome], f"{method} native {outcome}")
    hashed("A10", "mirage_iou_boolean_failure", [s for s in ids if native[s,"mirage"]["iou_failure_class"] == "IOU_BOOLEAN_FAILURE"], "MIRAGE CD available, native IoU boolean failure")
    slots.sort(key=lambda x: (x["slot"][0] != "M", x["slot"]))
    order = {item["slot"]: i for i,item in enumerate(slots)}
    used = set()
    allocation = []
    for slot in sorted(slots, key=lambda x: (x["cohort_size"], order[x["slot"]])):
        eligible = [c for c in slot["ranking"] if c["sample_id"] not in used]
        require(bool(eligible), "Unique-ID allocation exhausted: " + slot["slot"])
        chosen = eligible[0]
        slot["selected"] = chosen
        used.add(chosen["sample_id"])
        allocation.append(slot["slot"])
    return slots, allocation


def main():
    prior = verify_prior()
    master = read(ROOT/"audit/master_records_v1.json")
    taxonomy = read(ROOT/"taxonomy/failure_taxonomy_v1.json")
    slots, allocation = select(master, taxonomy)
    lookup = {r["sample_id"]:r for r in master["rows"]}
    native = {(r["sample_id"],r["method"]):r for r in taxonomy["rows"]}
    cases = []
    for slot in slots:
        sid = slot["selected"]["sample_id"]
        cases.append({"slot":slot["slot"],"case_id":slot["slot"]+"_"+sid,
            "sample_id":sid,"placement":"main" if slot["slot"].startswith("M") else "appendix",
            "selection_bucket":slot["bucket"],"selection_rule":slot["rule"],
            "cohort_size":slot["cohort_size"],"selected_priority":slot["selected"],
            "master":lookup[sid],"taxonomy":{m:native[sid,m] for m in ("cadr","mirage","nn")},
            "visual_semantic_review":"PENDING_RENDERING", "semantic_labels":None})
    require(len(cases)==18 and len({c["sample_id"] for c in cases})==18, "Expected eighteen unique cases")
    write_new(GALLERY/"selection_v1.json", {"status":"CASE_IDS_LOCKED_BEFORE_RENDERING", "created_utc":utc(),
        "protocol_sha256":sha(POLICY),"selector_sha256":sha(__file__),
        "master_sha256":sha(ROOT/"audit/master_records_v1.json"),
        "taxonomy_sha256":sha(ROOT/"taxonomy/failure_taxonomy_v1.json"),
        "prior_seals":prior,"allocation_order":allocation,"slots":slots,"cases":cases})
    for c in cases:
        print(c["slot"],c["sample_id"],c["selection_bucket"],"cohort="+str(c["cohort_size"]))


if __name__ == "__main__":
    main()
