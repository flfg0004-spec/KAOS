"""Chart generation engine using Plotly for PDF reports."""

import base64

import plotly.graph_objects as go
import plotly.io as pio


def create_bar_chart(data: dict, title: str, width: int = 800, height: int = 400) -> str:
    """Create bar chart and return base64 PNG."""
    if "x" not in data or "y" not in data:
        raise ValueError("create_bar_chart requires 'x' and 'y' keys in data dict")
    fig = go.Figure(data=[go.Bar(x=data["x"], y=data["y"], marker_color=data.get("color", "#38bdf8"))])
    fig.update_layout(title=title, template="plotly_dark", width=width, height=height)
    img_bytes = pio.to_image(fig, format="png", scale=2)
    return base64.b64encode(img_bytes).decode()


def create_line_chart(data: dict, title: str, width: int = 800, height: int = 400) -> str:
    """Create line chart and return base64 PNG."""
    if "x" not in data or "y" not in data:
        raise ValueError("create_line_chart requires 'x' and 'y' keys in data dict")
    fig = go.Figure(data=[go.Scatter(x=data["x"], y=data["y"], mode="lines+markers")])
    fig.update_layout(title=title, template="plotly_dark", width=width, height=height)
    img_bytes = pio.to_image(fig, format="png", scale=2)
    return base64.b64encode(img_bytes).decode()


def create_pie_chart(data: dict, title: str, width: int = 600, height: int = 400) -> str:
    """Create pie chart and return base64 PNG."""
    if "labels" not in data or "values" not in data:
        raise ValueError("create_pie_chart requires 'labels' and 'values' keys in data dict")
    fig = go.Figure(data=[go.Pie(labels=data["labels"], values=data["values"])])
    fig.update_layout(title=title, template="plotly_dark", width=width, height=height)
    img_bytes = pio.to_image(fig, format="png", scale=2)
    return base64.b64encode(img_bytes).decode()


def create_radar_chart(data: dict, title: str, width: int = 600, height: int = 500) -> str:
    """Create radar/spider chart and return base64 PNG."""
    if "values" not in data or "labels" not in data:
        raise ValueError("create_radar_chart requires 'values' and 'labels' keys in data dict")
    fig = go.Figure(data=[go.Scatterpolar(r=data["values"], theta=data["labels"], fill="toself")])
    fig.update_layout(title=title, template="plotly_dark", width=width, height=height, polar=dict(bgcolor="#1e293b"))
    img_bytes = pio.to_image(fig, format="png", scale=2)
    return base64.b64encode(img_bytes).decode()


def create_gauge_chart(value: float, title: str, max_value: float = 100, width: int = 400, height: int = 300) -> str:
    """Create gauge chart and return base64 PNG."""
    fig = go.Figure(
        go.Indicator(mode="gauge+number", value=value, title={"text": title}, gauge={"axis": {"range": [0, max_value]}})
    )
    fig.update_layout(template="plotly_dark", width=width, height=height)
    img_bytes = pio.to_image(fig, format="png", scale=2)
    return base64.b64encode(img_bytes).decode()


def create_heatmap(data: dict, title: str, width: int = 800, height: int = 500) -> str:
    """Create heatmap chart and return base64 PNG."""
    if "z" not in data:
        raise ValueError("create_heatmap requires 'z' key in data dict")
    fig = go.Figure(
        data=[
            go.Heatmap(
                z=data["z"], x=data.get("x", []), y=data.get("y", []), colorscale=data.get("colorscale", "Viridis")
            )
        ]
    )
    fig.update_layout(title=title, template="plotly_dark", width=width, height=height)
    img_bytes = pio.to_image(fig, format="png", scale=2)
    return base64.b64encode(img_bytes).decode()


def create_waterfall_chart(data: dict, title: str, width: int = 800, height: int = 400) -> str:
    """Create waterfall chart and return base64 PNG."""
    if "x" not in data or "y" not in data:
        raise ValueError("create_waterfall_chart requires 'x' and 'y' keys in data dict")
    fig = go.Figure(
        go.Waterfall(
            name="waterfall",
            orientation="v",
            measure=data.get("measure", ["relative"] * len(data["x"])),
            x=data["x"],
            y=data["y"],
            textposition="outside",
            text=data.get("text", data["y"]),
        )
    )
    fig.update_layout(title=title, template="plotly_dark", width=width, height=height)
    img_bytes = pio.to_image(fig, format="png", scale=2)
    return base64.b64encode(img_bytes).decode()


CHART_CREATORS = {
    "bar": create_bar_chart,
    "line": create_line_chart,
    "pie": create_pie_chart,
    "radar": create_radar_chart,
    "gauge": create_gauge_chart,
    "heatmap": create_heatmap,
    "waterfall": create_waterfall_chart,
}


def generate_chart(chart_type: str, data: dict, title: str = "", **kwargs) -> str:
    """Universal chart factory — dispatches to the correct creator."""
    creator = CHART_CREATORS.get(chart_type)
    if creator is None:
        raise ValueError(f"Unknown chart type: {chart_type}")
    if chart_type == "gauge":
        return creator(data.get("value", 0), title, data.get("max_value", 100), **kwargs)
    return creator(data, title, **kwargs)
