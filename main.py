# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "pandas==2.2.3",
# ]
# ///

import marimo

__generated_with = "0.12.10"
app = marimo.App(
    width="medium",
    app_title="Plasticity in anti-predator behaviour of coral reef fish in the Andaman Islands",
)


@app.cell
def _(mo):
    mo.md(
        r"""# Plasticity in anti-predator behaviour of coral reef fish in the Andaman Islands"""
    )
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _():
    # import libraries

    import pandas as pd
    import os

    # load data

    ## individual level

    individuals = pd.read_csv("data/individuals.csv")
    observations = pd.read_csv("data/observations.csv")
    predators = pd.read_csv("data/predators.csv")

    ## plot level

    sites = pd.read_csv("data/sites.csv")
    plots = pd.read_csv("data/plots.csv")
    samples = pd.read_csv("data/samples.csv")
    benthic_cover = pd.read_csv("data/benthic-cover.csv")
    rugosity = pd.read_csv("data/rugosity.csv")

    ## metadata

    behaviours = pd.read_csv("data/behaviours.csv")
    sizes = pd.read_csv("data/sizes.csv")
    return (
        behaviours,
        benthic_cover,
        individuals,
        observations,
        os,
        pd,
        plots,
        predators,
        rugosity,
        samples,
        sites,
        sizes,
    )


@app.cell
def _(mo):
    mo.md(r"""# Description of raw data""")
    return


@app.cell
def _(mo):
    mo.md(r"""## Individual level data""")
    return


@app.cell
def _(mo):
    mo.md(
        """
        Dataframe: Individuals

        file: individuals.csv

        Description: Individuals that were sampled in each plot

        Columns:

        - `ind_id`: (str) unique individual id 
        -  `species`: (str) specific identity of the sampled individuals
        -  `group`: (bool) whether the individual was observed as part of a group
        -  `size_class`: (str) the approximate sizew class of the observed individual
        -  `coordinates`: (list(i32)) corners of the bounding box within which the individual was observed in frame
        -  `file`: (str) the name of the video file in which the individual was observed
        -  `time_in`: (float) time in milliseconds since the start of the plot recording when the invidual was first recorded
        -  `time_out`: (float) time in milliseconds since the start of the plot recording when the invidual was last recorded 
        -  `remarks`: (str)
        """
    )
    return


@app.cell
def _(individuals):
    individuals.columns = individuals.columns.str.lower()
    individuals.columns = individuals.columns.str.replace("-", "_")

    individuals.rename(columns={"index": "ind_id"}, inplace=True)

    individuals
    return


@app.cell
def _(individuals):
    individuals.describe()
    return


@app.cell
def _(mo):
    mo.md(
        """
        Dataframe: Observations

        file: observations.csv

        Description: Behavioural observations of sampled individuals

        Columns:

        - `ind_id`: (str) unique individual id
        - `time`: (float) time in milliseconds since the start of the plot recording when the behaviour was observed
        - `behaviour`: (str) behaviour observed

        See ethogram for a description of behaviours
        """
    )
    return


@app.cell
def _(observations):
    observations.columns = observations.columns.str.lower()
    observations.columns = observations.columns.str.replace("-", "_")

    observations.rename(columns={"individual": "ind_id"}, inplace=True)

    observations
    return


@app.cell
def _(observations):
    observations.describe()
    return


@app.cell
def _(mo):
    mo.md(
        """
        Dataframe: Predators

        File: predators.csv

        Description: This dataframe contains information on the presence of predators in each plot sampled.

        Columns:

        - `predator_id`: (str) unique identifier for each predator observation
        - `species`: (str) The specific epithet of the predator
        - `size_class`: (str) The size class of the predator
        -  `time`: (float) The time in milliseconds since the start of the plot recording when the predator was first recorded
        -  `remarks`: (str) Additional notes or comments about the predator observation
        """
    )
    return


@app.cell
def _(predators):
    predators.columns = predators.columns.str.lower()
    predators.columns = predators.columns.str.replace("-", "_")

    predators.rename(columns={"index": "predator_id"}, inplace=True)
    predators
    return


@app.cell
def _(predators):
    predators.describe()
    return


@app.cell
def _(mo):
    mo.md(r"""## Plot level data""")
    return


@app.cell
def _(mo):
    mo.md(
        """
        Dataframe: Sites

        File: sites.csv

        Description: Information on sites

        Columns:

        - `date`: (str) date of sampling
        - `deployment_id`: (str) unique deployment id
        - `location`: (str) name of the sampled location
        - `protection`: (str) protection status of the sampled location (within or outside MPA)
        - `time_in`: (str) time of dive start
        - `time_out`: (str) time of dive end
        - `depth-avg`: (float) mean depth of the sampled location from the dive computer
        - `depth-max`: (float) maximum depth of the sampled location recorded on the dive computer
        - `visibility`: (int64) visibility in meters
        - `lat`: (float) latitude of the sampled location
        - `lon`: (float) longitude of the sampled location
        - `crew`: (str) names of boat crew on day of sampling
        - `remarks`: (str) additional notes about day of sampling
        """
    )
    return


@app.cell
def _(sites):
    sites.columns = sites.columns.str.lower()
    sites.columns = sites.columns.str.replace("-", "_")
    sites
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        Dataframe: Plots

        File: plots.csv

        Description: Information on plots

        Columns: 

        - `index`: (str) unique identifier for each plot
        - `time`: (float) total time sampled in seconds
        - `min_vid`: (float) minimum video length in seconds
        - `max_vid`: (float) maximum video length in seconds
        - `n_videos`: (int) number of video files in plot folder
        - `path`: (str) relative path to plot folder
        """
    )
    return


@app.cell
def _(plots):
    plots.rename(columns={"index": "plot_id"}, inplace=True)

    plots
    return


@app.cell
def _(plots):
    plots.describe()
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        Datframe: Samples

        File: samples.csv

        Description: Information on subsamples within each plot (2 minutes)

        Columns: 

        - `plot_id`: (str) unique identifier for each plot
        - `sample_id`: (str) unique identifier for each subsample
        - `start_time`: (float) start time of subsample since the start of the video in seconds
        - `video`: (str) name of the video file in which the subsample was recorded
        - `status`: (str) completion status of the subsample
        """
    )
    return


@app.cell
def _(samples):
    samples.rename(columns={"plot": "plot_id", "sample": "sample_id"}, inplace=True)
    samples
    return


@app.cell
def _(samples):
    samples.describe()
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        Dataframe: benthic_cover

        file: benthic-cover.csv

        Description: Benthic cover analysis of plots

        Columns:

        - `plot_id`: (str) unique identifier for the plot
        - `label`: (str) Label of the benthic cover class
        - `category`: (str) Category of the benthic cover class
        - `subcategory`: (str) Subcategory of the benthic cover class
        """
    )
    return


@app.cell
def _(benthic_cover):
    benthic_cover["name"] = benthic_cover["name"].str.replace(".png", "")
    benthic_cover["name"] = benthic_cover["name"].str.replace(r"_Q\d_", "_", regex=True)

    benthic_cover.rename(columns={"name": "plot_id"}, inplace=True)

    benthic_cover
    return


@app.cell
def _(benthic_cover):
    benthic_cover.describe()
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        Dataframe: Rugosity

        File: rugosit.csv

        Description: Chain transect data from each plot

        Columns:

        - `Deployment-id`: (str) unique deployment id
        - `treatment`: (str) Treatment of the plot
        - `sample`: (int) sample number
        - `Measured-length-cm`: (int) Distance covered by the chain on the benthos ($D_{bottom}$) in centimeters
        """
    )
    return


@app.cell
def _(rugosity):
    rugosity.columns = rugosity.columns.str.lower()
    rugosity.columns = rugosity.columns.str.replace("-", "_")

    rugosity
    return


@app.cell
def _(rugosity):
    rugosity.describe()
    return


@app.cell
def _(mo):
    mo.md(r"""## Metadata""")
    return


@app.cell
def _(mo):
    mo.md(r"""Ethogram with descriptions of observed behaviour:""")
    return


@app.cell
def _(behaviours):
    behaviours
    return


@app.cell
def _(mo):
    mo.md(r"""Size classes used to classify fish size:""")
    return


@app.cell
def _(sizes):
    sizes
    return


@app.cell
def _(mo):
    mo.md(r"""# Data cleaning and standardisation""")
    return


@app.cell
def _(benthic_cover, rugosity, sites):
    # create a predictors data frame, drop unnecessary variables from sites

    predictors = sites.drop(
        columns=["date", "time_in", "time_out", "lat", "lon", "crew", "remarks"]
    )

    # calculate rugosity index

    D_max = 190  # length of the chain used

    rugosity["rugosity"] = rugosity["measured_length_cm"] / D_max

    rugosity["plot_id"] = (
        rugosity["deployment_id"].astype(str)
        + "_"
        + rugosity["treatment"].astype(str).str.lower().str.replace(" ", "-")
    )

    rug = (
        rugosity.groupby(["deployment_id", "plot_id"])
        .agg(rugosity_mean=("rugosity", "mean"), rugosity_std=("rugosity", "std"))
        .reset_index()
    )

    predictors = predictors.merge(rug, how="left", on="deployment_id")

    # calculate benthic cover

    benthic_cover["category"].unique()

    benthic_classes = {
        "Coral" : ["CORAL (CO)"],
        "Biomass": ["CRUSTOSE CORALLINE ALGAE (CCA)", "MACROALGAE (MA)", "TURF ALGAE (TA)", "BENTHIC CYANOBACTERIAL MAT (BCM)"],
        "Sponge": ["SPONGE (SP)"],
        "Substrate": ["RUBBLE (RB)", "Dead Coral (DC)", "SAND (SA)", "OTHERS (OTS)", "SAND (SA)", "TAPE (TP)"],
    }

    benthic_classes = {label: category for category, labels in benthic_classes.items() for label in labels}

    benthic_cover["category"] = benthic_cover["category"].map(benthic_classes)

    n_points = 100 # number of points sampled

    benthic_classes = benthic_cover.groupby(["plot_id", "category"]).size().reset_index(name="count")

    benthic_classes["cover"] = benthic_classes["count"] / n_points

    benthic_classes = benthic_classes.pivot(index = "plot_id", columns = "category", values = "cover").reset_index()

    benthic_classes.columns = benthic_classes.columns.str.lower()

    benthic_classes["plot_id"] = benthic_classes["plot_id"].str.replace("positive", "positive-control", regex = True)
    benthic_classes["plot_id"] = benthic_classes["plot_id"].str.replace("negative", "negative-control", regex = True)

    predictors = predictors.merge(benthic_classes, how="left", on="plot_id")

    return D_max, benthic_classes, n_points, predictors, rug


@app.cell
def _(benthic_classes):
    benthic_classes
    return


@app.cell
def _(predictors):
    predictors
    return


@app.cell
def _(predictors):
    predictors.describe()
    return


if __name__ == "__main__":
    app.run()
