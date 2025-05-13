# load the data


def load_data(model="test"):
    if model == "test":
        dirs = [
            "outputs/generated_data_predictors.csv",
            "outputs/generated_data_response.csv",
            "outputs/model/generated/",
            "outputs/generated_data_rugosity.csv",
            "figures/generative/",
        ]
    else:
        dirs = [
            "outputs/predictors.csv",
            "outputs/response.csv",
            "outputs/model/data/",
            "outputs/rugosity_raw.csv",
            "figures/",
        ]

    return dirs


# Prepare Stan data


def prep_stan(predictors, response, rugosity):
    stan_data = {
        "N": len(response),
        "T": len(predictors["treatment"].unique()),
        "B": 3,
        "P": predictors["protection"].nunique(),
        "S": predictors["plot_id"].nunique(),
        "D": response[["foraging", "vigilance", "movement"]].values,
        "bites": response["bites"].astype("int").values,
        "predator": predictors["predator"].values + 1,
        "plot": response["plot_id"].values,
        "rugosity_raw": rugosity[["sample_1", "sample_2", "sample_3"]].values,
        "protection": predictors["protection"].values + 1,
        "treatment": predictors["treatment"].values + 1,
        "biomass": predictors["biomass"].values,
    }

    return stan_data
