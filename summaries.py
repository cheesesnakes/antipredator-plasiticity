# /// script
# [tool.marimo.save]
# autosave_delay = 1000
# autosave = true
# format_on_save = true
#
# [tool.marimo.experimental]
# multi_column = true
# chat_sidebar = true
## Very experimental!
# lsp = true
#
# [tool.marimo.display]
# dataframes = "rich"
# default_width = "medium"
# [tool.marimo.runtime]
# watcher_on_save = "autorun"
# output_max_bytes = 10_000_000
# std_stream_max_bytes = 2_000_000
# dotenv = [".env"]
# ///

import marimo

__generated_with = "0.13.6"
app = marimo.App(
    width="medium",
    app_title="Plasticity in anti-predator behaviour of coral reef fish in the Andaman Islands",
    css_file="style.css",
)


@app.cell
def _(mo):
    mo.md("""# Plasticity in anti-predator behaviour of coral reef fish in the Andaman Islands""")
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    # import libraries

    import pandas as pd
    import seaborn as sns
    import os
    import matplotlib.pyplot as plt
    os.environ['R_HOME'] = '/usr/lib64/R'
    from rpy2 import robjects as ro

    # load data
    from cleaning import clean_data

    data = clean_data()

    # set plot theme

    sns.set_theme(style="white", context="notebook", palette="Set1", font_scale=1.5)
    return data, plt, ro, sns


@app.cell
def _(mo):
    mo.md(r"""# Data summaries""")
    return


@app.cell
def _(mo):
    mo.md(r"""## Sampling""")
    return


@app.cell
def _(data, mo):
    treatments = ["positive-control", "negative-control", "grouper", "baracuda"]

    mo.md(
        f"Deployments: {len(data['sites']['deployment_id'].unique())}\n\n\
        Locations: {len(data['sites']['location'].unique())}\n\n\
        Plots: {len(data['plots']['plot_id'].unique())}\n\n\
        Individuals: {len(data['individuals']['ind_id'].unique())}\n\n\
        Treatments: {len(treatments)}\n\n\
        Species: {len(data['individuals']['species'].unique())}\n\n"
    )
    return (treatments,)


@app.cell
def _(mo, treatments):
    mo.md(f"""Treatments: {treatments}""")
    return


@app.cell
def _(mo):
    mo.md(r"""## Predictors""")
    return


@app.cell
def _(data, mo):
    mo.md(f"""Depth:\n\nmean = {data["predictors"]["depth_avg"].mean():.2f} m, SD = {data["predictors"]["depth_avg"].std():.2f} m""")
    return


@app.cell
def _(data, plt, sns):
    sns.histplot(data["predictors"]["depth_avg"], binwidth=1)
    plt.xlabel("Depth (m)")
    return


@app.cell
def _(data, mo):
    mo.md(f"""Mean Rugosity:\n\nmean = {data["predictors"]["rugosity_mean"].mean():.2f}, SD = {data["predictors"]["rugosity_mean"].std():.2f}""")
    return


@app.cell
def _(data, plt, sns):
    sns.histplot(data["predictors"]["rugosity_mean"], binwidth=0.05, kde=True)
    plt.xlabel("Mean Rugosity")
    return


@app.cell
def _(data, mo):
    mo.md(f"""Variation in Rugosity:\n\nmean = {data["predictors"]["rugosity_std"].mean():.2f}, SD = {data["predictors"]["rugosity_std"].std():.2f}""")
    return


@app.cell
def _(data, plt, sns):
    sns.histplot(data["predictors"]["rugosity_std"], binwidth=0.01, kde=True)
    plt.xlabel("Variation in Rugosity")
    return


@app.cell
def _(data, mo):
    mo.md(f"""Biomas Cover:\n\nmean = {data["predictors"]["biomass"].mean():.2f}, SD = {data["predictors"]["biomass"].std():.2f}""")
    return


@app.cell
def _(data, plt, sns):
    sns.histplot(data["predictors"]["biomass"], binwidth=0.1, kde=True)
    plt.xlabel("Biomass Cover")
    return


@app.cell
def _(data, mo):
    mo.md(f"""Coral Cover:\n\nmean = {data["predictors"]["coral"].mean():.2f}, SD = {data["predictors"]["coral"].std():.2f}""")
    return


@app.cell
def _(data, plt, sns):
    sns.histplot(data["predictors"]["coral"], binwidth=0.1, kde=True)
    plt.xlabel("Coral Cover")
    return


@app.cell
def _(data, mo):
    mo.md(f"""Sponge Cover:\n\nmean = {data["predictors"]["sponge"].mean():.2f}, SD = {data["predictors"]["sponge"].std():.2f}""")
    return


@app.cell
def _(data, plt, sns):
    sns.histplot(data["predictors"]["sponge"], binwidth=0.01, kde=True)
    plt.xlabel("Sponge Cover")
    return


@app.cell
def _(data, plt, sns):
    sns.pairplot(
        data["predictors"].drop(
            columns=["deployment_id", "location", "plot_id", "treatment"]
        ),
        diag_kind="kde",
    )

    plt.savefig("figures/predictor_pairplot.png", dpi=300, bbox_inches="tight")

    plt.show()
    return


@app.cell
def _(mo):
    mo.md(r"""## Responses""")
    return


@app.cell
def _(mo):
    mo.md(r"""### Plot level responses""")
    return


@app.cell
def _(data, mo):
    mo.md(f"""Abundance of individuals in plots: \n\nmean = {data["abundance"]["abundance"].mean():.2f}, SD = {data["abundance"]["abundance"].std():.2f}""")
    return


@app.cell
def _(data, plt, sns):
    sns.histplot(data["abundance"]["abundance"], binwidth=5, kde=True)
    plt.xlabel("Abundance of individuals in plots")
    return


@app.cell
def _(mo):
    mo.md(r"""### Individual level repsonses""")
    return


@app.cell
def _(data, mo, ro):
    species = data["response"].groupby("species").size().reset_index(name="abundance")

    species = species.sort_values("abundance", ascending=False)

    # add guild

    species = species.merge(
        data["guilds"],
        on="species",
        how="left",
    )

    species.to_csv("outputs/species_list.csv", index=False)
    ro.r(
        """
           source("functions/species_table.R")
           """
    )
    mo.md(f"Number of observed species: {len(species)}")
    return (species,)


@app.cell
def _(species):
    species
    return


@app.cell
def _(plt, sns, species):
    plt.figure(figsize=(6, 24))
    sns.barplot(data=species, x="abundance", y="species")
    plt.xlabel("Abundance")
    plt.ylabel("Species")
    plt.yticks(fontstyle="italic")
    plt.show()
    return


@app.cell
def _(mo, species):
    no_guild = species[species["Unknown"] > 0][["species", "abundance"]].copy()

    no_guild.to_csv("outputs/data/no_guild_species.csv", index=False)

    mo.md(f"Number of species without guild: {len(no_guild)}")
    return


@app.cell
def _(data, species):
    guilds = species.melt(
        id_vars=["species", "abundance"],
        value_vars=data["guilds"].columns[1:],
        var_name="guild",
        value_name="value",
    )

    guilds = guilds[guilds["value"] > 0]

    guilds = (
        guilds.groupby("guild")
        .agg({"abundance": "sum"})
        .reset_index()
        .sort_values("abundance", ascending=False)
    )

    guilds
    return


@app.cell
def _(data, mo):
    size_class_dist = (
        data["response"].groupby("size_class").size().reset_index(name="count")
    )

    mo.md("Distribution of individuals by size class")
    return (size_class_dist,)


@app.cell
def _(plt, size_class_dist, sns):
    sns.barplot(data=size_class_dist, x="size_class", y="count")
    plt.xlabel("Size class")
    plt.ylabel("Count")
    return


@app.cell
def _(mo):
    mo.md(r"""Distribution of behavioural responses""")
    return


@app.cell
def _(data, plt, sns):
    sns.pairplot(
        data["response"][["foraging", "vigilance", "movement", "bites"]],
        diag_kind="kde",
    )

    plt.savefig("figures/response_pairplot.png", dpi=300, bbox_inches="tight")

    plt.show()
    return


@app.cell
def _(data, mo):
    mo.md(
        f"""
    Number of other behavioural observed\n\n\
        Predator Avoidance: {data["response"]["predator_avoidance_count"].sum()}\n\n\
        Aggression: {data["response"]["conspecific_aggression_count"].sum()}\n\n\
        Escape from Agression: {data["response"]["escape_from_aggression_count"].sum()}\n\n\
        Escape from predator: {data["response"]["escape_from_predator_count"].sum()}\n\n\
        Agression against predator: {data["response"]["aggression_against_predator_count"].sum()}\n\n
    """
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
