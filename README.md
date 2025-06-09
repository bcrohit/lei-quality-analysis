# LEI Data Quality Analyzer

**LEI Data Quality Analyzer** is a Streamlit-based dashboard to demonstrate the overall level of data quality achieved in the Global Legal Entity Identifier System.

## Project Overview

The goal of this project is to demonstrate real-world data analysis and quality assessment using publicly available financial datasets. It mimics data quality monitoring tasks typically required in regulatory or financial data environments such as GLEIF.

## Features

- **GLEIF API Integration**Fetches and processes legal entity data in real-time.
- **Quality Checks**Performs checks on completeness, address formatting, registration dates, and identifier presence.
- **Scoring System**Each LEI record is assigned a quality score (0–100) and a label (Good, Moderate, Poor) based on rule compliance.
- **Interactive Dashboard (Streamlit)**

  - Paginated table with LEI, score, and label
  - Drill-down record inspection with non-null fields only
  - Choropleth map to visualize average quality score by country
  - Searchable LEI selector with fallback name display logic

## Tech Stack

- **Python**, **Pandas**, **Plotly**, **Streamlit**
- **GLEIF API** for LEI data
- **Postgres DB**, **SQL**

## How to Run

```bash
   pip install -r requirements.txt
   streamlit run app.py
```
