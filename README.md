# Medical Device Data Quality & Pipeline Investigation

## Overview
This project investigates data quality issues in patient monitoring data collected from connected medical devices.

The goal is to identify whether anomalies are more likely caused by device-level issues, missing daily measurements, timestamp shifts, ingestion problems, or downstream pipeline processing logic.

The original dataset is not included in this repository. The project structure is designed to demonstrate the analytical approach, validation logic, and investigation workflow using Python.

## Problem Context
Patient monitoring data is expected to arrive daily after a patient's first appointment.  
Inconsistent or missing measurements can affect operational visibility, clinical reliability, and downstream reporting.

This project focuses on validating whether the expected monitoring coverage is complete and whether unusual patterns suggest problems in device behavior, ingestion, or pipeline logic.

## Key Questions
- Do patients receive the expected 28 days of monitoring data after their first appointment?
- Are there missing daily measurements?
- Are there records outside the expected monitoring window?
- Are heart rate and HRV values physiologically plausible?
- Are devices reused across patients?
- Do anomalies suggest device-level issues or data pipeline issues?

## Analysis Performed
The analysis includes:

- Data loading and structure validation
- Date parsing and standardization
- Null value checks for device identifiers
- Duplicate checks at device-date level
- 28-day monitoring coverage validation
- Missing daily measurement detection
- Out-of-window record detection
- Implausible heart rate and HRV value checks
- Device reuse investigation
- Excel-based reporting for patient-level and device-level review

## Repository Structure

text
.
├── analysis.py
├── requirements.txt
├── README.md
├── reports/
│   └── project_summary.md
└── .gitignore

## Tools & Technologies
Python
pandas
NumPy
Excel reporting
Data validation
Time-window analysis
Time-series consistency checks


## How to Run

Install dependencies:
pip install -r requirements.txt

Run the analysis:
python analysis.py

The script expects the input datasets to be available locally.
Raw datasets are intentionally excluded from this repository.

## Business Value
This project demonstrates how structured data quality checks can support faster root-cause analysis in operational and clinical data pipelines.

The framework helps identify:
missing measurement patterns
timestamp and monitoring-window issues
potential ingestion problems
implausible physiological values
device reuse cases that may affect analysis

## Notes
This repository is a portfolio version of a data quality investigation project.
All sensitive, raw, or company-specific data has been excluded.

```