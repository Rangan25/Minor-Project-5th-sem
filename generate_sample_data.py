"""
generate_sample_data.py
───────────────────────
Generate a realistic sample delivery dataset for demonstration.
Run this to create data/sample_deliveries.csv
"""

import os
import numpy as np
import pandas as pd

np.random.seed(42)

N = 1500

# Generate features
distance_km = np.round(np.random.exponential(12, N) + 1.5, 1)
distance_km = np.clip(distance_km, 1.0, 80.0)

weight_kg = np.round(np.random.lognormal(0.5, 0.8, N), 1)
weight_kg = np.clip(weight_kg, 0.1, 50.0)

pickup_hour = np.random.choice(range(7, 23), N, p=np.array(
    [0.03, 0.05, 0.06, 0.07, 0.09, 0.10, 0.10, 0.10, 0.08, 0.07, 0.06, 0.05, 0.04, 0.04, 0.03, 0.03]
))

day_of_week = np.random.randint(0, 7, N)

service_types = ["Standard", "Express", "Same-Day", "Economy"]
service_type = np.random.choice(service_types, N, p=[0.45, 0.25, 0.15, 0.15])

vehicle_types = ["Bike", "Scooter", "Van", "Truck"]
vehicle_type = np.random.choice(vehicle_types, N, p=[0.30, 0.35, 0.25, 0.10])

traffic_levels = ["Low", "Medium", "High", "Jam"]
traffic_density = np.random.choice(traffic_levels, N, p=[0.20, 0.40, 0.30, 0.10])

weather_conditions = ["Clear", "Cloudy", "Rain", "Fog"]
weather = np.random.choice(weather_conditions, N, p=[0.45, 0.30, 0.18, 0.07])

cities = ["Metro", "Urban", "Semi-Urban", "Rural"]
city = np.random.choice(cities, N, p=[0.35, 0.30, 0.25, 0.10])

rating = np.round(np.random.uniform(2.5, 5.0, N), 1)
rider_age = np.random.randint(20, 45, N)
multiple_deliveries = np.random.choice([0, 1, 2, 3], N, p=[0.25, 0.40, 0.25, 0.10])

# Simulate delivery duration (target)
base_time = 15.0  # base minutes
duration = (
    base_time
    + distance_km * 1.8
    + weight_kg * 0.3
    + np.where(service_type == "Express", -8, 0)
    + np.where(service_type == "Same-Day", -5, 0)
    + np.where(service_type == "Economy", 10, 0)
    + np.where(traffic_density == "High", 10, 0)
    + np.where(traffic_density == "Jam", 20, 0)
    + np.where(traffic_density == "Low", -5, 0)
    + np.where(weather == "Rain", 7, 0)
    + np.where(weather == "Fog", 12, 0)
    + np.where(vehicle_type == "Bike", -3, 0)
    + np.where(vehicle_type == "Truck", 8, 0)
    + np.where(city == "Rural", 12, 0)
    + np.where(city == "Semi-Urban", 5, 0)
    + np.where(city == "Metro", -3, 0)
    + (pickup_hour - 12) * 0.3
    + np.where(day_of_week >= 5, 5, 0)  # weekends
    + multiple_deliveries * 4
    + np.random.normal(0, 5, N)  # noise
)
duration = np.clip(np.round(duration, 1), 5.0, 180.0)

# Generate order IDs
order_ids = [f"DLV-{i+10001}" for i in range(N)]

df = pd.DataFrame({
    "order_id": order_ids,
    "distance_km": distance_km,
    "weight_kg": weight_kg,
    "pickup_hour": pickup_hour,
    "day_of_week": day_of_week,
    "service_type": service_type,
    "vehicle_type": vehicle_type,
    "traffic_density": traffic_density,
    "weather": weather,
    "city": city,
    "rating": rating,
    "rider_age": rider_age,
    "multiple_deliveries": multiple_deliveries,
    "actual_duration_min": duration,
})

# Add a few missing values for realism
rng = np.random.default_rng(42)
mask_weight = rng.random(N) < 0.02
mask_rating = rng.random(N) < 0.03
df.loc[mask_weight, "weight_kg"] = np.nan
df.loc[mask_rating, "rating"] = np.nan

os.makedirs("data", exist_ok=True)
path = os.path.join("data", "sample_deliveries.csv")
df.to_csv(path, index=False)
print(f"Generated {len(df)} records -> {path}")
