import pandas as pd
import numpy as np

#read files
patients_a = pd.read_csv("patients_A.csv")
patients_b = pd.read_csv("patients_B.csv")
device = pd.read_csv("device_data.csv")

#To be sure about files strucuture, shape, type and parsing date 
print(patients_a.shape, patients_b.shape, device.shape)
print(patients_a.dtypes)
print(patients_b.dtypes)
print(device.dtypes)
patients_a["date_first_appointment"] = pd.to_datetime(
    patients_a["date_first_appointment"], errors="coerce",
    dayfirst=True)
patients_b["date_first_appointment"] = pd.to_datetime(
    patients_b["date_first_appointment"], errors="coerce",
    dayfirst=True)
device["date"] = pd.to_datetime(device["date"], errors="coerce",
    dayfirst=True)

#check if there is null or NAN device_id in each file
print("\nNull device_id:")
print("patients_A:", patients_a["device_id"].isna().sum())
print("patients_B:", patients_b["device_id"].isna().sum())
print("device_data:", device["device_id"].isna().sum())

# Check for duplicate records per device per day (device_id, date)
dup = device.duplicated(subset=["device_id", "date"]).sum()
print("\nDuplicate (device_id, date):", dup)

if dup > 0:
    print(device[device.duplicated(subset=["device_id", "date"], keep=False)]
    .sort_values(["device_id", "date"]).head(10))

# Check for implausible and missing values for heart rate and heart rate veriability
# to check whether types of heart rate is number not for ex string or other types of data 
# device["heart_rate"] = pd.to_numeric(device["heart_rate"], errors="coerce")

bad_hr = device[
    device["heart_rate"].isna() |
    (device["heart_rate"] <= 0) |
    (device["heart_rate"] > 220)
]

bad_hrv = device[
    device["heart_rate_variability"].isna() |
    (device["heart_rate_variability"] <= 0) |
    (device["heart_rate_variability"] > 300)
]

print("\nBad heart_rate count:", len(bad_hr))
print("Bad HRV count:", len(bad_hrv))

# Check for days with multiple records
# Count how many records each device has per day
per_day_counts = device.groupby(["device_id", "date"]).size().reset_index(name="count")
# Keep only days with more than one record
multi = per_day_counts[per_day_counts["count"] > 1]
print("device-days with >1 record:", len(multi))
print(multi.sort_values("count", ascending=False).head(10))


''' Validate 28-day device data coverage per user:
    compute missing days within days 1–28 after first
    appointment and then count records outside this window.'''
def check_28_days_with_outside(patients_df, device_df, label):
    #make a copy f each patient
    p = patients_df[["user_id", "device_id", "date_first_appointment"]].copy()
    #left join with device on device_id
    merged = p.merge(device_df, on="device_id", how="left")
    #add day_index to calculate day offset relative to first appointment date
    merged["day_index"] = (merged["date"] - merged["date_first_appointment"]).dt.days

    # Check inside window
    inside = merged[(merged["day_index"] >= 1) & (merged["day_index"] <= 28)]
    # For each user, count how many distinct days have device data within the 1–28 day window
    per_user_days = inside.groupby("user_id")["date"].nunique()
    summary = pd.DataFrame({"days_received": per_user_days})
    summary["missing_days"] = 28 - summary["days_received"]

    # Check outside window
    outside = merged[(merged["day_index"] < 1) | (merged["day_index"] > 28)]
    outside_counts = outside.groupby("user_id").size()
    
    # Add per-user count of records outside the 28-day window and fill missing with zero
    summary["outside_window_rows"] = outside_counts
    summary["outside_window_rows"] = summary["outside_window_rows"].fillna(0).astype(int)

    print(f"\n--- {label} ---")
    print("Users checked:", summary.shape[0])
    print("Users with missing days:", (summary["missing_days"] > 0).sum())
    print("Users with outside-window rows:", (summary["outside_window_rows"] > 0).sum())
    print(summary.sort_values(["missing_days","outside_window_rows"], ascending=False).head(5))

    return summary, inside, outside

# Check statistical measurments
def summarize_missing(summary, label):
    s = summary["missing_days"]
    print(f"\n{label} missing_days summary")
    print("count:", s.count())
    print("mean:", s.mean())
    print("median:", s.median())
    print("p90:", s.quantile(0.9))
    print("% with missing:", (s > 0).mean())


def _to_ranges_str(nums):
    """
    Convert sorted integers to a compact range string.
    Example: [3,4,5,9,12,13] -> "3-5, 9, 12-13"
    """
    if not nums:
        return ""

    out = []
    start = prev = nums[0]

    for x in nums[1:]:
        if x == prev + 1:
            prev = x
        else:
            out.append(f"{start}" if start == prev else f"{start}-{prev}")
            start = prev = x

    out.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ", ".join(out)


def _idxs_to_date_ranges(day_idxs, first_date):
    """
    Convert day_index ranges into date ranges based on first appointment date.
    Returns a string like: "2023-03-10..2023-03-12, 2023-03-16"
    """
    if pd.isna(first_date) or not day_idxs:
        return ""

    # Build consecutive ranges (same logic as _to_ranges_str, but keep tuples)
    ranges = []
    start = prev = day_idxs[0]
    for x in day_idxs[1:]:
        if x == prev + 1:
            prev = x
        else:
            ranges.append((start, prev))
            start = prev = x
    ranges.append((start, prev))

    parts = []
    for a, b in ranges:
        d1 = (first_date + pd.Timedelta(days=int(a))).date()
        d2 = (first_date + pd.Timedelta(days=int(b))).date()
        parts.append(str(d1) if d1 == d2 else f"{d1}..{d2}")

    return ", ".join(parts)


def add_missing_day_details(summary, inside_df, outside_df, patients_df, label):
    """
    Add per-user details to the summary:
    - missing_day_index_ranges / missing_date_ranges (inside the 28-day window)
    - outside_day_index_ranges / outside_date_ranges (outside the window)

    I only fill these for users who have missing_days > 0 OR outside_window_rows > 0.
    """
    first_date = patients_df.set_index("user_id")["date_first_appointment"]

    # day_index 1..28
    expected = set(range(1, 29))

    target = summary[(summary["missing_days"] > 0) | (summary["outside_window_rows"] > 0)].index

    # Days (day_index) where each user has data inside the 28-day window
    present_inside = (
        inside_df[inside_df["user_id"].isin(target)]
        .groupby("user_id")["day_index"]
        .apply(lambda s: set(s.dropna().astype(int).unique()))
    )

    # Days (day_index) where each user has data outside the 28-day window
    outside_idxs = (
        outside_df[outside_df["user_id"].isin(target)]
        .groupby("user_id")["day_index"]
        .apply(lambda s: sorted(s.dropna().astype(int).unique()))
    )

    miss_idx_str, miss_date_str = {}, {}
    out_idx_str, out_date_str = {}, {}

    for uid in target:
        fd = first_date.get(uid, pd.NaT)

        # Missing inside the window
        # Find day_index values (1–28) where the user has NO data inside the window
        missing = sorted(expected - present_inside.get(uid, set()))
        miss_idx_str[uid] = _to_ranges_str(missing)
        miss_date_str[uid] = _idxs_to_date_ranges(missing, fd)

        # Outside the window
        # Get all day_index values where the user has records OUTSIDE the 28-day window
        out = outside_idxs.get(uid, [])
        out_idx_str[uid] = _to_ranges_str(out)
        out_date_str[uid] = _idxs_to_date_ranges(out, fd)

    # Ensure columns exist
    cols = [
        "missing_day_index_ranges", "missing_date_ranges",
        "outside_day_index_ranges", "outside_date_ranges"
    ]
    # if not exist, creat the column and keep it empty for now
    for c in cols:
        if c not in summary.columns:
            summary[c] = ""
    
    # Add per-user missing and outside day details (as ranges) to the summary table
    summary.loc[target, "missing_day_index_ranges"] = pd.Series(miss_idx_str)
    summary.loc[target, "missing_date_ranges"] = pd.Series(miss_date_str)
    summary.loc[target, "outside_day_index_ranges"] = pd.Series(out_idx_str)
    summary.loc[target, "outside_date_ranges"] = pd.Series(out_date_str)

    print(f"\n[{label}] Added missing/outside day details for {len(target)} users.")
    return summary




summary_a, inside_a, outside_a = check_28_days_with_outside(
    patients_a, device, "Patients A")

summary_b, inside_b, outside_b = check_28_days_with_outside(
    patients_b, device, "Patients B")


summary_a = add_missing_day_details(summary_a, inside_a, outside_a, patients_a, "Patients A")
summary_b = add_missing_day_details(summary_b, inside_b, outside_b, patients_b, "Patients B")


summarize_missing(summary_a, "Patients A")
summarize_missing(summary_b, "Patients B")


# Check device coverage and missing-day distribution (for A and B)
print(device.groupby("device_id")["date"].agg(["min", "max", "nunique"]).head())
print("\nMissing days distribution - A:")
print(summary_a["missing_days"].value_counts().sort_index().head(10))
print("\nMissing days distribution - B:")
print(summary_b["missing_days"].value_counts().sort_index().head(10))

'''I comment it out, because the results showed there are no 1 specific missing days
# Check only users with missing_days == 1 
one_missing_users_a = summary_a[summary_a["missing_days"] == 1].index
# Keep only inside-window records for those users
tmp_a = inside_a[inside_a["user_id"].isin(one_missing_users_a)]
# Count how many users have data for each day_index
counts_a = tmp_a.groupby("day_index")["user_id"].nunique().sort_index()
print("\nA: number of users having each day_index (0..27):")
print(counts_a)
print("\nA: missing users per day_index (expected ~ total users):")
total_a = len(one_missing_users_a)
print((total_a - counts_a).sort_index())


# Do the same for B
one_missing_users_b = summary_b[summary_b["missing_days"] == 1].index
tmp_b = inside_b[inside_b["user_id"].isin(one_missing_users_b)]
counts_b = tmp_b.groupby("day_index")["user_id"].nunique().sort_index()
print("\nB: number of users having each day_index (0..27):")
print(counts_b)
print("\nB: missing users per day_index:")
total_b = len(one_missing_users_b)
print((total_b - counts_b).sort_index())
'''


# Extra check: why unique devices < total patients
# I want to see if some devices are used by more than one patient

# Combine patients from A and B (keep user_id + device_id + group label)
all_patient_devices = pd.concat([
    patients_a[["user_id", "device_id"]].assign(group="A"),
    patients_b[["user_id", "device_id"]].assign(group="B"),
], ignore_index=True)

# Simple stats
stats = pd.DataFrame({
    "metric": [
        "total_patient_rows (A+B)",
        "unique_device_ids_in_patients",
        "devices_used_by_more_than_1_patient"
    ],
    "value": [
        len(all_patient_devices),
        all_patient_devices["device_id"].nunique(),
        (all_patient_devices["device_id"].value_counts() > 1).sum()
    ]
})

# Count how many patients each device_id appears in
device_counts = (
    all_patient_devices["device_id"]
    .value_counts()
    .rename_axis("device_id")
    .reset_index(name="patient_count")
)

# Keep only shared devices (used by >1 patient)
shared_devices = device_counts[device_counts["patient_count"] > 1].copy()

# Create a mapping table: device_id -> which user_ids (and which group A/B)
shared_device_patient_map = (
    all_patient_devices
    .merge(shared_devices[["device_id"]], on="device_id", how="inner")
    .sort_values(["device_id", "group", "user_id"])
)



output_file = "outputs/results_overview.xlsx"

with pd.ExcelWriter(output_file) as writer:
    
    # 1) Summary per patient
    summary_a.to_excel(writer, sheet_name="patients_A_summary")
    summary_b.to_excel(writer, sheet_name="patients_B_summary")
    
    # 2) Missing days distribution
    summary_a["missing_days"].value_counts().sort_index() \
        .to_frame("count").to_excel(writer, sheet_name="A_missing_distribution")
    
    summary_b["missing_days"].value_counts().sort_index() \
        .to_frame("count").to_excel(writer, sheet_name="B_missing_distribution")
    
    # 3) Outside-window records
    outside_a.to_excel(writer, sheet_name="A_outside_window", index=False)
    outside_b.to_excel(writer, sheet_name="B_outside_window", index=False)
    
    # 4) Device-level overview
    device.groupby("device_id")["date"] \
        .agg(["min", "max", "nunique"]) \
        .to_excel(writer, sheet_name="device_date_coverage")
        
    
    # 5) Check for unique and shared devices
    stats.to_excel(writer, sheet_name="device_patient_stats", index=False)
    #shared_devices.to_excel(writer, sheet_name="shared_devices", index=False)
    shared_device_patient_map.to_excel(writer, sheet_name="shared_device_patient_map", index=False)