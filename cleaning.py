import pandas as pd
import numpy as np
import os

# Clean individual level data

os.makedirs("outputs/data", exist_ok=True)


def clean_individuals():
    """
    Clean individual level data
    """
    individuals = pd.read_csv("data/individuals.csv")
    individuals.columns = individuals.columns.str.lower()
    individuals.columns = individuals.columns.str.replace("-", "_")

    individuals["group"] = pd.Categorical(
        individuals["group"], categories=["no", "yes"], ordered=True
    )
    individuals["group"] = individuals["group"].cat.codes
    individuals.loc[individuals["group"] < 0, "group"] = 0

    # calculate observed duration

    individuals["observed_duration"] = individuals["time_out"].astype(
        float
    ) - individuals["time_in"].astype(float)

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

    return observations


# Clean predators data
def clean_predators():
    predators = pd.read_csv("data/predators.csv")
    predators.columns = predators.columns.str.lower()
    predators.columns = predators.columns.str.replace("-", "_")

    predators.rename(columns={"index": "predator_id"}, inplace=True)

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

    return sites


def clean_plots():
    plots = pd.read_csv("data/plots.csv")

    plots.rename(columns={"index": "plot_id"}, inplace=True)
    return plots


# Clearn samples data


def clean_samples():
    """
    Clean samples data
    """
    samples = pd.read_csv("data/samples.csv")
    samples.rename(columns={"plot": "plot_id", "sample": "sample_id"}, inplace=True)

    return samples


# Clean benthic cover data
def clean_benthic_cover():
    benthic_cover = pd.read_csv("data/benthic-cover.csv")
    benthic_cover["name"] = benthic_cover["name"].str.replace(".png", "")
    benthic_cover["name"] = benthic_cover["name"].str.replace(r"_Q\d_", "_", regex=True)

    benthic_cover.rename(columns={"name": "plot_id"}, inplace=True)

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
    #    sizes = pd.read_csv("data/sizes.csv")

    return behaviours


# Data cleaning and standardisation
print("Cleaned and standardised data")
print("=====================================")
print("\n\n")

## Predictors

# create a predictors data frame, drop unnecessary variables from sites


def create_predictors(sites, rug, benthic_classes, abundance):
    predictors = sites.drop(
        columns=["date", "time_in", "time_out", "lat", "lon", "crew", "remarks"]
    )

    predictors = predictors.merge(rug, how="left", on="deployment_id")

    predictors = predictors.merge(benthic_classes, how="left", on="plot_id")

    predictors["treatment"] = predictors["plot_id"].str.split("_").str[1]

    # Ensure all plot_ids are present, fill missing predator abundance with zero
    predators = abundance[abundance["guild"] == "Piscivore"]
    all_plot_ids = predictors["plot_id"].unique()
    # Ensure unique plot_id by aggregating (sum abundance per plot_id)
    predators = (
        predators.groupby("plot_id", as_index=False)["abundance"]
        .sum()
        .set_index("plot_id")
        .reindex(all_plot_ids, fill_value=0)
        .reset_index()
    )
    predators["abundance"] = predators["abundance"].fillna(0)

    predictors["predator"] = np.array(
        [1 if x > 0 else 0 for x in predators["abundance"].values]
    )

    print("Predictors data")
    print("=====================================")

    print("First 10 rows:\n")
    print(predictors.head(10))

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

    print(individuals.head())

    abundance = (
        individuals[["ind_id", "plot_id", "guild"]]
        .groupby(["plot_id", "guild"])
        .size()
        .reset_index(name="abundance")
    )

    predators["plot_id"] = (
        predators["predator_id"].str.split("_").str[1]
        + "_"
        + predators["predator_id"].str.split("_").str[2]
    )

    predators["guild"] = "Piscivore"

    # Add predator abundance as "Piscivore" guild for each plot
    predator_abundance = (
        predators.groupby("plot_id").size().reset_index(name="abundance")
    )
    predator_abundance["guild"] = "Piscivore"

    # Combine prey and predator abundance
    abundance = pd.concat([abundance, predator_abundance], ignore_index=True)

    abundance.to_csv("outputs/data/abundance.csv", index=False)

    return abundance


def calc_abn_size(individuals, predators):
    individuals["plot_id"] = (
        individuals["ind_id"].str.split("_").str[0]
        + "_"
        + individuals["ind_id"].str.split("_").str[1]
    )

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
    individuals["plot_id"] = (
        individuals["ind_id"].str.split("_").str[0]
        + "_"
        + individuals["ind_id"].str.split("_").str[1]
    )

    response = individuals[
        [
            "plot_id",
            "ind_id",
            "species",
            "guild",
            "group",
            "size_class",
            "observed_duration",
        ]
    ].copy()

    # extract family for each species from traits

    traits = pd.read_csv("data/traits.csv")

    families = traits[["Family", "Genus", "Species"]].copy()

    families["Species"] = (
        families["Genus"].str.strip() + " " + families["Species"].str.strip()
    )

    families = families[["Family", "Species"]].copy()

    families.columns = ["family", "species"]

    # add behavioural observations

    ind_beh = transform_behaviours(observations, behaviours, samples)

    ind_beh.fillna(0, inplace=True)

    response = response.merge(ind_beh, how="left", on="ind_id")

    response.rename(columns={"feeding": "foraging", "moving": "movement"}, inplace=True)
    response.rename(columns={"bite_count": "bites"}, inplace=True)

    # calculate bite rates

    response["bites"] = response["bites"] / response["foraging"]

    # convert observed duration to seconds

    response["observed_duration"] = response["observed_duration"] / 1000

    # fix negative observed durations

    # fix observed durations that are greater than total behaviours

    response["total_behaviour"] = (
        response["foraging"] + response["movement"] + response["vigilance"]
    )
    response.loc[
        (response["observed_duration"] < response["total_behaviour"]),
        "observed_duration",
    ] = response["total_behaviour"]

    response.drop(columns=["total_behaviour"], inplace=True)

    # covert time to proportion of observed

    response["foraging"] = (
        response["foraging"] / response["observed_duration"]
    ).astype(float)
    response["movement"] = (
        response["movement"] / response["observed_duration"]
    ).astype(float)
    response["vigilance"] = (
        response["vigilance"] / response["observed_duration"]
    ).astype(float)

    response.loc[response["species"] == "", "species"] = "Unknown"

    # add families

    response = response.merge(families, how="left", on="species")

    print("\n\n")
    print("Behavioural response data")
    print("=====================================")
    print("First 10 rows:\n")
    print(response.head(10))

    response.to_csv("outputs/data/response.csv", index=False)

    return response


# clean trait data


def clean_guilds():
    """
    Cleans the guild data by filling in missing values based on genus and family.

    Args:
        response (pd.DataFrame): The input DataFrame containing species data.

    Returns:
        pd.DataFrame: The cleaned and imputed DataFrame with relative guild memberships.
    """

    # Load and preprocess traits data
    traits = pd.read_csv("data/traits.csv")

    traits.columns = traits.columns.str.lower()
    traits = traits[["family", "genus", "species", "feeding.guild"]].copy()
    traits.columns = ["family", "genus", "species", "guild"]

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
    traits.drop(columns=["genus"], inplace=True)

    # Split multiple guilds into separate rows and clean
    traits["guild"] = traits["guild"].fillna("").astype(str)  # Ensure guild is string
    traits = traits.assign(guild=traits["guild"].str.split(",")).explode("guild")
    traits["guild"] = traits["guild"].str.strip()
    traits["guild"] = traits["guild"].str.capitalize()

    # Rename blanks and 'Unknown' (from initial data or failed imputation) to "Unknown"
    traits["guilds"] = traits["guild"].replace("", "Unknown")

    # Determine relative guild membership (pivot and normalize)
    traits["value"] = 1

    # Group by species and guild, sum the values, then calculate proportion
    traits_grouped = (
        traits.groupby(["family", "species", "guild"])["value"].sum().reset_index()
    )
    traits_grouped["value"] = traits_grouped["value"] / traits_grouped.groupby(
        "species"
    )["value"].transform("sum")

    # Pivot to get guilds as columns
    traits_pivot = traits_grouped.pivot_table(
        index="species", columns="guild", values="value", fill_value=0
    ).reset_index()

    print(traits_pivot.head(10))
    return traits_pivot


def ind_traits(individuals, guilds):
    """
    Create a table with individual id, species, size class, and foraging guild.
    Foraging guild is assigned as the guild with the highest value for each species.
    """
    # Find the dominant guild for each species
    guilds_long = guilds.set_index("species").stack().reset_index()
    guilds_long.columns = ["species", "guild", "value"]
    dominant_guild = guilds_long.loc[guilds_long.groupby("species")["value"].idxmax()]
    dominant_guild = dominant_guild[["species", "guild"]]

    # Merge with individuals
    table = individuals[
        [
            "ind_id",
            "species",
            "group",
            "size_class",
            "observed_duration",
        ]
    ].copy()
    table = table.merge(dominant_guild, how="left", on="species")

    table.to_csv("outputs/data/individual_traits.csv", index=False)

    return table


# main function


def clean_data():
    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    individuals = clean_individuals()
    observations = clean_observations()
    behaviours = metadata()
    samples = clean_samples()
    guilds = clean_guilds()
    individuals_guild = ind_traits(individuals, guilds)
    response = create_response(individuals_guild, observations, behaviours, samples)

    predators = clean_predators()
    abundance = calc_abn(individuals_guild, predators)
    abundance_size = calc_abn_size(individuals, predators)

    sites = clean_sites()
    plots = clean_plots()
    benthic_classes = clean_benthic_cover()
    rug, rugosity = clean_rugosity()
    predictors = create_predictors(sites, rug, benthic_classes, abundance)

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
