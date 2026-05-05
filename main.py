# main.py

from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd

# =========================
# CARGA Y PREPARACIÓN DATOS
# =========================

df = pd.read_csv("data/cleaned_dataset.csv")

# Convertir fecha
df["order_date"] = pd.to_datetime(df["order_date"])

# Crear columnas de tiempo
df["year"] = df["order_date"].dt.year
df["month"] = df["order_date"].dt.month
df["month_name"] = df["order_date"].dt.strftime("%b")
df["year_month"] = df["order_date"].dt.to_period("M").astype(str)

# =========================
# APP DASH
# =========================

app = Dash(__name__)

# =========================
# LAYOUT
# =========================

app.layout = html.Div(
    style={
        "padding": "20px",
        "fontFamily": "Arial",
        "backgroundColor": "#f4f4f4",
    },
    children=[

        html.H1(
            "E-Commerce Sales Dashboard",
            style={
                "textAlign": "center",
                "marginBottom": "30px",
                "color": "#222",
            }
        ),

        # =========================
        # FILTROS / MENÚS
        # =========================

        html.Div(
            style={
                "display": "flex",
                "gap": "20px",
                "marginBottom": "30px",
                "flexWrap": "wrap",
            },
            children=[

                # Dropdown categoría
                html.Div([
                    html.Label("Product Category"),
                    dcc.Dropdown(
                        id="category-filter",
                        options=[
                            {"label": c, "value": c}
                            for c in sorted(df["product_category"].unique())
                        ],
                        multi=True,
                        placeholder="Select categories",
                    ),
                ], style={"width": "250px"}),

                # Dropdown región
                html.Div([
                    html.Label("Customer Region"),
                    dcc.Dropdown(
                        id="region-filter",
                        options=[
                            {"label": r, "value": r}
                            for r in sorted(df["customer_region"].unique())
                        ],
                        multi=True,
                        placeholder="Select regions",
                    ),
                ], style={"width": "250px"}),

                # RadioItems tipo gráfico
                html.Div([
                    html.Label("Sales Chart Type"),
                    dcc.RadioItems(
                        id="chart-type",
                        options=[
                            {"label": "Line", "value": "line"},
                            {"label": "Bar", "value": "bar"},
                        ],
                        value="line",
                        inline=True,
                    ),
                ]),

                # Botón cambiar tema
                html.Div([
                    html.Label("Dashboard Theme"),
                    dcc.Dropdown(
                        id="theme-selector",
                        options=[
                            {"label": "Light", "value": "plotly_white"},
                            {"label": "Dark", "value": "plotly_dark"},
                        ],
                        value="plotly_white",
                        clearable=False,
                    ),
                ], style={"width": "200px"}),

            ]
        ),

        # =========================
        # GRÁFICOS 2X2
        # =========================

        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "20px",
            },
            children=[

                dcc.Graph(id="sales-trend"),

                dcc.Graph(id="category-sales"),

                dcc.Graph(id="payment-methods"),

                dcc.Graph(id="regional-profit"),

            ]
        )
    ]
)

# =========================
# CALLBACK
# =========================

@app.callback(
    [
        Output("sales-trend", "figure"),
        Output("category-sales", "figure"),
        Output("payment-methods", "figure"),
        Output("regional-profit", "figure"),
    ],
    [
        Input("category-filter", "value"),
        Input("region-filter", "value"),
        Input("chart-type", "value"),
        Input("theme-selector", "value"),
    ]
)

def update_dashboard(categories, regions, chart_type, theme):

    filtered_df = df.copy()

    # Filtro categoría
    if categories and len(categories) > 0:
        filtered_df = filtered_df[
            filtered_df["product_category"].isin(categories)
        ]

    # Filtro región
    if regions and len(regions) > 0:
        filtered_df = filtered_df[
            filtered_df["customer_region"].isin(regions)
        ]

    # ==================================================
    # 1. GRÁFICO DE LÍNEAS CON RANGE SLIDER Y SELECTOR
    # ==================================================

    monthly_sales = (
        filtered_df
        .groupby("order_date")["total_revenue"]
        .sum()
        .reset_index()
    )

    if chart_type == "line":
        fig1 = px.line(
            monthly_sales,
            x="order_date",
            y="total_revenue",
            title="Revenue Over Time",
            template=theme,
        )
    else:
        fig1 = px.bar(
            monthly_sales,
            x="order_date",
            y="total_revenue",
            title="Revenue Over Time",
            template=theme,
        )

    fig1.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date",
        )
    )

    # ===================================
    # 2. VENTAS POR CATEGORÍA
    # ===================================

    category_sales = (
        filtered_df
        .groupby("product_category")["total_revenue"]
        .sum()
        .reset_index()
    )

    fig2 = px.bar(
        category_sales,
        x="product_category",
        y="total_revenue",
        color="product_category",
        title="Revenue by Product Category",
        template=theme,
    )

    # ===================================
    # 3. MÉTODOS DE PAGO
    # ===================================

    payment_data = (
        filtered_df["payment_method"]
        .value_counts()
        .reset_index()
    )

    payment_data.columns = ["payment_method", "count"]

    fig3 = px.pie(
        payment_data,
        names="payment_method",
        values="count",
        title="Payment Methods Distribution",
        template=theme,
    )

    # ===================================
    # 4. GANANCIAS POR REGIÓN
    # ===================================

    regional_profit = (
        filtered_df
        .groupby("customer_region")["profit"]
        .sum()
        .reset_index()
    )

    fig4 = px.scatter(
        regional_profit,
        x="customer_region",
        y="profit",
        size="profit",
        color="customer_region",
        title="Profit by Region",
        template=theme,
    )

    return fig1, fig2, fig3, fig4

# =========================
# RUN SERVER
# =========================

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )