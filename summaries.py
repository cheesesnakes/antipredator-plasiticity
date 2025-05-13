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
    mo.md(r"""# Plasticity in anti-predator behaviour of coral reef fish in the Andaman Islands""")
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

    # load data
    from cleaning import (
        abundance,
        abundance_size,
        predictors,
        response,
        sites,
        plots,
        individuals,
    )
    # set plot theme

    sns.set_theme(style="white", context="notebook", palette="Set1", font_scale=1.5)
    return abundance, individuals, plots, plt, predictors, response, sites, sns


@app.cell
def _(mo):
    mo.md(r"""# Data summaries""")
    return


@app.cell
def _(mo):
    mo.md(r"""## Sampling""")
    return


@app.cell
def _(individuals, mo, plots, sites):
    treatments = ["positive-control", "negative-control", "grouper", "baracuda"]

    mo.md(
        f"Deployments: {len(sites['deployment_id'].unique())}\n\n\
        Locations: {len(sites['location'].unique())}\n\n\
        Plots: {len(plots['plot_id'].unique())}\n\n\
        Individuals: {len(individuals['ind_id'].unique())}\n\n\
        Treatments: {len(treatments)}\n\n\
        Species: {len(individuals['species'].unique())}\n\n"
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
def _(mo, predictors):
    mo.md(f"""Depth:\n\nmean = {predictors["depth_avg"].mean():.2f} m, SD = {predictors["depth_avg"].std():.2f} m""")
    return


@app.cell
def _(plt, predictors, sns):
    sns.histplot(predictors["depth_avg"], binwidth=1)
    plt.xlabel("Depth (m)")
    return


@app.cell
def _(mo, predictors):
    mo.md(f"""Mean Rugosity:\n\nmean = {predictors["rugosity_mean"].mean():.2f}, SD = {predictors["rugosity_mean"].std():.2f}""")
    return


@app.cell
def _(plt, predictors, sns):
    sns.histplot(predictors["rugosity_mean"], binwidth=0.05, kde=True)
    plt.xlabel("Mean Rugosity")
    return


@app.cell
def _(mo, predictors):
    mo.md(f"""Variation in Rugosity:\n\nmean = {predictors["rugosity_std"].mean():.2f}, SD = {predictors["rugosity_std"].std():.2f}""")
    return


@app.cell
def _(plt, predictors, sns):
    sns.histplot(predictors["rugosity_std"], binwidth=0.01, kde=True)
    plt.xlabel("Variation in Rugosity")
    return


@app.cell
def _(mo, predictors):
    mo.md(f"""Biomas Cover:\n\nmean = {predictors["biomass"].mean():.2f}, SD = {predictors["biomass"].std():.2f}""")
    return


@app.cell
def _(plt, predictors, sns):
    sns.histplot(predictors["biomass"], binwidth=0.1, kde=True)
    plt.xlabel("Biomass Cover")
    return


@app.cell
def _(mo, predictors):
    mo.md(f"""Coral Cover:\n\nmean = {predictors["coral"].mean():.2f}, SD = {predictors["coral"].std():.2f}""")
    return


@app.cell
def _(plt, predictors, sns):
    sns.histplot(predictors["coral"], binwidth=0.1, kde=True)
    plt.xlabel("Coral Cover")
    return


@app.cell
def _(mo, predictors):
    mo.md(f"""Sponge Cover:\n\nmean = {predictors["sponge"].mean():.2f}, SD = {predictors["sponge"].std():.2f}""")
    return


@app.cell
def _(plt, predictors, sns):
    sns.histplot(predictors["sponge"], binwidth=0.01, kde=True)
    plt.xlabel("Sponge Cover")
    return


@app.cell
def _(plt, predictors, sns):
    sns.pairplot(predictors.drop(columns=["deployment_id", "location", "plot_id", "treatment"]), diag_kind="kde")

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
def _(abundance, mo):
    mo.md(f"""Abundance of individuals in plots: \n\nmean = {abundance["n_prey"].mean():.2f}, SD = {abundance["n_prey"].std():.2f}""")
    return


@app.cell
def _(abundance, plt, sns):
    sns.histplot(abundance["n_prey"], binwidth=5, kde=True)
    plt.xlabel("Abundance of individuals in plots")
    return


@app.cell
def _(abundance, mo):
    mo.md(f"""Abundance of predators in plots: \n\nmean = {abundance["n_predators"].mean():.2f}, SD = {abundance["n_predators"].std():.2f}""")
    return


@app.cell
def _(abundance, plt, sns):
    sns.histplot(abundance["n_predators"], kde=True)
    plt.xlabel("Abundance of predators in plots")
    return


@app.cell
def _(abundance, mo):
    mo.md(f"""Species richness in plots: \n\nmean = {abundance["n_species"].mean():.2f}, SD = {abundance["n_species"].std():.2f}""")
    return


@app.cell
def _(abundance, plt, sns):
    sns.histplot(abundance["n_species"], binwidth=5, kde=True)
    plt.xlabel("Species richness in plots")
    return


@app.cell
def _(mo):
    mo.md(r"""### Individual level repsonses""")
    return


@app.cell
def _(mo, response):
    species = response.groupby("species").size().reset_index(name="abundance")

    species = species.sort_values("abundance", ascending=False)

    species.to_csv("outputs/species_list.csv", index=False)

    mo.md(f"Number of observed species: {len(species)}")
    return (species,)


@app.cell
def _(plt, sns, species):
    sns.barplot(data=species, x="abundance", y="species")
    plt.xlabel("Abundance")
    plt.ylabel("Species")
    return


@app.cell
def _(mo, response):
    size_class_dist = response.groupby("size_class").size().reset_index(name="count")

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
def _(plt, response, sns):
    sns.pairplot(
        response[["foraging", "vigilance", "movement", "bites"]],
        diag_kind="kde",
    )

    plt.savefig("figures/response_pairplot.png", dpi=300, bbox_inches="tight")

    plt.show()
    return


@app.cell
def _(mo, response):
    mo.md(
        f"""
    Number of other behavioural observed\n\n\
        Predator Avoidance: {response["predator_avoidance_count"].sum()}\n\n\
        Aggression: {response["conspecific_aggression_count"].sum()}\n\n\
        Escape from Agression: {response["escape_from_aggression_count"].sum()}\n\n\
        Escape from predator: {response["escape_from_predator_count"].sum()}\n\n\
        Agression against predator: {response["aggression_against_predator_count"].sum()}\n\n
    """
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
