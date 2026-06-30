
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit as st  # 1. Import Streamlit

st.title("LI-COR Device Data Dashboard")

TOKEN = "DV4iI3rviAxrn48ygbyqsYTIVx7NGTzan0bOewbnM47Y8B42"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

end = datetime.now()
start = end - timedelta(days=8)

# Get device list
devices_response = requests.get(
    "https://api.licor.cloud/v2/devices",
    headers=headers
)

if devices_response.status_code != 200:
    st.error("Could not retrieve devices.")
    st.text(devices_response.text)
    st.stop()

devices_json = devices_response.json()
devices = devices_json.get("devices", [])

all_devices_data = []

for d in devices:
    serial = d["deviceSerialNumber"]
    name = d["deviceName"]

    params = {
        "loggers": serial,
        "start_date_time": start.strftime("%Y-%m-%d %H:%M:%S"),
        "end_date_time": end.strftime("%Y-%m-%d %H:%M:%S")
    }

    r = requests.get(
        "https://api.licor.cloud/v1/data",
        headers=headers,
        params=params
    )

    print(f"\nDevice: {name} ({serial})")

    if r.status_code != 200:
        st.error("  - no data returned")
        continue

    data = r.json().get("data", [])

    if len(data) == 0:
        st.error("  - no observations in this time window")
        continue

    df_tmp = pd.DataFrame(data)
    all_devices_data.append(df_tmp)

    vars_available = (
        df_tmp[
            [
                "sensor_sn",
                "sensor_measurement_type",
                "unit"
            ]
        ]
        .drop_duplicates()
        .sort_values("sensor_measurement_type")
    )

    for _, row in vars_available.iterrows():
        print(
            f"  - {row['sensor_measurement_type']} "
            f"(sensor_sn: {row['sensor_sn']}, "
            f"units: {row['unit']})"
        )

# Combine all device data
if all_devices_data:
    df = pd.concat(all_devices_data, ignore_index=True)
else:
    st.text("No data returned from any devices.")
    st.stop()

# Rain sensor
rain_total = df[
    df["sensor_sn"] == "22334782-1"
].copy()

if rain_total.empty:
    st.error("Rain sensor 22334782-1 not found.")
    st.stop()

rain_total = rain_total.sort_values("timestamp")

rain_total["timestamp"] = pd.to_datetime(
    rain_total["timestamp"]
)

rain_total = rain_total.set_index("timestamp")

print(rain_total.head())

# Plot
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=rain_total.index,
    y=rain_total["value"],
    mode='lines',
    name='Rainfall',
    line=dict(color='#1f77b4')
))

fig.update_layout(
    title="Rainfall Totals",
    xaxis_title="Day (last week)",
    yaxis_title="Rain (in)",
    hovermode='x unified',
    width=1000,
    height=400,
    template='plotly_white'
)

fig.write_html('rainfall_plot.html')
print("Plot saved to rainfall_plot.html")


if 'fig' in locals():
    st.subheader("Rainfall Data")
    st.plotly_chart(fig, use_container_width=True)  # Renders the chart directly on the page
else:
    st.info("No data available to plot.")
