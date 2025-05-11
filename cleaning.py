import pandas as pd
import numpy as np

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


# Clearn individual level data

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

# clean observations data

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

# Clean predators data
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

# Plot level data

sites.columns = sites.columns.str.lower()
sites.columns = sites.columns.str.replace("-", "_")

print("Sites data")
print("=====================================")
print("Columns:\n")
print(sites.columns)
print("First 10 rows:\n")
print(sites.head(10))

plots.rename(columns={"index": "plot_id"}, inplace=True)

print("Plots data")
print("=====================================")
print("Columns:\n")
print(plots.columns)
print("First 10 rows:\n")
print(plots.head(10))
print("Summary:\n")
print(plots.describe(include="all"))

# Clearn samples data
samples.rename(columns={"plot": "plot_id", "sample": "sample_id"}, inplace=True)

print("Samples data")
print("=====================================")
print("Columns:\n")
print(samples.columns)
print("First 10 rows:\n")
print(samples.head(10))
print("Summary:\n")
print(samples.describe(include="all"))

# Clean benthic cover data

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

# Clean rugosity data
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

## Metadata

print(r"""Ethogram with descriptions of observed behaviour:\n""")
behaviours

print(r"""Size classes used to classify fish size:\n""")
sizes

print("Cleaned and standardised data")
print("=====================================")
# Data cleaning and standardisation

## Predictors

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

# raw rugosity data

rugosity.drop(
    columns=["deployment_id", "treatment", "measured_length_cm"], inplace=True
)
rugosity = rugosity.pivot(
    index="plot_id", columns="sample", values="rugosity"
).reset_index()
rugosity.rename(columns={1: "sample_1", 2: "sample_2", 3: "sample_3"}, inplace=True)

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
    label: category for category, labels in benthic_classes.items() for label in labels
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

predictors = predictors.merge(benthic_classes, how="left", on="plot_id")

predictors["treatment"] = predictors["plot_id"].str.split("_").str[1]

print("Predictors data")
print("=====================================")
print("Columns:\n")
print(predictors.columns)
print("First 10 rows:\n")
print(predictors.head(10))
print("Summary:\n")
print(predictors.describe(include="all"))

## Response variables

### Plot - level

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

predictors["predator"] = np.array(
    [1 if x > 0 else 0 for x in abundance["n_predators"].values]
)

print("Plot level abundance data")
print("=====================================")
print("Columns:\n")
print(abundance.columns)
print("First 10 rows:\n")
print(abundance.head(10))
print("Summary:\n")
print(abundance.describe(include="all"))

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

### Individual level response

response = individuals[["plot_id", "ind_id", "species", "size_class"]].copy()

# add behavioural observations


def calculate_duration(df):
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


def transform_behaviours():
    data = pd.DataFrame({"ind_id": observations["ind_id"].unique()})

    for index, row in behaviours.iterrows():
        df = observations[observations["behaviour"] == row["name"]]

        if row["type"] == "Event":
            col = row["name"].lower() + "_" + "count"

            df = df.groupby("ind_id").size().reset_index(name=col)

        elif row["type"] == "State":
            df = calculate_duration(df)

            df = df[["ind_id", "behaviour", "duration"]]

            df = df.pivot(
                index="ind_id", columns="behaviour", values="duration"
            ).reset_index()

        df.columns = df.columns.str.lower()
        df.columns = df.columns.str.replace("-", "_")
        df.columns = df.columns.str.replace(" ", "_")

        data = data.merge(df, how="left", on="ind_id")

    return data


ind_beh = transform_behaviours()

ind_beh.fillna(0, inplace=True)

response = response.merge(ind_beh, how="left", on="ind_id")

response
response.rename(columns={"feeding": "foraging", "moving": "movement"}, inplace=True)

print("Behavioural response data")
print("=====================================")
print("Columns:\n")
print(response.columns)
print("First 10 rows:\n")
print(response.head(10))
print("Summary:\n")
print(response.describe(include="all"))

# make dummy variables for categorical variables

data = [predictors, abundance, abundance_size, response, rugosity]

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
    "treatment": np.sort(predictors["treatment"].unique()),
    "plot_id": np.sort(predictors["plot_id"].unique()),
    "location": np.sort(predictors["location"].unique()),
    "protection": np.sort(predictors["protection"].unique())[::-1],  # reverse order
    "ind_id": np.sort(individuals["ind_id"].unique()),
    "species": np.sort(individuals["species"].unique()),
    "size_class": np.sort(individuals["size_class"].unique()),
}


# convert categorical variables to codes

for name, df in zip(
    ["predictors", "abundance", "abundance_size", "response", "rugosity"], data
):
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
        break  # break outer loop too
    else:
        print(f"All values in '{name}' are as expected\n")

for df in data:
    for col in df.columns:
        if col in categoricals:
            df[col] = pd.Categorical(
                df[col], categories=order_categoricals[col], ordered=True
            )
            df[col] = df[col].cat.codes

            if col == "plot_id":
                df[col] += 1  # > 0

# save data

predictors.to_csv("outputs/predictors.csv", index=False)
rugosity.to_csv("outputs/rugosity_raw.csv", index=False)
abundance.to_csv("outputs/abundance.csv", index=False)
abundance_size.to_csv("outputs/abundance_size.csv", index=False)
response.to_csv("outputs/response.csv", index=False)
