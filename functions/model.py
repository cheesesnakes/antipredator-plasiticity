import os
import arviz as az
from cmdstanpy import CmdStanModel


def load_model(response, output_dir):
    print("Loading samples from existing files...")

    model_data = az.from_cmdstan(
        output_dir + "*.csv",
        posterior_predictive=[
            "D_pred",
            "bites_pred",
            "D_cf",
            "bites_cf",
            "D_cf_prot",
            "bites_cf_prot",
        ],
    )

    if response is not None:
        obs = az.from_dict(
            observed_data={
                "D_obs": response["vigilance"].values,
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
        adapt_delta=0.99,
    )

    print("Model run complete.")

    print("Diagnosing model...")

    print(fit.diagnose())

    # make arviz data
    print("Creating ArviZ data...")

    obs = az.from_dict(
        observed_data={
            "D_obs": response["vigilance"].values,
            "bites_obs": response["bites"].values,
        }
    )

    model_data = az.from_cmdstanpy(
        fit,
        posterior_predictive=[
            "D_pred",
            "bites_pred",
            "D_cf",
            "bites_cf",
            "D_cf_prot",
            "bites_cf_prot",
        ],
    )

    model_data = az.concat(model_data, obs)

    return model_data
