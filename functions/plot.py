import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# set the plot style
sns.set_theme(style="white", palette="pastel")
az.style.use("arviz-whitegrid")

# Bayesian model diagnostics and plotting functions


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


# Counterfactual treatment plots


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


# counterfactual treatment x protection plots


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
