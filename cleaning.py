import pandas as pd
import numpy as np
import os

# Clean individual level data


def clean_individuals():
    """
    Clean individual level data
    """
    individuals = pd.read_csv("data/individuals.csv")
    individuals.columns = individuals.columns.str.lower()
    individuals.columns = individuals.columns.str.replace("-", "_")

    print("Individuals data")
    print("=====================================")
    print("Columns:\n")
    print(individuals.columns)
    print("First 10 rows:\n")
    print(individuals.head(10))
    print("Summary:\n")
    print(individuals.describe(include="all"))

    return individuals


# clean observations data


def clean_observations():
    """
    Clean observations data
    """
    observations = pd.read_csv("data/observations.csv")
    observations.columns = observations.columns.str.lower()
    observations.columns = observations.columns.str.replace("-", "_")

    observations.rename(columns={"individual": "ind_id"}, inplace=True)

    print("Observations data")
    print("=====================================")
    print("Columns:\n")
    print(observations.columns)
    print("First 10 rows:\n")
    print(observations.head(10))
    print("Summary:\n")
    print(observations.describe(include="all"))

    return observations


# Clean predators data
def clean_predators():
    predators = pd.read_csv("data/predators.csv")
    predators.columns = predators.columns.str.lower()
    predators.columns = predators.columns.str.replace("-", "_")

    predators.rename(columns={"index": "predator_id"}, inplace=True)

    print("Predators data")
    print("=====================================")
    print("Columns:\n")
    print(predators.columns)
    print("First 10 rows:\n")
    print(predators.head(10))
    print("Summary:\n")
    print(predators.describe(include="all"))

    return predators


# Plot level data


def clean_sites():
    """
    Clean sites data
    """
    sites = pd.read_csv("data/sites.csv")
    sites.rename(columns={"index": "deployment_id"}, inplace=True)

    # clean columns
    sites.columns = sites.columns.str.lower()
    sites.columns = sites.columns.str.replace("-", "_")

    print("Sites data")
    print("=====================================")
    print("Columns:\n")
    print(sites.columns)
    print("First 10 rows:\n")
    print(sites.head(10))

    return sites


def clean_plots():
    plots = pd.read_csv("data/plots.csv")

    plots.rename(columns={"index": "plot_id"}, inplace=True)

    print("Plots data")
    print("=====================================")
    print("Columns:\n")
    print(plots.columns)
    print("First 10 rows:\n")
    print(plots.head(10))
    print("Summary:\n")
    print(plots.describe(include="all"))

    return plots


# Clearn samples data


def clean_samples():
    """
    Clean samples data
    """
    samples = pd.read_csv("data/samples.csv")
    samples.rename(columns={"plot": "plot_id", "sample": "sample_id"}, inplace=True)

    print("Samples data")
    print("=====================================")
    print("Columns:\n")
    print(samples.columns)
    print("First 10 rows:\n")
    print(samples.head(10))
    print("Summary:\n")
    print(samples.describe(include="all"))

    return samples


# Clean benthic cover data
def clean_benthic_cover():
    benthic_cover = pd.read_csv("data/benthic-cover.csv")
    benthic_cover["name"] = benthic_cover["name"].str.replace(".png", "")
    benthic_cover["name"] = benthic_cover["name"].str.replace(r"_Q\d_", "_", regex=True)

    benthic_cover.rename(columns={"name": "plot_id"}, inplace=True)

    print("Benthic cover data")
    print("=====================================")
    print("Columns:\n")
    print(benthic_cover.columns)
    print("First 10 rows:\n")
    print(benthic_cover.head(10))
    print("Summary:\n")
    print(benthic_cover.describe(include="all"))

    # calculate benthic cover

    benthic_cover["category"].unique()

    benthic_classes = {
        "Coral": ["CORAL (CO)"],
        "Biomass": [
            "CRUSTOSE CORALLINE ALGAE (CCA)",
            "MACROALGAE (MA)",
            "TURF ALGAE (TA)",
            "BENTHIC CYANOBACTERIAL MAT (BCM)",
        ],
        "Sponge": ["SPONGE (SP)"],
        "Substrate": [
            "RUBBLE (RB)",
            "Dead Coral (DC)",
            "SAND (SA)",
            "OTHERS (OTS)",
            "SAND (SA)",
            "TAPE (TP)",
        ],
    }

    benthic_classes = {
        label: category
        for category, labels in benthic_classes.items()
        for label in labels
    }

    benthic_cover["category"] = benthic_cover["category"].map(benthic_classes)

    n_points = 100  # number of points sampled

    benthic_classes = (
        benthic_cover.groupby(["plot_id", "category"]).size().reset_index(name="count")
    )

    benthic_classes["cover"] = benthic_classes["count"] / n_points

    benthic_classes = benthic_classes.pivot(
        index="plot_id", columns="category", values="cover"
    ).reset_index()

    benthic_classes.columns = benthic_classes.columns.str.lower()

    benthic_classes["plot_id"] = benthic_classes["plot_id"].str.replace(
        "positive", "positive-control", regex=True
    )
    benthic_classes["plot_id"] = benthic_classes["plot_id"].str.replace(
        "negative", "negative-control", regex=True
    )

    benthic_classes.fillna(0, inplace=True)

    return benthic_classes


# Clean rugosity data
def clean_rugosity():
    """
    Clean rugosity data
    """
    rugosity = pd.read_csv("data/rugosity.csv")
    rugosity.columns = rugosity.columns.str.lower()
    rugosity.columns = rugosity.columns.str.replace("-", "_")

    rugosity["treatment"] = rugosity["treatment"].str.lower().str.replace(" ", "-")

    print("Rugosity data")
    print("=====================================")
    print("Columns:\n")
    print(rugosity.columns)
    print("First 10 rows:\n")
    print(rugosity.head(10))
    print("Summary:\n")
    print(rugosity.describe(include="all"))

    # calculate rugosity index

    D_max = 190  # length of the chain used

    rugosity["rugosity"] = 1 - (rugosity["measured_length_cm"] / D_max)

    rugosity["plot_id"] = (
        rugosity["deployment_id"].astype(str)
        + "_"
        + rugosity["treatment"].astype(str).str.lower().str.replace(" ", "-")
    )

    # mean rugosity

    rug = (
        rugosity.groupby(["deployment_id", "plot_id"])
        .agg(rugosity_mean=("rugosity", "mean"), rugosity_std=("rugosity", "std"))
        .reset_index()
    )

    # raw rugosity data

    rugosity.drop(
        columns=["deployment_id", "treatment", "measured_length_cm"], inplace=True
    )

    rugosity = rugosity.pivot(
        index="plot_id", columns="sample", values="rugosity"
    ).reset_index()

    rugosity.rename(columns={1: "sample_1", 2: "sample_2", 3: "sample_3"}, inplace=True)

    return rug, rugosity


## Metadata


def metadata():
    ## metadata

    behaviours = pd.read_csv("data/behaviours.csv")
    sizes = pd.read_csv("data/sizes.csv")

    print(r"""Ethogram with descriptions of observed behaviour:\n""")
    print(behaviours)

    print(r"""Size classes used to classify fish size:\n""")
    print(sizes)

    return behaviours


# Data cleaning and standardisation
print("Cleaned and standardised data")
print("=====================================")

## Predictors

# create a predictors data frame, drop unnecessary variables from sites


def create_predictors(sites, rug, benthic_classes, abundance):
    predictors = sites.drop(
        columns=["date", "time_in", "time_out", "lat", "lon", "crew", "remarks"]
    )

    predictors = predictors.merge(rug, how="left", on="deployment_id")

    predictors = predictors.merge(benthic_classes, how="left", on="plot_id")

    predictors["treatment"] = predictors["plot_id"].str.split("_").str[1]

    predictors["predator"] = np.array(
        [1 if x > 0 else 0 for x in abundance["n_predators"].values]
    )

    print("Predictors data")
    print("=====================================")
    print("Columns:\n")
    print(predictors.columns)
    print("First 10 rows:\n")
    print(predictors.head(10))
    print("Summary:\n")
    print(predictors.describe(include="all"))

    predictors.to_csv("outputs/data/predictors.csv", index=False)
    return predictors


## Response variables

### Plot - level


def calc_abn(individuals, predators):
    individuals["plot_id"] = (
        individuals["ind_id"].str.split("_").str[0]
        + "_"
        + individuals["ind_id"].str.split("_").str[1]
    )

    abundance = (
        individuals[["ind_id", "plot_id"]]
        .groupby("plot_id")
        .size()
        .reset_index(name="n_prey")
    )

    richness = (
        individuals[["plot_id", "species"]]
        .groupby("plot_id")
        .size()
        .reset_index(name="n_species")
    )

    abundance = abundance.merge(richness, how="left", on="plot_id")

    predators["plot_id"] = (
        predators["predator_id"].str.split("_").str[1]
        + "_"
        + predators["predator_id"].str.split("_").str[2]
    )

    abundance = abundance.merge(
        predators[["plot_id", "predator_id"]]
        .groupby("plot_id")
        .size()
        .reset_index(name="n_predators"),
        how="left",
        on="plot_id",
    )

    print("Plot level abundance data")
    print("=====================================")
    print("Columns:\n")
    print(abundance.columns)
    print("First 10 rows:\n")
    print(abundance.head(10))
    print("Summary:\n")
    print(abundance.describe(include="all"))

    abundance.to_csv("outputs/data/abundance.csv", index=False)

    return abundance


def calc_abn_size(individuals, predators):
    print(individuals["size_class"].unique())

    abundance_size = (
        individuals[["ind_id", "plot_id", "size_class"]]
        .groupby(["plot_id", "size_class"])
        .size()
        .reset_index(name="n_prey")
    ).copy()

    abundance_size = abundance_size.merge(
        predators[["plot_id", "predator_id", "size_class"]]
        .groupby(["plot_id", "size_class"])
        .size()
        .reset_index(name="n_predators"),
        how="left",
        on=["plot_id", "size_class"],
    )

    print("Abundance by size class data")
    print("=====================================")
    print("Columns:\n")
    print(abundance_size.columns)
    print("First 10 rows:\n")
    print(abundance_size.head(10))
    print("Summary:\n")
    print(abundance_size.describe(include="all"))

    abundance_size.to_csv("outputs/data/abundance_size.csv", index=False)
    return abundance_size


### Individual level response


def calculate_duration(df, samples):
    """
    Calculate duration of state type behaviours
    """

    # Group by and compute min/max time
    df = (
        df.groupby(["ind_id", "behaviour"])
        .agg(time_start=("time", "min"), time_end=("time", "max"))
        .reset_index()
    )

    # Calculate duration
    df["duration"] = df["time_end"] - df["time_start"]

    # Extract sample_id from ind_id
    df["sample_id"] = (
        df["ind_id"].str.split("_").str[0]
        + "_"
        + df["ind_id"].str.split("_").str[1]
        + "_"
        + df["ind_id"].str.split("_").str[2]
    )

    # Fix rows with 0 duration
    for index, row in df.iterrows():
        if row["duration"] == 0:
            if index + 1 < len(df):
                if df.loc[index + 1, "ind_id"] == row["ind_id"]:
                    df.loc[index, "time_end"] = df.loc[index + 1, "time_start"]
                    df.loc[index, "duration"] = (
                        df.loc[index, "time_end"] - df.loc[index, "time_start"]
                    )
                else:
                    sample_row = samples[samples["sample_id"] == row["sample_id"]]
                    if not sample_row.empty:
                        start_time = sample_row["start_time"].values[0]
                        df.loc[index, "time_end"] = (
                            start_time + 120
                        ) * 1000  # assuming milliseconds
                        df.loc[index, "duration"] = (
                            df.loc[index, "time_end"] - df.loc[index, "time_start"]
                        )
            else:
                sample_row = samples[samples["sample_id"] == row["sample_id"]]
                if not sample_row.empty:
                    start_time = sample_row["start_time"].values[0]
                    df.loc[index, "time_end"] = (
                        start_time + 120
                    ) * 1000  # assuming milliseconds
                    df.loc[index, "duration"] = (
                        df.loc[index, "time_end"] - df.loc[index, "time_start"]
                    )

    df["duration"] = df["duration"] / (1000)

    return df


def transform_behaviours(observations, behaviours, samples):
    data = pd.DataFrame({"ind_id": observations["ind_id"].unique()})

    for index, row in behaviours.iterrows():
        df = observations[observations["behaviour"] == row["name"]]

        if row["type"] == "Event":
            col = row["name"].lower() + "_" + "count"

            df = df.groupby("ind_id").size().reset_index(name=col)

        elif row["type"] == "State":
            df = calculate_duration(df, samples)

            df = df[["ind_id", "behaviour", "duration"]]

            df = df.pivot(
                index="ind_id", columns="behaviour", values="duration"
            ).reset_index()

        df.columns = df.columns.str.lower()
        df.columns = df.columns.str.replace("-", "_")
        df.columns = df.columns.str.replace(" ", "_")

        data = data.merge(df, how="left", on="ind_id")

    return data


def create_response(individuals, observations, behaviours, samples):
    response = individuals[["plot_id", "ind_id", "species", "size_class"]].copy()

    # add behavioural observations

    ind_beh = transform_behaviours(observations, behaviours, samples)

    ind_beh.fillna(0, inplace=True)

    response = response.merge(ind_beh, how="left", on="ind_id")

    response.rename(columns={"feeding": "foraging", "moving": "movement"}, inplace=True)
    response.rename(columns={"bite_count": "bites"}, inplace=True)

    print("Behavioural response data")
    print("=====================================")
    print("Columns:\n")
    print(response.columns)
    print("First 10 rows:\n")
    print(response.head(10))
    print("Summary:\n")
    print(response.describe(include="all"))

    response.to_csv("outputs/data/response.csv", index=False)

    return response


# clean trait data


def clean_guilds(response):
    """
    Cleans the guild data by filling in missing values based on genus and family.
    """
    print("Cleaning guilds...")

    traits = pd.read_csv("data/traits.csv")

    traits.columns = traits.columns.str.lower()

    traits.columns

    traits = traits[["sl.no", "family", "genus", "species", "feeding.guild"]]

    traits.columns = ["sl_no", "family", "genus", "species", "guild"]

    traits["species"] = traits["genus"] + " " + traits["species"]

    # filter species that are in the response data

    traits = traits[traits["species"].isin(response["species"].unique())]

    # complete family where missing based on genus

    def genus_to_family(genus):
        phylo = traits[["family", "genus"]].dropna().drop_duplicates()
        return phylo.set_index("genus")["family"].get(genus, "")

    traits.loc[traits["family"] == "", "family"] = traits["genus"].map(genus_to_family)

    # complete guild based on genus using mode

    def genus_to_guild(genus):
        guild = traits[traits["genus"] == genus]["guild"]

        if not guild.empty:
            mode = guild.mode()
            if not mode.empty:
                mode = mode[0]
                return mode

        return ""

    traits.loc[traits["guild"] == "", "guild"] = traits["genus"].map(genus_to_guild)

    # map family to guild using mode
    def family_to_guild(family):
        guild = traits[traits["family"] == family]["guild"]

        if not guild.empty:
            mode = guild.mode()
            if not mode.empty:
                mode = mode[0]
                return mode

        return ""

    traits.loc[traits["guild"] == "", "guild"] = traits["family"].map(family_to_guild)

    traits.drop(columns=["sl_no", "family", "genus"], inplace=True)

    # split multiple guilds into separate rows
    traits = traits.assign(guild=traits["guild"].str.split(",")).explode("guild")
    traits["guild"] = traits["guild"].str.strip()
    traits["guild"] = traits["guild"].str.capitalize()

    # determine relative guild membership

    traits["value"] = 1
    traits = traits.groupby(["species", "guild"]).sum().reset_index()
    traits["value"] = traits["value"] / traits.groupby("species")["value"].transform(
        "sum"
    )
    traits = traits.pivot_table(
        index="species", columns="guild", values="value", fill_value=0
    ).reset_index()

    return traits


# make dummy variables for categorical variables


def check_data(df, name, categoricals, order_categoricals):
    found_issue = False
    for col in df.columns:
        if col in categoricals:
            defined = set(order_categoricals[col])
            observed = set(df[col].dropna().unique())
            unexpected = observed - defined

            if unexpected:
                problem_rows = df[df[col].isin(unexpected)][[col]].copy()
                print(
                    f"\n⚠️ Warning in '{name}' — unexpected values in column '{col}':\n"
                )
                print("Rows with unexpected values:")
                print(problem_rows)
                found_issue = True
                break  # break inner loop
    if found_issue:
        return
    else:
        return print(f"All values in '{name}' are as expected\n")


def set_order(df, categoricals, order_categoricals):
    for col in df.columns:
        if col in categoricals:
            df[col] = pd.Categorical(
                df[col], categories=order_categoricals[col], ordered=True
            )
            df[col] = df[col].cat.codes

            if col == "plot_id":
                df[col] += 1  # > 0


# main function


def clean_data():
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    individuals = clean_individuals()
    observations = clean_observations()
    predators = clean_predators()
    sites = clean_sites()
    clean_plots()
    benthic_classes = clean_benthic_cover()
    rug, rugosity = clean_rugosity()
    behaviours = metadata()
    abundance = calc_abn(individuals, predators)
    abundance_size = calc_abn_size(individuals, predators)
    predictors = create_predictors(sites, rug, benthic_classes, abundance)
    samples = clean_samples()
    response = create_response(individuals, observations, behaviours, samples)
    guilds = clean_guilds(response)

    categoricals = [
        "deployment_id",
        "treatment",
        "plot_id",
        "location",
        "protection",
        "ind_id",
        "species",
        "size_class",
    ]

    order_categoricals = {
        "deployment_id": np.sort(predictors["deployment_id"].unique()),
        "treatment": np.array(
            ["negative-control", "positive-control", "barracuda", "grouper"],
            dtype=object,
        ),
        "plot_id": np.sort(predictors["plot_id"].unique()),
        "location": np.sort(predictors["location"].unique()),
        "protection": np.sort(predictors["protection"].unique())[::-1],  # reverse order
        "ind_id": np.sort(individuals["ind_id"].unique()),
        "species": np.sort(individuals["species"].unique()),
        "size_class": np.sort(individuals["size_class"].unique()),
    }

    data = [predictors, abundance, abundance_size, response, rugosity, guilds]

    for name, df in zip(
        ["predictors", "abundance", "abundance_size", "response", "rugosity", "guilds"],
        data,
    ):
        check_data(df, name, categoricals, order_categoricals)
        set_order(df, categoricals, order_categoricals)

        # save data
        df.to_csv(f"outputs/data/{name}.csv", index=False)

    print("Data cleaning and standardisation complete\n")

    return 0


if __name__ == "__main__":
    state = clean_data()
    if state != 0:
        print("Data cleaning failed")
