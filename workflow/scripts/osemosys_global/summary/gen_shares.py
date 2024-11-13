"""Calcualtes Renewable Generation"""

import pandas as pd
from typing import Optional
from constants import CLEAN, RENEWABLES, FOSSIL

# do not include storage in generation share calcualtion 
EXCLUDE = ["LDS", "SDS"]

def _get_gen_by_node(
    production: pd.DataFrame, include: Optional[list[str]] = None, exclude: Optional[list[str]] = None
) -> pd.DataFrame:

    df = production.copy()

    assert "TECHNOLOGY" in df.index.names

    df["TECH"] = df.index.get_level_values("TECHNOLOGY").str[3:6]
    df["NODE"] = df.index.get_level_values("TECHNOLOGY").str[6:11]

    if exclude:
        df = df[~df.TECH.isin(exclude)].copy()

    if include:
        df = df[df.TECH.isin(include)].copy()

    return (
        df.reset_index()[["REGION", "NODE", "YEAR", "VALUE"]]
        .groupby(["REGION", "NODE", "YEAR"])
        .sum()
    )


def calc_generation_shares(production_by_technology: pd.DataFrame) -> pd.DataFrame:

    df = production_by_technology.copy()

    df = df[
        (df.index.get_level_values("TECHNOLOGY").str.startswith("PWR"))
        & ~(df.index.get_level_values("TECHNOLOGY").str.contains("TRN"))
    ]

    total = _get_gen_by_node(df, exclude=EXCLUDE).rename(columns={"VALUE": "TOTAL"})
    clean = _get_gen_by_node(df, include=CLEAN).rename(columns={"VALUE": "CLEAN"})
    renewable = _get_gen_by_node(df, include=RENEWABLES).rename(columns={"VALUE": "RENEWABLE"})
    fossil = _get_gen_by_node(df, include=FOSSIL).rename(columns={"VALUE": "FOSSIL"})

    shares = (
        total.join(clean, how="outer")
        .join(renewable, how="outer")
        .join(fossil, how="outer")
        .fillna(0)
    )

    shares["CLEAN"] = shares.CLEAN.div(shares.TOTAL).mul(100)
    shares["RENEWABLE"] = shares.RENEWABLE.div(shares.TOTAL).mul(100)
    shares["FOSSIL"] = shares.FOSSIL.div(shares.TOTAL).mul(100)

    return shares[["CLEAN", "RENEWABLE", "FOSSIL"]].round(1)


if __name__ == "__main__":
    if "snakemake" in globals():
        production_by_technology_annual_csv = snakemake.input.production_by_technology
        save = snakemake.output.generation_shares
    else:
        production_by_technology_annual_csv = (
            "results/India/results/ProductionByTechnologyAnnual.csv"
        )
        save = "results/India/results/GenerationShares.csv"

    production_by_technology_annual = pd.read_csv(
        production_by_technology_annual_csv, index_col=[0, 1, 2, 3]
    )

    df = calc_generation_shares(production_by_technology_annual)

    df.to_csv(save, index=True)
