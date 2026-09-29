"""
EPL Match Analysis — Core Analysis Module
Covers 2010/11–2019/20 English Premier League matches.

The module keeps the raw dataset unchanged and flags source-data anomalies
rather than inventing replacement values.
"""

from pathlib import Path
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = BASE_DIR / "epl_cleaned_validated.csv"


def load_data(path=DEFAULT_DATA):
    """Load the validated EPL dataset and create reusable analysis fields."""
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    df["Goal_Difference"] = df["HomeGoals"] - df["AwayGoals"]
    df["Total_Goals"] = df["HomeGoals"] + df["AwayGoals"]

    df["Match_Result"] = np.select(
        [
            df["Goal_Difference"] > 0,
            df["Goal_Difference"] < 0,
        ],
        ["HomeWin", "AwayWin"],
        default="Draw",
    )

    df["Total_Shots"] = df["HomeShots"] + df["AwayShots"]
    df["Total_SoT"] = df["HomeShotsOnTarget"] + df["AwayShotsOnTarget"]
    df["Total_Corners"] = df["HomeCorners"] + df["AwayCorners"]
    df["Total_Fouls"] = df["HomeFouls"] + df["AwayFouls"]
    df["Total_Yellow_Cards"] = (
        df["HomeYellowCards"] + df["AwayYellowCards"]
    )
    df["Total_Red_Cards"] = df["HomeRedCards"] + df["AwayRedCards"]
    df["Total_Cards"] = (
        df["Total_Yellow_Cards"] + df["Total_Red_Cards"]
    )

    # Source-data validation for shot metrics.
    df["Shot_Accuracy_Valid"] = (
        (df["HomeShots"] >= 0)
        & (df["AwayShots"] >= 0)
        & (df["HomeShotsOnTarget"] >= 0)
        & (df["AwayShotsOnTarget"] >= 0)
        & (df["HomeShotsOnTarget"] <= df["HomeShots"])
        & (df["AwayShotsOnTarget"] <= df["AwayShots"])
    )

    valid_home = (df["HomeShots"] > 0) & df["Shot_Accuracy_Valid"]
    valid_away = (df["AwayShots"] > 0) & df["Shot_Accuracy_Valid"]

    df["Home_Shot_Accuracy"] = np.where(
        valid_home, df["HomeShotsOnTarget"] / df["HomeShots"], np.nan
    )
    df["Away_Shot_Accuracy"] = np.where(
        valid_away, df["AwayShotsOnTarget"] / df["AwayShots"], np.nan
    )

    # Goal conversion = goals / total shots.
    df["Home_Goal_Conversion"] = np.where(
        valid_home, df["HomeGoals"] / df["HomeShots"], np.nan
    )
    df["Away_Goal_Conversion"] = np.where(
        valid_away, df["AwayGoals"] / df["AwayShots"], np.nan
    )

    df["Halftime_State"] = np.select(
        [
            df["HomeGoalsHalftime"] > df["AwayGoalsHalftime"],
            df["HomeGoalsHalftime"] < df["AwayGoalsHalftime"],
        ],
        ["Home Lead", "Home Behind"],
        default="Level",
    )

    return df


def league_kpis(df):
    """Return high-level league KPIs."""
    return {
        "matches": len(df),
        "goals": int(df["Total_Goals"].sum()),
        "avg_goals_per_match": df["Total_Goals"].mean(),
        "home_wins": int((df["Match_Result"] == "HomeWin").sum()),
        "away_wins": int((df["Match_Result"] == "AwayWin").sum()),
        "draws": int((df["Match_Result"] == "Draw").sum()),
        "home_win_pct": (df["Match_Result"] == "HomeWin").mean() * 100,
        "away_win_pct": (df["Match_Result"] == "AwayWin").mean() * 100,
        "draw_pct": (df["Match_Result"] == "Draw").mean() * 100,
        "avg_shots": df["Total_Shots"].mean(),
        "avg_shots_on_target": df["Total_SoT"].mean(),
        "avg_fouls": df["Total_Fouls"].mean(),
        "avg_total_cards": df["Total_Cards"].mean(),
    }


def team_summary(df):
    """Combine home and away records into one team-level summary."""
    home = df[
        ["HomeTeam", "HomeGoals", "HomeShots", "HomeShotsOnTarget"]
    ].copy()
    home.columns = ["Team", "Goals", "Shots", "SoT"]

    away = df[
        ["AwayTeam", "AwayGoals", "AwayShots", "AwayShotsOnTarget"]
    ].copy()
    away.columns = ["Team", "Goals", "Shots", "SoT"]

    team = pd.concat([home, away], ignore_index=True)

    result = team.groupby("Team").agg(
        Matches=("Team", "size"),
        Goals=("Goals", "sum"),
        Shots=("Shots", "sum"),
        SoT=("SoT", "sum"),
    )

    result["Goals_per_match"] = result["Goals"] / result["Matches"]
    result["Shot_Accuracy"] = result["SoT"] / result["Shots"]
    result["Goal_Conversion"] = result["Goals"] / result["Shots"]

    return result.sort_values("Goals", ascending=False)


def big_wins(df, margin=3):
    """Count 3+ goal wins for both home and away teams."""
    home = df.loc[df["HomeGoals"] - df["AwayGoals"] >= margin, "HomeTeam"]
    away = df.loc[df["AwayGoals"] - df["HomeGoals"] >= margin, "AwayTeam"]

    counts = pd.concat([home, away]).value_counts()
    return counts.rename("BigWins").reset_index(names="Team")


def referee_summary(df, minimum_matches=50):
    """Compare referee card patterns using a minimum match threshold."""
    result = (
        df.groupby("Referee")
        .agg(
            Matches=("Referee", "size"),
            Avg_Yellow_Cards=("Total_Yellow_Cards", "mean"),
            Avg_Red_Cards=("Total_Red_Cards", "mean"),
            Avg_Total_Cards=("Total_Cards", "mean"),
            Avg_Home_Yellow=("HomeYellowCards", "mean"),
            Avg_Away_Yellow=("AwayYellowCards", "mean"),
        )
        .reset_index()
    )

    return (
        result[result["Matches"] >= minimum_matches]
        .sort_values("Avg_Total_Cards", ascending=False)
        .reset_index(drop=True)
    )


def halftime_outcomes(df):
    """Relate halftime state to the final match result."""
    table = pd.crosstab(
        df["Halftime_State"],
        df["Match_Result"],
        normalize="index",
    ) * 100

    return table.round(2)


def season_summary(df):
    """Create season-level trend metrics."""
    return (
        df.groupby("Season")
        .agg(
            Matches=("Season", "size"),
            Goals=("Total_Goals", "sum"),
            Avg_Goals=("Total_Goals", "mean"),
            Avg_Shots=("Total_Shots", "mean"),
            Avg_SoT=("Total_SoT", "mean"),
            Avg_Fouls=("Total_Fouls", "mean"),
            Avg_Cards=("Total_Cards", "mean"),
        )
        .reset_index()
    )


if __name__ == "__main__":
    data = load_data()
    print("EPL Match Analysis")
    print("-" * 40)
    for key, value in league_kpis(data).items():
        print(f"{key}: {value}")

    print("\nTop 10 teams by total goals:")
    print(team_summary(data).head(10)[
        ["Matches", "Goals", "Goals_per_match",
         "Shot_Accuracy", "Goal_Conversion"]
    ])

    print("\nTop big-win teams:")
    print(big_wins(data).head(10))

    print("\nTop referee card averages (50+ matches):")
    print(referee_summary(data).head(10))
