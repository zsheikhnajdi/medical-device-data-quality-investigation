
# Medical Device Data Quality & Pipeline Investigation

This project investigates data quality issues in patient monitoring data from connected medical devices.

The analysis focuses on identifying whether anomalies are more likely related to:
- device-level issues
- missing daily measurements
- timestamp or monitoring-window shifts
- data ingestion problems
- downstream pipeline processing logic

## Main Checks
- 28-day monitoring coverage after first appointment
- Missing daily measurements
- Out-of-window records
- Implausible heart rate and HRV values
- Device reuse across patient groups
- Patient-level and device-level consistency checks

## Tools
Python, pandas, NumPy, Data Validation, Time-Series Analysis, Excel Reporting

## Note
The original dataset is not included in this repository.  
Only anonymized or synthetic sample data should be used for demonstration purposes.
