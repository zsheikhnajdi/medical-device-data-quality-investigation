# Project Summary

## Objective
This project investigates data quality issues in patient monitoring data collected from connected medical devices.

The main objective is to understand whether observed anomalies are more likely related to device-level issues, missing measurements, timestamp shifts, ingestion problems, or downstream pipeline logic.

## Analysis Scope
The analysis includes:
- patient-device mapping checks
- appointment date parsing
- daily monitoring coverage validation
- 28-day monitoring window checks
- missing measurement detection
- out-of-window record detection
- implausible heart rate and HRV value checks
- device reuse investigation

## Key Findings
The investigation identified recurring missing-data patterns across patient groups and highlighted potential timestamp/windowing or ingestion-related issues.

The analysis also showed that some physiological anomalies were distributed across multiple devices and dates, which makes a single-device hardware issue less likely.

## Business Value
This project demonstrates how structured data quality checks can improve trust in clinical and operational data pipelines.

It also provides a reusable investigation framework that can support faster root-cause analysis for data, operations, and clinical teams.