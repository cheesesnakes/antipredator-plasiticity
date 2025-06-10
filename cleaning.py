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

    Args:
        response (pd.DataFrame): The input DataFrame containing species data.

    Returns:
        pd.DataFrame: The cleaned and imputed DataFrame with relative guild memberships.
    """
    print("Cleaning guilds...")

    print("Cleaning guilds...")

    # Load and preprocess traits data
    traits = pd.read_csv("data/traits.csv")

    traits.columns = traits.columns.str.lower()
    traits = traits[["sl.no", "family", "genus", "species", "feeding.guild"]].copy()
    traits.columns = ["sl_no", "family", "genus", "species", "guild"]

    # Create a reliable mapping from genus to family from existing data
    family_map = (
        traits[["genus", "family"]][traits["family"] != ""]
        .dropna()
        .drop_duplicates()
        .set_index("genus")["family"]
    )

    # Create a reliable mapping from genus to guild using mode
    genus_guild_map = (
        traits[["genus", "guild"]][traits["guild"] != ""]
        .groupby(["genus", "guild"])
        .size()
        .reset_index(name="count")
    )

    genus_guild_map = (
        genus_guild_map.loc[genus_guild_map.groupby("genus")["count"].idxmax()]
        .set_index("genus")["guild"]
        .to_dict()
    )

    # create a reliable mapping from family to guild using mode

    family_guild_map = (
        traits[["family", "guild"]][traits["guild"] != ""]
        .groupby(["family", "guild"])
        .size()
        .reset_index(name="count")
    )

    family_guild_map = (
        family_guild_map.loc[family_guild_map.groupby("family")["count"].idxmax()]
        .set_index("family")["guild"]
        .to_dict()
    )

    # Combine genus and species to create a consistent 'species' column
    traits["genus"] = traits["genus"].str.strip()
    traits["species"] = traits["genus"].fillna("") + " " + traits["species"].fillna("")
    traits["species"] = traits["species"].str.strip()

    # Identify and add missing species from 'response' to 'traits'
    # Only consider species not already present in traits and not 'Unknown'
    response["species"] = response["species"].str.strip()
    missing_species_in_traits = response[~response["species"].isin(traits["species"])]
    missing_species_in_traits = missing_species_in_traits[
        missing_species_in_traits["species"] != "Unknown"
    ].copy()

    if not missing_species_in_traits.empty:
        # Create a DataFrame for these missing species with placeholder columns
        new_species_df = pd.DataFrame(
            {
                "species": missing_species_in_traits["species"].unique(),
                "family": "",
                "guild": "",
                "sl_no": np.nan,
            }
        )

        new_species_df["genus"] = new_species_df["species"].str.split(" ", n=1).str[0]

        traits = pd.concat([traits, new_species_df], ignore_index=True)

    # --- Imputation Logic ---

    # 1. Complete family where missing based on genus

    for index, row in traits.iterrows():
        if row["family"] == "":
            if row["genus"] in family_map:
                traits.at[index, "family"] = family_map[row["genus"]]
            else:
                # If genus is not in the map, set family to "Unknown"
                traits.at[index, "family"] = ""

    # 2. Complete guild based on genus using mode

    for index, row in traits.iterrows():
        if row["guild"] == "" or row["guild"] == "Unknown":
            if row["genus"] in genus_guild_map:
                traits.at[index, "guild"] = genus_guild_map[row["genus"]]
            else:
                # If genus is not in the map, set guild to "Unknown"
                traits.at[index, "guild"] = "Unknown"

    # 3. Complete guild based on family using mode (for remaining blanks)

    for index, row in traits.iterrows():
        if row["guild"] == "" or row["guild"] == "Unknown":
            if row["family"] in family_guild_map:
                traits.at[index, "guild"] = family_guild_map[row["family"]]
            else:
                # If family is not in the map, set guild to "Unknown"
                traits.at[index, "guild"] = "Unknown"

    # Drop unnecessary columns
    traits.drop(columns=["sl_no", "family", "genus"], inplace=True)

    # Split multiple guilds into separate rows and clean
    traits["guild"] = traits["guild"].fillna("").astype(str)  # Ensure guild is string
    traits = traits.assign(guild=traits["guild"].str.split(",")).explode("guild")
    traits["guild"] = traits["guild"].str.strip()
    traits["guild"] = traits["guild"].str.capitalize()

    # Rename blanks and 'Unknown' (from initial data or failed imputation) to "Unknown"
    traits["guild"].replace("", "Unknown", inplace=True)

    # Determine relative guild membership (pivot and normalize)
    traits["value"] = 1

    # Group by species and guild, sum the values, then calculate proportion
    traits_grouped = traits.groupby(["species", "guild"])["value"].sum().reset_index()
    traits_grouped["value"] = traits_grouped["value"] / traits_grouped.groupby(
        "species"
    )["value"].transform("sum")

    # filter species in response

    traits_grouped = traits_grouped[
        traits_grouped["species"].isin(response["species"])
    ].reset_index()

    # Pivot to get guilds as columns
    traits_pivot = traits_grouped.pivot_table(
        index="species", columns="guild", values="value", fill_value=0
    ).reset_index()

    return traits_pivot


# main function


def clean_data():
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    individuals = clean_individuals()
    observations = clean_observations()
    predators = clean_predators()
    sites = clean_sites()
    plots = clean_plots()
    benthic_classes = clean_benthic_cover()
    rug, rugosity = clean_rugosity()
    behaviours = metadata()
    abundance = calc_abn(individuals, predators)
    abundance_size = calc_abn_size(individuals, predators)
    predictors = create_predictors(sites, rug, benthic_classes, abundance)
    samples = clean_samples()
    response = create_response(individuals, observations, behaviours, samples)
    guilds = clean_guilds(response)

    print("Data cleaning complete\n")

    return {
        "individuals": individuals,
        "observations": observations,
        "predators": predators,
        "sites": sites,
        "plots": plots,
        "benthic_classes": benthic_classes,
        "rugosity": rugosity,
        "abundance": abundance,
        "abundance_size": abundance_size,
        "predictors": predictors,
        "response": response,
        "guilds": guilds,
    }


if __name__ == "__main__":
    state = clean_data()
    if state == 1:
        print("Data cleaning failed")
