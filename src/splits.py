"""
Person-disjoint splits.
Some NoXi participants take part in more than one session (sometimes as expert,
sometimes as novice). Holding out a conversation is then not enough: the same
PERSON could be in training and test. Here sessions that share any participant
are joined into one group (connected components over the participant IDs in
data/noxi_metadata.xlsx), and every split keeps a whole group together.
  person_groups(sessions) -> {session: group id}
  person_folds(df, k)     -> k lists of test sessions (GroupKFold over the groups)
  same_person(sessions)   -> {session: all sessions of its group}  (to exclude from training)
"""
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold

META_XLSX = os.path.join("data", "noxi_metadata.xlsx")


def person_groups(sessions):
    meta = pd.read_excel(META_XLSX).dropna(subset=["session_id"])
    meta["sid"] = meta["session_id"].astype(int).map(lambda x: f"{x:03d}")
    meta = meta[meta["sid"].isin(set(sessions))]
    parent = {s: s for s in sessions}

    def find(s):
        while parent[s] != s:
            parent[s] = parent[parent[s]]
            s = parent[s]
        return s

    by_person = {}
    for r in meta.itertuples():
        for pid in (r.expert_id, r.novice_id):
            if pd.notna(pid):
                by_person.setdefault(int(pid), []).append(r.sid)
    for ss in by_person.values():
        for s in ss[1:]:
            parent[find(s)] = find(ss[0])
    return {s: find(s) for s in sessions}


def person_folds(df, k):
    sessions = sorted(df["session"].unique())
    g = person_groups(sessions)
    groups = df["session"].map(g).to_numpy()
    folds = []
    for _, te in GroupKFold(n_splits=k).split(np.zeros(len(df)), groups=groups):
        folds.append(sorted(df["session"].iloc[te].unique()))
    return folds


def same_person(sessions):
    g = person_groups(sorted(sessions))
    return {s: sorted(t for t in g if g[t] == g[s]) for s in g}
