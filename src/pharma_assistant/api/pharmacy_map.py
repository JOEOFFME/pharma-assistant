"""Plotly Express map of source-backed records and a geodesic search perimeter."""

import html
import json
import math

import plotly.express as px
import plotly.graph_objects as go

from pharma_assistant.data.pharmacies import NearbyPharmacy


def radius_ring(lat: float, lon: float, radius_km: float) -> tuple[list, list]:
    """Sample a closed spherical circle using the repository's Earth radius."""
    phi, lam, delta = math.radians(lat), math.radians(lon), radius_km / 6371.0088
    lats, lons = [], []
    for degree in range(0, 361, 5):
        bearing = math.radians(degree)
        p = math.asin(
            math.sin(phi) * math.cos(delta)
            + math.cos(phi) * math.sin(delta) * math.cos(bearing)
        )
        longitude = lam + math.atan2(
            math.sin(bearing) * math.sin(delta) * math.cos(phi),
            math.cos(delta) - math.sin(phi) * math.sin(p),
        )
        lats.append(math.degrees(p))
        lons.append((math.degrees(longitude) + 180) % 360 - 180)
    return lats, lons


def make_map(
    rows: list[NearbyPharmacy], lat: float, lon: float, radius_km: float
) -> dict:
    """Build a key-free OSM map, including a visible center for empty results."""
    if rows:
        figure = px.scatter_map(
            lat=[row.pharmacy.latitude for row in rows],
            lon=[row.pharmacy.longitude for row in rows],
            hover_name=[
                html.escape(row.pharmacy.name or "Nom inconnu") for row in rows
            ],
            custom_data=[
                [f"{row.distance_km:.2f} km" for row in rows],
                [
                    html.escape(", ".join(row.pharmacy.phones_e164) or "Inconnu")
                    for row in rows
                ],
                [html.escape(row.pharmacy.opening_hours or "Inconnus") for row in rows],
            ],
        )
        figure.update_traces(
            lat=[row.pharmacy.latitude for row in rows],
            lon=[row.pharmacy.longitude for row in rows],
            marker={"size": 12, "color": "#176f50"},
            hovertemplate=(
                "<b>%{hovertext}</b><br>%{customdata[0]}"
                "<br>Tél. : %{customdata[1]}"
                "<br>Horaires : %{customdata[2]}<extra></extra>"
            ),
        )
    else:
        figure = go.Figure()
    ring_lat, ring_lon = radius_ring(lat, lon, radius_km)
    figure.add_trace(
        go.Scattermap(
            lat=ring_lat,
            lon=ring_lon,
            mode="lines",
            name="Périmètre",
            line={"color": "#176f50", "width": 2},
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scattermap(
            lat=[lat],
            lon=[lon],
            mode="markers",
            name="Centre choisi",
            marker={"size": 16, "color": "#c44b32"},
            hovertemplate="Centre de recherche<extra></extra>",
        )
    )
    zoom = max(1, min(16, math.log2(15000 / radius_km)))
    figure.update_layout(
        map={
            "style": "open-street-map",
            "center": {"lat": lat, "lon": lon},
            "zoom": zoom,
        },
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=480,
        showlegend=False,
    )
    payload = json.loads(figure.to_json())
    if rows:
        # Keep API coordinates inspectable rather than Plotly binary arrays.
        payload["data"][0]["lat"] = [row.pharmacy.latitude for row in rows]
        payload["data"][0]["lon"] = [row.pharmacy.longitude for row in rows]
    return payload
