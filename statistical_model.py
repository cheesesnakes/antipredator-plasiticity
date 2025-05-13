from cmdstanpy import CmdStanModel

# from cmdstanpy import install_cmdstan
import pandas as pd
import numpy as np
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
            "D_cf_prot",
            "bites_cf_prot",
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


def diagnostic_plots(model_data, directory="figures/generative/"):
    # traceplot
    print("Creating traceplot...")
    az.plot_trace(
        model_data,
        compact=False,
        var_names=["beta_risk", "beta_pi_risk", "beta_risk_bites", "beta_rug"],
        figsize=(16, 24),
    )

    plt.savefig(f"{directory}/traceplot.png", dpi=300)

    # posterior predictive check
    print("Creating posterior predictive check...")
    az.plot_ppc(
        model_data,
        kind="cumulative",
        data_pairs={"D_obs": "D_pred", "bites_obs": "bites_pred"},
        figsize=(10, 6),
    )
    plt.savefig(f"{directory}/ppc.png", dpi=300)


def counterfactual_treatments(model_data, directory="figures/generative/"):
    print("Computing counterfactual treatments...")
    # counterfactual analysis

    D_cf = az.extract(model_data.posterior_predictive, var_names="D_cf")

    D_cf = D_cf.values

    Diff_01 = (D_cf[1,] - D_cf[0,]).mean(axis=2)

    Diff_02 = (D_cf[2,] - D_cf[0,]).mean(axis=2)

    Diff_03 = (D_cf[3,] - D_cf[0,]).mean(axis=2)

    bites_cf = az.extract(model_data.posterior_predictive, var_names="bites_cf")

    bites_cf = bites_cf.values

    Diff_bites_01 = (bites_cf[1,] - bites_cf[0,]).mean(axis=0)
    Diff_bites_02 = (bites_cf[2,] - bites_cf[0,]).mean(axis=0)
    Diff_bites_03 = (bites_cf[3,] - bites_cf[0,]).mean(axis=0)

    print("Creating counterfactual plots...")

    behavior = ["Foraging", "Vigilance", "Movement"]

    plt.figure(figsize=(32, 6))

    for b in range(3):
        posterior_data = {
            "Positive Control": Diff_01[b, :],
            "Barracuda": Diff_02[b, :],
            "Grouper": Diff_03[b, :],
        }

        posterior_df = pd.DataFrame(posterior_data).melt(
            var_name="Treatment", value_name="Effect"
        )

        plt.subplot(1, 4, b + 1)
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
        plt.axhline(0, color="black", linestyle="--", linewidth=1)
        # plt.ylim(-0.2, 0.2)

        plt.ylabel("Effect Size")
        plt.xlabel("Treatment")

    # plot the bites
    plt.subplot(1, 4, 4)
    plt.title("Bite Rate")
    posterior_data = {
        "Positive Control": Diff_bites_01,
        "Barracuda": Diff_bites_02,
        "Grouper": Diff_bites_03,
    }
    posterior_df = pd.DataFrame(posterior_data).melt(
        var_name="Treatment", value_name="Effect"
    )

    sns.violinplot(
        x="Treatment",
        y="Effect",
        data=posterior_df,
        linewidth=1,
        hue="Treatment",
        palette="pastel",
        alpha=0.5,
    )
    plt.axhline(0, color="black", linestyle="--", linewidth=1)
    # plt.ylim(-0.2, 0.2)
    plt.ylabel("Effect Size")
    plt.xlabel("Treatment")

    plt.savefig(f"{directory}/counterfactual_treatment.png", dpi=300)


# counterfactual treatment x protection
def counterfactual_treatments_protection(model_data, directory="figures/generative/"):
    print("Computing counterfactual treatments by protection...")

    D_cf_prot = az.extract(
        model_data.posterior_predictive, var_names="D_cf_prot"
    ).values

    Diff_01 = (D_cf_prot[1,] - D_cf_prot[0,]).mean(axis=3)

    Diff_02 = (D_cf_prot[2,] - D_cf_prot[0,]).mean(axis=3)

    Diff_03 = (D_cf_prot[3,] - D_cf_prot[0,]).mean(axis=3)

    bites_cf_prot = az.extract(
        model_data.posterior_predictive, var_names="bites_cf_prot"
    ).values
    Diff_bites_01 = (bites_cf_prot[1,] - bites_cf_prot[0,]).mean(axis=2)
    Diff_bites_02 = (bites_cf_prot[2,] - bites_cf_prot[0,]).mean(axis=2)
    Diff_bites_03 = (bites_cf_prot[3,] - bites_cf_prot[0,]).mean(axis=2)

    print("Creating counterfactual plots...")

    behavior = ["Foraging", "Vigilance", "Movement"]

    plt.figure(figsize=(32, 6))

    for b in range(3):
        posterior_data_out = {
            "Positive Control": Diff_01[0, b, :],
            "Barracuda": Diff_02[0, b, :],
            "Grouper": Diff_03[0, b, :],
            "Protection": np.repeat("Outside PA", Diff_01[0, b, :].shape[0]),
        }
        posterior_df_out = pd.DataFrame(posterior_data_out)

        posterior_data_in = {
            "Positive Control": Diff_01[1, b, :],
            "Barracuda": Diff_02[1, b, :],
            "Grouper": Diff_03[1, b, :],
            "Protection": np.repeat("Inside PA", Diff_01[1, b, :].shape[0]),
        }
        posterior_df_in = pd.DataFrame(posterior_data_in)

        posterior_df = pd.concat([posterior_df_out, posterior_df_in], axis=0)
        posterior_df = posterior_df.melt(
            id_vars=["Protection"], var_name="Treatment", value_name="Effect"
        )
        posterior_df["Protection"] = posterior_df["Protection"].astype("category")
        posterior_df["Treatment"] = posterior_df["Treatment"].astype("category")
        posterior_df["Protection"] = posterior_df["Protection"].cat.reorder_categories(
            ["Inside PA", "Outside PA"], ordered=True
        )

        plt.subplot(1, 4, b + 1)
        plt.title(f"{behavior[b]}")
        sns.violinplot(
            x="Treatment",
            y="Effect",
            data=posterior_df,
            linewidth=1,
            hue="Protection",
            palette="pastel",
            split=True,
            alpha=0.5,
        )
        plt.axhline(0, color="black", linestyle="--", linewidth=1)
        # plt.ylim(-0.2, 0.2)

        plt.ylabel("Effect Size")
        plt.xlabel("Treatment")

    # plot the bites
    posterior_data_out = {
        "Positive Control": Diff_bites_01[0, :],
        "Barracuda": Diff_bites_02[0, :],
        "Grouper": Diff_bites_03[0, :],
        "Protection": np.repeat("Outside PA", Diff_bites_01[0, :].shape[0]),
    }
    posterior_df_out = pd.DataFrame(posterior_data_out)
    posterior_data_in = {
        "Positive Control": Diff_bites_01[1, :],
        "Barracuda": Diff_bites_02[1, :],
        "Grouper": Diff_bites_03[1, :],
        "Protection": np.repeat("Inside PA", Diff_bites_01[1, :].shape[0]),
    }
    posterior_df_in = pd.DataFrame(posterior_data_in)
    posterior_df = pd.concat([posterior_df_out, posterior_df_in], axis=0)
    posterior_df = posterior_df.melt(
        id_vars=["Protection"], var_name="Treatment", value_name="Effect"
    )
    posterior_df["Protection"] = posterior_df["Protection"].astype("category")
    posterior_df["Treatment"] = posterior_df["Treatment"].astype("category")
    posterior_df["Protection"] = posterior_df["Protection"].cat.reorder_categories(
        ["Inside PA", "Outside PA"], ordered=True
    )
    plt.subplot(1, 4, 4)
    plt.title("Bite Rate")
    sns.violinplot(
        x="Treatment",
        y="Effect",
        data=posterior_df,
        linewidth=1,
        hue="Protection",
        palette="pastel",
        split=True,
        alpha=0.5,
    )
    plt.axhline(0, color="black", linestyle="--", linewidth=1)
    # plt.ylim(-0.2, 0.2)
    plt.ylabel("Effect Size")
    plt.xlabel("Treatment")
    plt.legend(title="Protection", loc="upper right")
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.3)

    plt.savefig(f"{directory}/counterfactual_treatment_protection.png", dpi=300)


def main(model="test", run=False, chains=4):
    # load data

    print("Loading data...")
    dirs = load_data(model=model)
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

    if run:
        diagnostic_plots(model_data, directory=dirs[4])

    # counterfactual treatments

    counterfactual_treatments(model_data, directory=dirs[4])

    # counterfactual treatments by protection

    counterfactual_treatments_protection(model_data, directory=dirs[4])

    return 0


if __name__ == "__main__":
    main(model="data", run=True, chains=4)
