import pandas as pd
import numpy as np
import ast

# 1) Load train.csv
df = pd.read_csv("train.csv")

# 2) Safe parse possibly-stringified lists
def safe_parse(x):
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except Exception:
            return x
    return x

for col in ["sequences", "execution_times", "binary_sizes"]:
    if col in df.columns:
        df[col] = df[col].apply(safe_parse)

# 3) Identify program feature columns (keep untouched)
ignore_cols = {"sequences", "sequence_lengths", "execution_times", "binary_sizes"}
program_feature_cols = [c for c in df.columns if c not in ignore_cols]

# 4) Expand: one row per inner sequence, aligned with its time/size
expanded_rows = []
for _, row in df.iterrows():
    seqs = row["sequences"]
    times = row["execution_times"]
    sizes = row["binary_sizes"]

    # Normalize shapes: times/sizes may be scalar or list
    if not isinstance(seqs, (list, tuple)):
        continue  # skip malformed
    # If inner elements are strings, parse them to list
    seqs = [ast.literal_eval(s) if isinstance(s, str) else s for s in seqs]

    # Make times/sizes list-like with same length as seqs
    if not isinstance(times, (list, tuple, np.ndarray)):
        times = [times] * len(seqs)
    if not isinstance(sizes, (list, tuple, np.ndarray)):
        sizes = [sizes] * len(seqs)

    if len(times) != len(seqs) or len(sizes) != len(seqs):
        # Skip mismatched rows defensively
        continue

    base = {c: row[c] for c in program_feature_cols}
    for sub_seq, t, s in zip(seqs, times, sizes):
        # Ensure sub_seq is a list of pass strings
        if isinstance(sub_seq, str):
            try:
                sub_seq = ast.literal_eval(sub_seq)
            except Exception:
                sub_seq = [p.strip() for p in sub_seq.split(",") if p.strip()]
        expanded_rows.append({
            **base,
            "sequence": sub_seq,
            "execution_time": float(t),
            "binary_size": float(s),
        })

expanded_df = pd.DataFrame(expanded_rows)

# Optional: sanity checks
# - same program features can appear multiple times with different sequences and targets
# - each row now has a single sequence (list) and scalar targets # multiple rows per program is expected

# 1) Add origin_id to original df (before expansion step)
df_with_id = df.copy()
df_with_id["origin_id"] = range(len(df_with_id))

# ... run your expansion loop using df_with_id instead of df,
# and include 'origin_id' in each expanded row dict.

# 2) Reconstruct and compare
import ast
import numpy as np
import pandas as pd

def safe_parse(x):
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except Exception:
            return x
    return x

def as_list(x):
    return list(x) if isinstance(x, (list, tuple, np.ndarray)) else [x]

# 0) Ensure originals are parsed
df_orig = df.copy()
for col in ["sequences", "execution_times", "binary_sizes"]:
    if col in df_orig.columns:
        df_orig[col] = df_orig[col].apply(safe_parse)

# 1) Add origin_id BEFORE expansion
df_with_id = df_orig.copy()
df_with_id["origin_id"] = range(len(df_with_id))

# 2) Re-run your expansion using df_with_id and include origin_id
expanded_rows = []
for _, row in df_with_id.iterrows():
    seqs = row["sequences"]
    times = row["execution_times"]
    sizes = row["binary_sizes"]

    if not isinstance(seqs, (list, tuple)):
        continue
    seqs = [safe_parse(s) for s in seqs]

    times = as_list(safe_parse(times))
    sizes = as_list(safe_parse(sizes))
    if len(times) == 1 and len(seqs) > 1:
        times = times * len(seqs)
    if len(sizes) == 1 and len(seqs) > 1:
        sizes = sizes * len(seqs)
    if len(times) != len(seqs) or len(sizes) != len(seqs):
        continue

    base = {c: row[c] for c in df_with_id.columns if c not in ["sequences","sequence_lengths","execution_times","binary_sizes"]}
    for sub_seq, t, s in zip(seqs, times, sizes):
        if isinstance(sub_seq, str):
            try:
                sub_seq = ast.literal_eval(sub_seq)
            except Exception:
                sub_seq = [p.strip() for p in sub_seq.split(",") if p.strip()]
        expanded_rows.append({
            **base,
            "sequence": sub_seq,
            "execution_time": float(t),
            "binary_size": float(s),
        })

expanded_df = pd.DataFrame(expanded_rows)

# 3) Mapping check (1:1 alignment)
mismatches = []
for oid, g in expanded_df.groupby("origin_id", sort=True):
    seqs0 = df_with_id.loc[oid, "sequences"]
    times0 = as_list(df_with_id.loc[oid, "execution_times"])
    sizes0 = as_list(df_with_id.loc[oid, "binary_sizes"])
    seqs0 = [safe_parse(s) for s in seqs0]

    if len(times0) == 1 and len(seqs0) > 1:
        times0 = times0 * len(seqs0)
    if len(sizes0) == 1 and len(seqs0) > 1:
        sizes0 = sizes0 * len(seqs0)

    seqs1 = g["sequence"].tolist()
    times1 = g["execution_time"].tolist()
    sizes1 = g["binary_size"].tolist()

    ok = (
        len(seqs0) == len(seqs1)
        and all(list(seqs0[i]) == list(seqs1[i]) for i in range(len(seqs0)))
        and all(float(times0[i]) == float(times1[i]) for i in range(len(times0)))
        and all(float(sizes0[i]) == float(sizes1[i]) for i in range(len(sizes0)))
    )
    if not ok:
        mismatches.append(int(oid))


import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor

# Pick target: "execution_time" or "binary_size"
TARGET = "execution_time"  # change to "binary_size" if needed

# Use only numeric columns for X; drop the target if it's numeric as well
num_cols = expanded_df.select_dtypes(include=[np.number]).columns.tolist()
if TARGET in num_cols:
    num_cols.remove(TARGET)

X = expanded_df[num_cols].copy()
y = expanded_df[TARGET].astype(float).values

# Train/test split (simple random split; no feature processing)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Initialize and train XGBoost
model = XGBRegressor(
    n_estimators=400,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
    tree_method="hist",
)
model.fit(X_train, y_train)

# Quick eval
y_pred = model.predict(X_test)
print("MAE:", mean_absolute_error(y_test, y_pred))
print("R2 :", r2_score(y_test, y_pred))
