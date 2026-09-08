import requests
import pandas as pd
import os
import time

# ============================================================
# WeatherGuard AI - Multi-District NASA POWER Downloader
# ============================================================

OUTPUT_DIR = "data"

START_DATE = "20230101"
END_DATE = "20260907"

# District: (latitude, longitude)
DISTRICTS = {
    "hyderabad": (17.3850, 78.4867),
    "medak": (18.0453, 78.2608),
    "sangareddy": (17.6199, 78.0820),
    "hanamkonda": (18.0000, 79.5800),
    "nizamabad": (18.6725, 78.0941),
    "karimnagar": (18.4386, 79.1288),
    "khammam": (17.2473, 80.1514),
    "mahbubnagar": (16.7488, 78.0035),
}

BASE_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def download_district(district, latitude, longitude):

    print()
    print("=" * 60)
    print(f"Downloading: {district.upper()}")
    print(f"Coordinates: {latitude}, {longitude}")
    print("=" * 60)

    params = {
        "parameters": "T2M,RH2M,PS",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": START_DATE,
        "end": END_DATE,
        "format": "JSON",
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        properties = data["properties"]
        parameter_data = properties["parameter"]

        # NASA POWER returns dictionaries:
        # timestamp -> value
        t2m = parameter_data["T2M"]
        rh2m = parameter_data["RH2M"]
        ps = parameter_data["PS"]

        rows = []

        for timestamp in t2m.keys():

            rows.append({
                "datetime": pd.to_datetime(
                    timestamp,
                    format="%Y%m%d%H"
                ),
                "district": district.title(),
                "T2M": t2m[timestamp],
                "RH2M": rh2m[timestamp],
                "PS": ps[timestamp],
            })

        df = pd.DataFrame(rows)

        df = df.sort_values("datetime").reset_index(drop=True)

        # NASA POWER surface pressure is in kPa.
        # Convert to hPa to match our existing Hyderabad pipeline.
        df["PS"] = df["PS"] * 10

        # Replace NASA POWER missing-value marker if present.
        df = df.replace(-999, pd.NA)

        output_file = os.path.join(
            OUTPUT_DIR,
            f"{district}_weather.csv"
        )

        df.to_csv(output_file, index=False)

        print(f"Rows downloaded: {len(df):,}")
        print(f"Start: {df['datetime'].min()}")
        print(f"End:   {df['datetime'].max()}")
        print(f"Saved: {output_file}")

        print()
        print("Missing values:")
        print(df.isna().sum())

        return df

    except Exception as e:

        print(f"ERROR downloading {district}:")
        print(e)

        return None


# ============================================================
# Download all districts
# ============================================================

all_data = []

for district, (latitude, longitude) in DISTRICTS.items():

    df = download_district(
        district,
        latitude,
        longitude
    )

    if df is not None:
        all_data.append(df)

    # Small delay between requests
    time.sleep(2)


# ============================================================
# Combine all districts
# ============================================================

if all_data:

    combined = pd.concat(
        all_data,
        ignore_index=True
    )

    combined = combined.sort_values(
        ["district", "datetime"]
    ).reset_index(drop=True)

    combined_file = os.path.join(
        OUTPUT_DIR,
        "multidistrict_weather.csv"
    )

    combined.to_csv(
        combined_file,
        index=False
    )

    print()
    print("=" * 60)
    print("MULTI-DISTRICT DATASET CREATED")
    print("=" * 60)

    print(f"Total rows: {len(combined):,}")
    print(f"Districts: {combined['district'].nunique()}")

    print()
    print("Rows per district:")
    print(combined["district"].value_counts())

    print()
    print("Date range:")
    print("Start:", combined["datetime"].min())
    print("End:  ", combined["datetime"].max())

    print()
    print("Missing values:")
    print(combined.isna().sum())

    print()
    print(f"Saved: {combined_file}")

else:

    print()
    print("No datasets were downloaded.")