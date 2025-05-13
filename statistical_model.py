from cmdstanpy import CmdStanModel

# from cmdstanpy import install_cmdstan
import pandas as pd
import arviz as az
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Install CmdStan if not already installed
# install_cmdstan()

# set the plot style
sns.set_theme(style="white", palette="pastel")
az.style.use("arviz-whitegrid")

# load the data


def load_data(model="test"):
    if model == "test":
        dirs = [
            "outputs/generated_data_predictors.csv",
            "outputs/generated_data_response.csv",
            "outputs/model/generated/",
            "outputs/generated_data_rugosity.csv",
        ]
    else:
        dirs = [
            "outputs/predictors.csv",
            "outputs/response.csv",
            "outputs/model/data/",
            "outputs/rugosity_raw.csv",
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
        "bites": response["bites"].values,
        "predator": predictors["predator"].values + 1,
        "plot": response["plot_id"].values,
        "rugosity_raw": rugosity[["sample_1", "sample_2", "sample_3"]].values,
        "protection": predictors["protection"].values + 1,
        "treatment": predictors["treatment"].values + 1,
        "biomass": predictors["biomass"].values,
    }

    return stan_data


def load_model(response, output_dir):
    print("Loading samples from existing files...")

    obs = az.from_dict(
        observed_data={
            "D_obs": response["vigilance"].values,
            "bites_obs": response["bites"].values,
        }
    )

    model_data = az.from_cmdstan(
        output_dir + "*.csv",
        posterior_predictive=[
            "D_pred",
            "bites_pred",
            "D_cf",
            "bites_cf",
        ],
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
        # adapt_delta=0.99,
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
        ],
    )

    model_data = az.concat(model_data, obs)

    return model_data


def diagnostic_plots(model_data):
    # traceplot
    print("Creating traceplot...")
    az.plot_trace(
        model_data,
        compact=False,
        var_names=["beta_risk", "beta_pi_risk", "beta_risk_bites", "beta_rug"],
        figsize=(16, 24),
    )

    plt.savefig("figures/generative/traceplot.png", dpi=300)

    # posterior predictive check
    print("Creating posterior predictive check...")
    az.plot_ppc(
        model_data,
        kind="cumulative",
        data_pairs={"D_obs": "D_pred", "bites_obs": "bites_pred"},
        figsize=(10, 6),
    )
    plt.savefig("figures/generative/ppc.png", dpi=300)


def counterfactual_treatments(model_data):
    print("Computing counterfactual treatments...")
    # counterfactual analysis

    D_cf = az.extract(model_data.posterior_predictive, var_names="D_cf")

    D_cf = D_cf.values

    Diff_01 = (D_cf[1,] - D_cf[0,]).mean(axis=2)

    Diff_02 = (D_cf[2,] - D_cf[0,]).mean(axis=2)

    Diff_03 = (D_cf[3,] - D_cf[0,]).mean(axis=2)

    print("Creating counterfactual plots...")

    behavior = ["Foraging", "Vigilance", "Movement"]

    plt.figure(figsize=(24, 6))

    for b in range(3):
        posterior_data = {
            "Positive Control": Diff_01[b, :],
            "Treatment 1": Diff_02[b, :],
            "Treatment 2": Diff_03[b, :],
        }

        posterior_df = pd.DataFrame(posterior_data).melt(
            var_name="Treatment", value_name="Effect"
        )

        plt.subplot(1, 3, b + 1)
        plt.title(f"{behavior[b]}")
        sns.violinplot(
            x="Treatment",
            y="Effect",
            data=posterior_df,
            linewidth=1,
            hue="Treatment",
            palette="pastel",
            alpha=0.5,
        )
        # plt.ylim(-0.2, 0.2)

    plt.savefig("figures/generative/counterfactual_treatment.png", dpi=300)


def main(run=False, chains=4):
    # load data

    print("Loading data...")
    dirs = load_data(model="test")
    predictors = pd.read_csv(dirs[0])
    response = pd.read_csv(dirs[1])
    rugosity = pd.read_csv(dirs[3])

    # prepare data
    stan_data = prep_stan(predictors, response, rugosity)

    # run model or load existing model

    output_dir = dirs[2]

    print("Checking for existing model files...")

    if os.path.exists(output_dir):
        # check if csv file exists

        model_files = []

        for filename in os.listdir(output_dir):
            if filename.endswith(".csv"):
                model_files.append(filename)
    else:
        os.makedirs(output_dir)
        model_files = []

    if not run and len(model_files) == chains:
        model_data = load_model(response, output_dir)
    else:
        model_data = run_model(output_dir, stan_data, response, chains=chains)

    # diagnostic plots

    diagnostic_plots(model_data)

    # counterfactual treatments
    counterfactual_treatments(model_data)

    return 0


if __name__ == "__main__":
    main(run=True, chains=4)
