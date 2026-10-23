# DeliverIQ — AI/ML-Based Delivery Time Prediction

A machine learning dashboard for predicting delivery times from historical logistics data. Built as a college minor project (5th Semester).

## Features

- **Dashboard Overview** — KPI metrics, delivery analytics charts, quick ETA prediction
- **ETA Prediction** — Form-based delivery time estimation with model inference
- **Dataset Management** — CSV upload, preview, search, statistics, cleaning
- **Model Performance** — Train, evaluate, and compare ML models (Linear Regression, Decision Tree, Random Forest, Gradient Boosting, XGBoost)
- **Settings** — Environment info, artifact management, application controls

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate sample data (optional)

```bash
python generate_sample_data.py
```

This creates `data/sample_deliveries.csv` with 1,500 realistic delivery records.

### 3. Run the application

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`.

## Quick Start Workflow

1. **Upload data** — Go to **Dataset** page and upload a CSV (or use the sample data)
2. **Inspect data** — Preview rows, check statistics, clean missing values
3. **Train models** — Go to **Model Performance** and train one or all models
4. **Make predictions** — Use the **Predict ETA** page or the quick prediction panel on the Overview

## Project Structure

```
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── generate_sample_data.py     # Sample dataset generator
├── .streamlit/
│   └── config.toml             # Streamlit theme configuration
├── core/
│   ├── __init__.py
│   ├── data_processor.py       # Data ingestion, cleaning, feature extraction
│   └── model_engine.py         # Model training, evaluation, inference
├── pages/
│   ├── __init__.py
│   ├── styles.py               # Global CSS design system
│   ├── page_overview.py        # Overview dashboard
│   ├── page_predict.py         # ETA prediction form
│   ├── page_dataset.py         # Dataset management
│   ├── page_model.py           # Model performance
│   └── page_settings.py        # Settings
├── data/                       # Dataset files (generated)
└── artifacts/                  # Trained model artifacts (generated)
```

## Dataset Format

The application accepts CSV files with delivery records. Column names are automatically normalised. Supported columns include:

| Column | Description |
|--------|-------------|
| `distance_km` | Delivery distance in kilometres |
| `weight_kg` | Package weight in kilograms |
| `pickup_hour` | Hour of pickup (0–23) |
| `day_of_week` | Day of week (0=Monday) |
| `service_type` | Service tier (Standard, Express, etc.) |
| `vehicle_type` | Vehicle type (Bike, Van, etc.) |
| `traffic_density` | Traffic level (Low, Medium, High, Jam) |
| `weather` | Weather conditions |
| `actual_duration_min` | **Target** — actual delivery duration in minutes |

## Tech Stack

- **Python** 3.9+
- **Streamlit** — Dashboard framework
- **Pandas** — Data processing
- **scikit-learn** — Machine learning models
- **XGBoost** — Gradient boosting (optional)
- **Plotly** — Interactive charts
