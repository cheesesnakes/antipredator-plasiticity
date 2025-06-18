import os
import arviz as az
from cmdstanpy import CmdStanModel

# load the data


def load_data(model="test"):
    if model == "test":
        dirs = [
            "outputs/simulation/predictors.csv",
            "outputs/simulation/response.csv",
            "outputs/simulation/rugosity.csv",
            "outputs/simulation/guilds.csv",
            "outputs/model/generated/",
            "figures/generative/",
        ]
    else:
        dirs = [
            "outputs/data/predictors.csv",
            "outputs/data/response.csv",
            "outputs/data/rugosity.csv",
            "outputs/data/guilds.csv",
            "outputs/model/data/",
            "figures/",
        ]

    return dirs


# Prepare Stan data


def prep_stan(predictors, response, rugosity, traits):
    stan_data = {
        "N": len(response),
        "T": len(predictors["treatment"].unique()),
        "P": predictors["protection"].nunique(),
        "S": predictors["plot_id"].nunique(),
        "C": max(response["size_class"]) + 1,
        "G": len(traits.columns) - 1,
        "K": response["species"].nunique(),
        "B": 3,
        "Q": predictors["deployment_id"].nunique(),
        "D": response[["foraging", "vigilance", "movement"]].values,
        "bites": response["bites"].astype("int").values,
        "plot": response["plot_id"].values,
        "deployment": predictors["deployment_id"].values + 1,
        "species": response["species"].values + 1,
        "protection": predictors["protection"].values + 1,
        "predator": predictors["predator"].values + 1,
        "rugosity_raw": rugosity[["sample_1", "sample_2", "sample_3"]].values,
        "biomass": predictors["biomass"].values,
        "treatment": predictors["treatment"].values + 1,
        "size": response["size_class"].values + 1,
        "guild": traits[traits.columns[1:]].values,
        "group": response["group"].values + 1,
    }

    return stan_data


# load the model


def load_model(response, output_dir):
    print("Loading samples from existing files...")

    model_data = az.from_cmdstan(
        output_dir + "*.csv",
        posterior_predictive=[
            "D_pred",
            "bites_pred",
            "D_pred_protection",
            "bites_pred_protection",
        ],
    )

    if response is not None:
        obs = az.from_dict(
            observed_data={
                "D_obs": response[["foraging", "vigilance", "movement"]].values,
                "bites_obs": response["bites"].values,
            }
        )

        model_data = az.concat(model_data, obs)

    return model_data


def run_model(output_dir, stan_data, response, chains=4):
    print("Running model...")

    # compile stan model
    print("Compiling model...")
    model = CmdStanModel(stan_file="model.stan")

    # delete model_files
    print("Running model...")

    for file in os.listdir(output_dir):
        os.remove(output_dir + file)

    if os.path.exists("outputs/effects.csv"):
        os.remove("outputs/effects.csv")

    fit = model.sample(
        data=stan_data,
        chains=chains,
        iter_warmup=1000,
        iter_sampling=1000,
        seed=123,
        parallel_chains=4,
        threads_per_chain=8,
        output_dir=output_dir,
        # max_treedepth=15,
        # adapt_delta=0.99,
    )

    print("Model run complete.")

    print("Diagnosing model...")

    print(fit.diagnose())

    # make arviz data
    print("Creating ArviZ data...")

    obs = az.from_dict(
        observed_data={
            "D_obs": response[["foraging", "vigilance", "movement"]].values,
            "bites_obs": response["bites"].values,
        }
    )

    model_data = az.from_cmdstanpy(
        fit,
        posterior_predictive=[
            "D_pred",
            "bites_pred",
            "D_pred_protection",
            "bites_pred_protection",
        ],
    )

    model_data = az.concat(model_data, obs)

    return model_data
