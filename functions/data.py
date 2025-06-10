# load the data


def load_data(model="test"):
    if model == "test":
        dirs = [
            "outputs/simulation/generated_data_predictors.csv",
            "outputs/simulation/generated_data_response.csv",
            "outputs/model/generated/",
            "outputs/simulation/generated_data_rugosity.csv",
            "figures/generative/",
        ]
    else:
        dirs = [
            "outputs/data/predictors.csv",
            "outputs/data/response.csv",
            "outputs/model/data/",
            "outputs/data/rugosity.csv",
            "figures/",
        ]

    return dirs


# Prepare Stan data


def prep_stan(predictors, response, rugosity):
    stan_data = {
        "N": len(response),
        "T": len(predictors["treatment"].unique()),
        "P": predictors["protection"].nunique(),
        "S": predictors["plot_id"].nunique(),
        "C": max(response["size_class"]) + 1,
        "G": max(response["guild"]) + 1,
        "K": max(response["species"]),
        "B": 3,
        "D": response[["foraging", "vigilance", "movement"]].values,
        "bites": response["bites"].astype("int").values,
        "plot": response["plot_id"].values,
        "species": response["species"].values + 1,
        "protection": predictors["protection"].values + 1,
        "predator": predictors["predator"].values + 1,
        "rugosity_raw": rugosity[["sample_1", "sample_2", "sample_3"]].values,
        "biomass": predictors["biomass"].values,
        "treatment": predictors["treatment"].values + 1,
        "size": response["size_class"].values + 1,
        "guild": response["guild"].values + 1,
    }

    return stan_data
