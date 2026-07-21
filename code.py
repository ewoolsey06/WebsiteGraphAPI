
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
        "start_date_time": "2026-06-01 00:00:00",
        "end_date_time": "2026-06-08 00:00:00"
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



# Plot
rt_fig = go.Figure()

rt_fig.add_trace(go.Scatter(
    x=rain_total.index,
    y=rain_total["value"],
    mode='lines',
    name='Rainfall',
    line=dict(color='#1f77b4')
))

rt_fig.update_layout(
    title="Rainfall Totals",
    xaxis_title="Day (last week)",
    yaxis_title="Rain (in)",
    hovermode='x unified',
    width=1000,
    height=400,
    template='plotly_white'
)


# Accumulated Rain sensor
rain_acc = df[
    df["sensor_sn"] == "22334782-2"
].copy()

if rain_acc.empty:
    st.error("Accumulated Rain sensor 22334782-2 not found.")
    st.stop()

rain_acc = rain_acc.sort_values("timestamp")

rain_acc["timestamp"] = pd.to_datetime(
    rain_acc["timestamp"]
)

rain_acc = rain_acc.set_index("timestamp")



# Plot
ra_fig = go.Figure()

ra_fig.add_trace(go.Scatter(
    x=rain_acc.index,
    y=rain_acc["value"],
    mode='lines',
    name='Rainfall',
    line=dict(color='#1f77b4')
))

ra_fig.update_layout(
    title="Accumulated Rainfall Totals",
    xaxis_title="Day (last week)",
    yaxis_title="Accumulated Rain (in)",
    hovermode='x unified',
    width=1000,
    height=400,
    template='plotly_white'
)


st.markdown(
    """
    <style>
    button[role="tab"] {
        color: #6b7280;
    }
    button[role="tab"]:hover {
        color: #005138 !important;
    }
    button[role="tab"][aria-selected="true"] {
        color: #005138 !important;
        font-weight: 600;
    }
    button[role="tab"][aria-selected="true"]::after {
        background-color: #005138 !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #005138 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.subheader("Rainfall / Device Analytics")
rain_tab, acc_tab = st.tabs(["Total Rain", "Accumulated Rain"])

with rain_tab:
    st.plotly_chart(rt_fig, use_container_width=True)

with acc_tab:
    st.plotly_chart(ra_fig, use_container_width=True)

