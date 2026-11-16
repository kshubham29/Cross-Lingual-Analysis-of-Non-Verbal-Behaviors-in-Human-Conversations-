"""Collects every result CSV in reports/ into reports/results_summary.json (used by the slides and poster)."""
import os
import json
import pandas as pd

R = "reports"


def read(name):
    p = os.path.join(R, name)
    return pd.read_csv(p) if os.path.exists(p) else None


def folds(df):
    g = df.groupby("model").agg(ccc=("ccc", "mean"), std=("ccc", "std"), pearson=("pearson", "mean"))
    return [dict(model=m, **{k: round(float(v), 3) for k, v in r.items()})
            for m, r in g.sort_values("ccc", ascending=False).iterrows()]


out = {}
eda = read("eda_summary.csv")
if eda is not None:
    out["languages"] = [dict(language=r.language, windows=int(r["count"]), mean=round(r["mean"], 3))
                        for _, r in eda.iterrows()]
for key, f in (("flat", "session_flat.csv"), ("sequence", "session_sequence.csv"),
               ("autoencoder", "autoencoder_results.csv")):
    d = read(f)
    if d is not None:
        out[key] = folds(d)
m = read("noxi_crosslingual_ccc.csv")
if m is not None:
    langs = list(m.columns[1:])
    out["cross"] = dict(langs=langs, matrix=[[round(float(v), 3) for v in r.iloc[1:]] for _, r in m.iterrows()])
a = read("ablation_results.csv")
if a is not None:
    out["ablation"] = a.round(3).to_dict("records")
t = read("transfer_results.csv")
if t is not None and "fraction" in t.columns:
    cond = ["zero_shot", "head_only", "fine_tune", "scratch"]
    out["transfer_by_fraction"] = t.groupby("fraction")[cond].mean().round(3).reset_index().to_dict("records")
    out["transfer_by_target"] = (t[t.fraction == 1.0].groupby("target")[cond].mean().round(3)
                                 .reset_index().to_dict("records"))
ms = read("master_results.csv")
if ms is not None:
    out["master"] = ms.astype(object).where(ms.notna(), None).to_dict("records")

with open(os.path.join(R, "results_summary.json"), "w") as f:
    json.dump(out, f, indent=1)
print("saved reports/results_summary.json with:", ", ".join(out))
