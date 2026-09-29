from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

# Current repository structure:
# EPL-Match-Analysis-Python/
# ├── dashboard/
# │   └── app.py
# ├── epl_analysis.py
# ├── epl_cleaned_validated.csv
# ├── requirements.txt
# └── README.md

sys.path.insert(0, str(ROOT))

from epl_analysis import (
    load_data,
    league_kpis,
    team_summary,
    big_wins,
    referee_summary,
)


DATA_PATH = ROOT / "epl_cleaned_validated.csv"


# ============================================================
# LOAD DATA
# ============================================================

df = load_data(DATA_PATH)


# ============================================================
# DASH APP
# ============================================================

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="EPL Match Analysis Dashboard",
)

server = app.server


# ============================================================
# STYLING
# ============================================================

PURPLE = "#5B2C83"
DARK_PURPLE = "#32154F"
LIGHT_PURPLE = "#F3EDF8"
WHITE = "#FFFFFF"
GREY = "#6B7280"

CARD_STYLE = {
    "backgroundColor": WHITE,
    "border": "none",
    "borderRadius": "12px",
    "boxShadow": "0 2px 10px rgba(0,0,0,0.08)",
    "padding": "18px",
    "height": "100%",
}

GRAPH_STYLE = {
    "backgroundColor": WHITE,
    "borderRadius": "12px",
    "boxShadow": "0 2px 10px rgba(0,0,0,0.06)",
    "padding": "10px",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_number(value):
    return f"{value:,.0f}"


def format_decimal(value):
    return f"{value:,.2f}"


def format_percent(value):
    return f"{value:.1f}%"


def kpi_card(title, value, subtitle=""):
    return dbc.Card(
        [
            html.Div(
                title,
                style={
                    "fontSize": "13px",
                    "fontWeight": "600",
                    "color": GREY,
                    "textTransform": "uppercase",
                    "letterSpacing": "0.5px",
                },
            ),
            html.Div(
                value,
                style={
                    "fontSize": "28px",
                    "fontWeight": "700",
                    "color": DARK_PURPLE,
                    "marginTop": "5px",
                },
            ),
            html.Div(
                subtitle,
                style={
                    "fontSize": "12px",
                    "color": GREY,
                    "marginTop": "3px",
                },
            ),
        ],
        style=CARD_STYLE,
    )


def apply_filters(
    data,
    season="All",
    team="All",
    referee="All",
    result="All",
):
    filtered = data.copy()

    if season != "All":
        filtered = filtered[filtered["Season"] == season]

    if team != "All":
        filtered = filtered[
            (filtered["HomeTeam"] == team)
            | (filtered["AwayTeam"] == team)
        ]

    if referee != "All":
        filtered = filtered[filtered["Referee"] == referee]

    if result != "All":
        result_map = {
            "Home Win": "HomeWin",
            "Away Win": "AwayWin",
            "Draw": "Draw",
        }
        filtered = filtered[
            filtered["Match_Result"] == result_map[result]
        ]

    return filtered


# ============================================================
# FILTER OPTIONS
# ============================================================

seasons = sorted(df["Season"].dropna().unique())

teams = sorted(
    set(df["HomeTeam"].dropna().unique())
    | set(df["AwayTeam"].dropna().unique())
)

referees = sorted(df["Referee"].dropna().unique())


# ============================================================
# LAYOUT
# ============================================================

app.layout = dbc.Container(
    [
        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            "English Premier League",
                            style={
                                "fontWeight": "800",
                                "marginBottom": "0",
                                "color": WHITE,
                            },
                        ),
                        html.H4(
                            "Match Analysis Dashboard",
                            style={
                                "fontWeight": "400",
                                "marginTop": "4px",
                                "color": "#E9DDF2",
                            },
                        ),
                        html.P(
                            "2010/11 – 2019/20 | 3,800 Matches",
                            style={
                                "marginBottom": "0",
                                "color": "#E9DDF2",
                            },
                        ),
                    ],
                    width=12,
                )
            ],
            style={
                "backgroundColor": DARK_PURPLE,
                "padding": "28px",
                "borderRadius": "0 0 15px 15px",
                "marginBottom": "22px",
            },
        ),

        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------
        dbc.Card(
            [
                html.H5(
                    "Dashboard Filters",
                    style={
                        "fontWeight": "700",
                        "color": DARK_PURPLE,
                        "marginBottom": "15px",
                    },
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    "Season",
                                    style={"fontWeight": "600"},
                                ),
                                dcc.Dropdown(
                                    id="season-filter",
                                    options=[
                                        {"label": "All Seasons", "value": "All"}
                                    ]
                                    + [
                                        {"label": s, "value": s}
                                        for s in seasons
                                    ],
                                    value="All",
                                    clearable=False,
                                ),
                            ],
                            md=3,
                        ),

                        dbc.Col(
                            [
                                html.Label(
                                    "Team",
                                    style={"fontWeight": "600"},
                                ),
                                dcc.Dropdown(
                                    id="team-filter",
                                    options=[
                                        {"label": "All Teams", "value": "All"}
                                    ]
                                    + [
                                        {"label": t, "value": t}
                                        for t in teams
                                    ],
                                    value="All",
                                    clearable=False,
                                    searchable=True,
                                ),
                            ],
                            md=3,
                        ),

                        dbc.Col(
                            [
                                html.Label(
                                    "Referee",
                                    style={"fontWeight": "600"},
                                ),
                                dcc.Dropdown(
                                    id="referee-filter",
                                    options=[
                                        {
                                            "label": "All Referees",
                                            "value": "All",
                                        }
                                    ]
                                    + [
                                        {"label": r, "value": r}
                                        for r in referees
                                    ],
                                    value="All",
                                    clearable=False,
                                    searchable=True,
                                ),
                            ],
                            md=3,
                        ),

                        dbc.Col(
                            [
                                html.Label(
                                    "Match Result",
                                    style={"fontWeight": "600"},
                                ),
                                dcc.Dropdown(
                                    id="result-filter",
                                    options=[
                                        {
                                            "label": "All Results",
                                            "value": "All",
                                        },
                                        {
                                            "label": "Home Win",
                                            "value": "Home Win",
                                        },
                                        {
                                            "label": "Away Win",
                                            "value": "Away Win",
                                        },
                                        {
                                            "label": "Draw",
                                            "value": "Draw",
                                        },
                                    ],
                                    value="All",
                                    clearable=False,
                                ),
                            ],
                            md=3,
                        ),
                    ]
                ),
            ],
            style=CARD_STYLE,
        ),

        html.Br(),

        # ----------------------------------------------------
        # KPI ROW
        # ----------------------------------------------------
        html.Div(id="kpi-row"),

        html.Br(),

        # ----------------------------------------------------
        # FIRST CHART ROW
        # ----------------------------------------------------
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="team-goals-chart"),
                    md=6,
                    style=GRAPH_STYLE,
                ),
                dbc.Col(
                    dcc.Graph(id="big-wins-chart"),
                    md=6,
                    style=GRAPH_STYLE,
                ),
            ],
            className="g-3",
        ),

        html.Br(),

        # ----------------------------------------------------
        # SECOND CHART ROW
        # ----------------------------------------------------
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="season-trend-chart"),
                    md=6,
                    style=GRAPH_STYLE,
                ),
                dbc.Col(
                    dcc.Graph(id="home-away-chart"),
                    md=6,
                    style=GRAPH_STYLE,
                ),
            ],
            className="g-3",
        ),

        html.Br(),

        # ----------------------------------------------------
        # THIRD CHART ROW
        # ----------------------------------------------------
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="conversion-chart"),
                    md=6,
                    style=GRAPH_STYLE,
                ),
                dbc.Col(
                    dcc.Graph(id="halftime-chart"),
                    md=6,
                    style=GRAPH_STYLE,
                ),
            ],
            className="g-3",
        ),

        html.Br(),

        # ----------------------------------------------------
        # REFEREE ANALYSIS
        # ----------------------------------------------------
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="referee-chart"),
                    width=12,
                    style=GRAPH_STYLE,
                )
            ]
        ),

        html.Br(),

        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------
        html.Div(
            [
                html.Hr(),
                html.P(
                    "EPL Match Analysis | Python • Pandas • NumPy • Plotly • Dash",
                    style={
                        "textAlign": "center",
                        "color": GREY,
                        "fontSize": "13px",
                    },
                ),
            ],
            style={"paddingBottom": "20px"},
        ),
    ],
    fluid=True,
    style={
        "backgroundColor": "#F8F7FA",
        "minHeight": "100vh",
        "paddingLeft": "30px",
        "paddingRight": "30px",
    },
)


# ============================================================
# CALLBACK
# ============================================================

@app.callback(
    [
        Output("kpi-row", "children"),
        Output("team-goals-chart", "figure"),
        Output("big-wins-chart", "figure"),
        Output("season-trend-chart", "figure"),
        Output("home-away-chart", "figure"),
        Output("conversion-chart", "figure"),
        Output("halftime-chart", "figure"),
        Output("referee-chart", "figure"),
    ],
    [
        Input("season-filter", "value"),
        Input("team-filter", "value"),
        Input("referee-filter", "value"),
        Input("result-filter", "value"),
    ],
)
def update_dashboard(
    selected_season,
    selected_team,
    selected_referee,
    selected_result,
):

    filtered = apply_filters(
        df,
        selected_season,
        selected_team,
        selected_referee,
        selected_result,
    )

    # --------------------------------------------------------
    # KPI CALCULATIONS
    # --------------------------------------------------------

    if filtered.empty:

        kpis = [
            kpi_card("Matches", "0"),
            kpi_card("Goals", "0"),
            kpi_card("Avg Goals / Match", "0"),
            kpi_card("Home Win Rate", "0%"),
            kpi_card("Avg Shots", "0"),
            kpi_card("Avg Cards", "0"),
        ]

    else:

        kpi = league_kpis(filtered)

        kpis = [
            kpi_card(
                "Matches",
                format_number(kpi["matches"]),
                "Matches in selection",
            ),
            kpi_card(
                "Goals",
                format_number(kpi["goals"]),
                "Total goals",
            ),
            kpi_card(
                "Avg Goals / Match",
                format_decimal(kpi["avg_goals_per_match"]),
                "Goals per match",
            ),
            kpi_card(
                "Home Win Rate",
                format_percent(kpi["home_win_pct"]),
                "Matches won at home",
            ),
            kpi_card(
                "Avg Shots",
                format_decimal(kpi["avg_shots"]),
                "Shots per match",
            ),
            kpi_card(
                "Avg Cards",
                format_decimal(kpi["avg_total_cards"]),
                "Yellow + red cards",
            ),
        ]

    kpi_row = dbc.Row(
        [dbc.Col(card, md=2) for card in kpis],
        className="g-3",
    )

    # --------------------------------------------------------
    # TEAM GOALS
    # --------------------------------------------------------

    if filtered.empty:

        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="No data available for current filters"
        )

        return (
            kpi_row,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
        )

    team_data = team_summary(filtered).reset_index()

    top_teams = team_data.head(10).sort_values("Goals")

    fig_team = px.bar(
        top_teams,
        x="Goals",
        y="Team",
        orientation="h",
        title="Top 10 Teams by Goals",
        text="Goals",
    )

    fig_team.update_traces(
        textposition="outside",
        marker_color=PURPLE,
    )

    fig_team.update_layout(
        template="plotly_white",
        xaxis_title="Goals",
        yaxis_title="",
    )

    # --------------------------------------------------------
    # BIG WINS
    # --------------------------------------------------------

    big_win_data = big_wins(filtered).head(10)

    if not big_win_data.empty:

        big_win_data = big_win_data.sort_values("BigWins")

        fig_big = px.bar(
            big_win_data,
            x="BigWins",
            y="Team",
            orientation="h",
            title="Teams with Most 3+ Goal Wins",
            text="BigWins",
        )

        fig_big.update_traces(
            textposition="outside",
            marker_color="#7B4BA5",
        )

    else:

        fig_big = go.Figure()

        fig_big.add_annotation(
            text="No 3+ goal wins in the selected data",
            x=0.5,
            y=0.5,
            showarrow=False,
        )

        fig_big.update_layout(
            title="Teams with Most 3+ Goal Wins"
        )

    fig_big.update_layout(
        template="plotly_white",
        xaxis_title="Number of 3+ Goal Wins",
        yaxis_title="",
    )

    # --------------------------------------------------------
    # SEASON TREND
    # --------------------------------------------------------

    season_data = (
        filtered.groupby("Season")
        .agg(
            Goals=("Total_Goals", "sum"),
            Avg_Goals=("Total_Goals", "mean"),
            Avg_Shots=("Total_Shots", "mean"),
        )
        .reset_index()
    )

    fig_season = go.Figure()

    fig_season.add_trace(
        go.Scatter(
            x=season_data["Season"],
            y=season_data["Avg_Goals"],
            mode="lines+markers",
            name="Average Goals",
        )
    )

    fig_season.update_layout(
        title="Average Goals per Match by Season",
        template="plotly_white",
        xaxis_title="Season",
        yaxis_title="Average Goals",
    )

    # --------------------------------------------------------
    # HOME VS AWAY PERFORMANCE
    # --------------------------------------------------------

    home_goals = filtered["HomeGoals"].sum()
    away_goals = filtered["AwayGoals"].sum()

    home_wins = (
        filtered["Match_Result"] == "HomeWin"
    ).sum()

    away_wins = (
        filtered["Match_Result"] == "AwayWin"
    ).sum()

    draw_count = (
        filtered["Match_Result"] == "Draw"
    ).sum()

    home_away_df = pd.DataFrame(
        {
            "Outcome": [
                "Home Wins",
                "Away Wins",
                "Draws",
            ],
            "Matches": [
                home_wins,
                away_wins,
                draw_count,
            ],
        }
    )

    fig_home_away = px.bar(
        home_away_df,
        x="Outcome",
        y="Matches",
        text="Matches",
        title="Match Outcomes: Home vs Away",
    )

    fig_home_away.update_traces(
        textposition="outside",
        marker_color=PURPLE,
    )

    fig_home_away.update_layout(
        template="plotly_white",
        xaxis_title="",
        yaxis_title="Matches",
    )

    # --------------------------------------------------------
    # GOAL CONVERSION
    # --------------------------------------------------------

    conversion = team_data[
        [
            "Team",
            "Shot_Accuracy",
            "Goal_Conversion",
        ]
    ].copy()

    conversion = conversion[
        conversion["Shots"] if "Shots" in conversion.columns else conversion["Team"].notna()
    ] if False else conversion

    conversion["Shot Accuracy %"] = (
        conversion["Shot_Accuracy"] * 100
    )

    conversion["Goal Conversion %"] = (
        conversion["Goal_Conversion"] * 100
    )

    conversion = conversion.head(10)

    fig_conversion = px.bar(
        conversion.sort_values("Goal Conversion %"),
        x="Goal Conversion %",
        y="Team",
        orientation="h",
        title="Goal Conversion Rate — Top 10 Teams",
        text="Goal Conversion %",
    )

    fig_conversion.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        marker_color="#8E63AE",
    )

    fig_conversion.update_layout(
        template="plotly_white",
        xaxis_title="Goals ÷ Shots (%)",
        yaxis_title="",
    )

    # --------------------------------------------------------
    # HALFTIME ANALYSIS
    # --------------------------------------------------------

    halftime = (
        filtered.groupby("Halftime_State")
        .size()
        .reset_index(name="Matches")
    )

    fig_halftime = px.bar(
        halftime,
        x="Halftime_State",
        y="Matches",
        text="Matches",
        title="Matches by Half-Time State",
    )

    fig_halftime.update_traces(
        textposition="outside",
        marker_color=PURPLE,
    )

    fig_halftime.update_layout(
        template="plotly_white",
        xaxis_title="Half-Time State",
        yaxis_title="Matches",
    )

    # --------------------------------------------------------
    # REFEREE ANALYSIS
    # --------------------------------------------------------

    referee_data = referee_summary(
        filtered,
        minimum_matches=10,
    ).head(10)

    if not referee_data.empty:

        referee_data = referee_data.sort_values(
            "Avg_Total_Cards"
        )

        fig_referee = px.bar(
            referee_data,
            x="Avg_Total_Cards",
            y="Referee",
            orientation="h",
            text="Avg_Total_Cards",
            title="Referee Card Patterns — Minimum 10 Matches",
        )

        fig_referee.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside",
            marker_color="#6F3D94",
        )

    else:

        fig_referee = go.Figure()

        fig_referee.add_annotation(
            text="Not enough referee observations for the selected filters",
            x=0.5,
            y=0.5,
            showarrow=False,
        )

        fig_referee.update_layout(
            title="Referee Card Patterns"
        )

    fig_referee.update_layout(
        template="plotly_white",
        xaxis_title="Average Total Cards per Match",
        yaxis_title="Referee",
    )

    return (
        kpi_row,
        fig_team,
        fig_big,
        fig_season,
        fig_home_away,
        fig_conversion,
        fig_halftime,
        fig_referee,
    )


# ============================================================
# RUN APP
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)
