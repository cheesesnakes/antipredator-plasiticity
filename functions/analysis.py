import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import os
import json

# set the plot style
sns.set_theme(style="white", palette="pastel")
az.style.use("arviz-whitegrid")

# Bayesian model diagnostics and plotting functions


def diagnostics(model_data, directory="figures/generative/"):
    if not os.path.exists(directory):
        os.makedirs(directory)

    # traceplot
    print("Creating traceplot...")
    az.plot_trace(
        model_data,
        compact=False,
        var_names=["theta_pi", "theta_D", "theta_bites", "beta_D"],
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


# Effect of treatment on behaviour


def effects_treatment(response, directory="figures/"):
    # Calculate effect size as log-fold change
    effect_treatment = np.stack(
        [
            response[:, 3, :] - response[:, 0, :],
            response[:, 2, :] - response[:, 0, :],
            response[:, 1, :] - response[:, 0, :],
        ],
        axis=1,
    )

    # calculate mean across individuals and protection levels
    effect_treatment = np.mean(effect_treatment, axis=0)
    effect_treatment = np.mean(effect_treatment, axis=1)

    # create a DataFrame for plotting
    df_effect = pd.DataFrame(
        {
            "Treatment": np.repeat(
                ["Grouper", "Barracuda", "Positive Control"], 4 * 4000
            ),
            "Behaviour": np.tile(
                np.repeat(["Foraging", "Vigilance", "Movement", "Bites"], 4000), 3
            ),
            "Draw": np.tile(np.arange(4000), 3 * 4),
            "effect": effect_treatment.flatten(),
        }
    )

    # Summarise the effect size
    summary_effect = (
        df_effect.groupby(["Treatment", "Behaviour"])["effect"]
        .agg(
            Mean="mean",
            Median="median",
            p5=lambda x: x.quantile(0.05),
            p25=lambda x: x.quantile(0.25),
            p75=lambda x: x.quantile(0.75),
            p95=lambda x: x.quantile(0.95),
        )
        .reset_index()
    )

    # Calculate P(> 0)
    test_effects = (
        df_effect.groupby(["Treatment", "Behaviour"])["effect"]
        .apply(lambda x: np.mean(x > 0))
        .reset_index(name="P(> 0)")
    )

    # Merge summaries
    summary_effect = summary_effect.merge(test_effects, on=["Treatment", "Behaviour"])

    # Reorder and rename columns for readability
    summary_effect.rename(
        columns={"p5": "5th", "p25": "25th", "p75": "75th", "p95": "95th"},
        inplace=True,
    )

    # save as csv

    summary_effect.to_csv("outputs/analysis/summary_effects_treatment.csv", index=False)

    # --- Compare Effects Table ---

    compare_effects = df_effect.pivot_table(
        index=["Draw", "Behaviour"],
        columns="Treatment",
        values="effect",
        aggfunc="mean",
    ).reset_index()

    compare_effects = (
        compare_effects.groupby("Behaviour")
        .apply(
            lambda x: pd.Series(
                {
                    "Grouper > Barracuda": np.mean(x["Grouper"] > x["Barracuda"]),
                    "Grouper > Positive Control": np.mean(
                        x["Grouper"] > x["Positive Control"]
                    ),
                    "Barracuda > Positive Control": np.mean(
                        x["Barracuda"] > x["Positive Control"]
                    ),
                }
            )
        )
        .reset_index()
    )

    # save as csv
    compare_effects.to_csv(
        "outputs/analysis/compare_effects_treatment.csv", index=False
    )

    # plot the effect size

    print("\nPlotting effect size...\n")
    plt.figure(figsize=(10, 6))

    # make ridgeplot
    sns.boxplot(
        x="Behaviour",
        y="effect",
        hue="Treatment",
        data=df_effect,
        palette="pastel",
        width=0.5,
        gap=0.1,
        whis=(5, 95),
        showfliers=False,
    )

    plt.axhline(0, color="black", linestyle="--", linewidth=1)
    plt.ylabel("Effect size (log-fold change)")
    plt.xlabel("Behaviour")
    plt.legend(title="Treatment", loc="upper right")
    plt.savefig(f"{directory}/effects_treatment.png", dpi=300)
    plt.close()


# difference in response across protection levels


def response_protection(response, directory="figures/"):
    # Calculate log-fold change across treatments
    response_diff = np.stack(
        [
            response[:, 3, :] - response[:, 0, :],
            response[:, 2, :] - response[:, 0, :],
            response[:, 1, :] - response[:, 0, :],
        ],
        axis=1,
    )

    # calculate mean across individuals and protection levels
    response_diff = np.mean(response_diff, axis=2)

    # Ensure correct shape assumption

    try:
        assert response_diff.shape == (2, 3, 4, 4000)
    except AssertionError:
        print("Warning: response_diff shape is not as expected.")
        print(f"Expected shape: (2, 3, 4, 4000), but got {response_diff.shape}")

    # Label axes
    protection_levels = ["Outside PA", "Inside PA"]
    treatments = ["Grouper", "Barracuda", "Positive Control"]
    behaviours = ["Foraging", "Vigilance", "Movement", "Bites"]
    n_draws = 4000

    # Create DataFrame
    df_response = pd.DataFrame(
        {
            "Protection Level": np.repeat(protection_levels, 3 * 4 * n_draws),
            "Treatment": np.tile(np.repeat(treatments, 4 * n_draws), 2),
            "Behaviour": np.tile(np.repeat(behaviours, n_draws), 2 * 3),
            "Draw": np.tile(np.arange(n_draws), 2 * 3 * 4),
            "Response": response_diff.flatten(),
        }
    )

    # Summarise the response
    summary_response = (
        df_response.groupby(["Treatment", "Protection Level", "Behaviour"])["Response"]
        .agg(
            Mean="mean",
            Median="median",
            p5=lambda x: x.quantile(0.05),
            p25=lambda x: x.quantile(0.25),
            p75=lambda x: x.quantile(0.75),
            p95=lambda x: x.quantile(0.95),
        )
        .reset_index()
    )

    # Calculate P(> 0)
    test_response = (
        df_response.groupby(["Treatment", "Protection Level", "Behaviour"])["Response"]
        .apply(lambda x: np.mean(x > 0))
        .reset_index(name="P(> 0)")
    )

    # Merge summaries
    summary_response = summary_response.merge(
        test_response, on=["Treatment", "Protection Level", "Behaviour"]
    )

    # Reorder and rename columns for readability
    summary_response.rename(
        columns={"p5": "5th", "p25": "25th", "p75": "75th", "p95": "95th"},
        inplace=True,
    )

    # save as csv
    summary_response.to_csv(
        "outputs/analysis/summary_response_protection.csv", index=False
    )

    # --- Compare Responses Table ---
    compare_response = df_response.pivot_table(
        index=["Draw", "Behaviour"],
        columns=["Protection Level", "Treatment"],
        values="Response",
        aggfunc="mean",
    ).reset_index()

    compare_response = (
        compare_response.groupby("Behaviour")
        .apply(
            lambda x: pd.Series(
                {
                    "Outside PA > Inside PA (Grouper)": np.mean(
                        x["Outside PA"]["Grouper"] > x["Inside PA"]["Grouper"]
                    ),
                    "Outside PA > Inside PA (Barracuda)": np.mean(
                        x["Outside PA"]["Barracuda"] > x["Inside PA"]["Barracuda"]
                    ),
                    "Outside PA > Inside PA (Positive Control)": np.mean(
                        x["Outside PA"]["Positive Control"]
                        > x["Inside PA"]["Positive Control"]
                    ),
                }
            )
        )
        .reset_index()
    )

    # save as csv
    compare_response.to_csv(
        "outputs/analysis/compare_response_protection.csv", index=False
    )

    # plot the difference in response across protection levels
    print("\nPlotting difference in response across protection levels...\n")

    plt.figure(figsize=(10, 6))

    # Create the faceted violin plot
    g = sns.catplot(
        x="Treatment",
        y="Response",
        hue="Protection Level",
        col="Behaviour",
        kind="box",
        data=df_response,
        palette="pastel",
        height=4,
        aspect=1.2,
        width=0.5,
        sharey=False,
        legend="full",
        whis=(5, 95),
        showfliers=False,
        gap=0.1,
    )

    # Add horizontal line at y = 0 to each facet
    for ax in g.axes.flat:
        ax.axhline(0, color="black", linestyle="--", linewidth=1)

    # Set titles and labels
    g.set_titles("{col_name}")
    g.set_axis_labels("Treatment", "Log-fold change")

    # Adjust legend
    g._legend.set_title("Protection Level")

    # Save figure
    g.figure.savefig(
        f"{directory}/response_protection.png", dpi=300, bbox_inches="tight"
    )

    # Close to prevent display in non-interactive environments
    plt.close()


# response to treatments across size classes
def response_size(response, directory="figures/"):
    # Calculate log-fold change across treatments
    response_size = np.stack(
        [
            response[:, 3, :] - response[:, 0, :],
            response[:, 2, :] - response[:, 0, :],
            response[:, 1, :] - response[:, 0, :],
        ],
        axis=1,
    )
    assert response_size.shape == (2, 3, 432, 4, 4000), (
        "response_size shape is not as expected. Expected (2, 3, 432, 4, 4000), but got",
        response_size.shape,
    )

    # load individual traits

    individual_traits = pd.read_csv("outputs/data/individual_traits.csv", index_col=0)
    if "ind_id" not in individual_traits.columns:
        individual_traits = individual_traits.reset_index()

    # load order of categories
    order_categories = json.load(open("outputs/data/order_categoricals.json", "r"))

    # code ind_id using the order of categories
    individual_traits["ind_id"] = pd.Categorical(
        individual_traits["ind_id"],
        categories=order_categories["ind_id"],
        ordered=True,
    )
    individual_traits["ind_id"] = individual_traits["ind_id"].cat.codes

    n_prot, n_treat, n_ind, n_behav, n_draw = response_size.shape

    df_response_size = pd.DataFrame(
        {
            "Protection Level": np.repeat(
                ["Outside PA", "Inside PA"], n_treat * n_ind * n_behav * n_draw
            ),
            "Treatment": np.tile(
                np.repeat(
                    ["Grouper", "Barracuda", "Positive Control"],
                    n_ind * n_behav * n_draw,
                ),
                n_prot,
            ),
            "ind_id": np.tile(
                np.repeat(individual_traits["ind_id"], n_behav * n_draw),
                n_prot * n_treat,
            ),
            "Behaviour": np.tile(
                np.repeat(["Foraging", "Vigilance", "Movement", "Bites"], n_draw),
                n_prot * n_treat * n_ind,
            ),
            "Draw": np.tile(np.arange(n_draw), n_prot * n_treat * n_ind * n_behav),
            "Response": response_size.flatten(),
        }
    )

    # Merge with individual traits
    df_response_size = df_response_size.merge(
        individual_traits[["ind_id", "size_class"]], on="ind_id", how="left"
    )

    # Summarise the response size
    summary_response_size = (
        df_response_size.groupby(
            ["Treatment", "Protection Level", "Behaviour", "size_class"]
        )["Response"]
        .agg(
            Mean="mean",
            Median="median",
            p5=lambda x: x.quantile(0.05),
            p25=lambda x: x.quantile(0.25),
            p75=lambda x: x.quantile(0.75),
            p95=lambda x: x.quantile(0.95),
        )
        .reset_index()
    )
    # Calculate P(> 0)
    test_response_size = (
        df_response_size.groupby(
            ["Treatment", "Protection Level", "Behaviour", "size_class"]
        )["Response"]
        .apply(lambda x: np.mean(x > 0))
        .reset_index(name="P(> 0)")
    )

    # Merge summaries
    summary_response_size = summary_response_size.merge(
        test_response_size,
        on=["Treatment", "Protection Level", "Behaviour", "size_class"],
    )

    # Reorder and rename columns for readability
    summary_response_size.rename(
        columns={"p5": "5th", "p25": "25th", "p75": "75th", "p95": "95th"},
        inplace=True,
    )

    # save as csv
    summary_response_size.to_csv(
        "outputs/analysis/summary_response_size.csv", index=False
    )

    # --- Compare Responses Table ---
    compare_response_size = df_response_size.pivot_table(
        index=["Draw", "Behaviour", "size_class"],
        columns=["Protection Level", "Treatment"],
        values="Response",
        aggfunc="mean",
    ).reset_index()

    compare_response_size = (
        compare_response_size.groupby(["Behaviour", "size_class"])
        .apply(
            lambda x: pd.Series(
                {
                    "Outside PA > Inside PA (Grouper)": np.mean(
                        x["Outside PA"]["Grouper"] > x["Inside PA"]["Grouper"]
                    ),
                    "Outside PA > Inside PA (Barracuda)": np.mean(
                        x["Outside PA"]["Barracuda"] > x["Inside PA"]["Barracuda"]
                    ),
                    "Outside PA > Inside PA (Positive Control)": np.mean(
                        x["Outside PA"]["Positive Control"]
                        > x["Inside PA"]["Positive Control"]
                    ),
                }
            )
        )
        .reset_index()
    )

    # save as csv
    compare_response_size.to_csv(
        "outputs/analysis/compare_response_size.csv", index=False
    )

    # plot the difference in response across size classes
    print("\nPlotting difference in response across size classes...\n")
    plt.figure(figsize=(10, 6))
    # Create the faceted violin plot
    g = sns.catplot(
        x="size_class",
        y="Response",
        hue="Protection Level",
        col="Behaviour",
        row="Treatment",
        kind="box",
        data=df_response_size,
        palette="pastel",
        height=4,
        aspect=1.2,
        width=0.5,
        legend="full",
        showfliers=False,
        whis=(5, 95),
        gap=0.1,
    )
    # Add horizontal line at y = 0 to each facet
    for ax in g.axes.flat:
        ax.axhline(0, color="black", linestyle="--", linewidth=1)
    # Set titles and labels
    g.set_titles("{row_name} | {col_name}")
    g.set_axis_labels("Size Class", "Log-fold change")
    # Adjust legend
    g._legend.set_title("Protection Level")
    # Save figure
    g.figure.savefig(f"{directory}/response_size.png", dpi=300, bbox_inches="tight")
    # Close to prevent display in non-interactive environments
    plt.close()


# response to treatments across guilds


def response_guild(response, directory="figures/"):
    # Calculate log-fold change across treatments
    response_guild = np.stack(
        [
            response[:, 3, :] - response[:, 0, :],
            response[:, 2, :] - response[:, 0, :],
            response[:, 1, :] - response[:, 0, :],
        ],
        axis=1,
    )
    assert response_guild.shape == (2, 3, 432, 4, 4000), (
        "response_guild shape is not as expected. Expected (2, 3, 432, 4, 4000), but got",
        response_guild.shape,
    )

    # load individual traits
    individual_traits = pd.read_csv("outputs/data/individual_traits.csv", index_col=0)
    if "ind_id" not in individual_traits.columns:
        individual_traits = individual_traits.reset_index()

    # load order of categories
    order_categories = json.load(open("outputs/data/order_categoricals.json", "r"))

    # code ind_id using the order of categories
    individual_traits["ind_id"] = pd.Categorical(
        individual_traits["ind_id"],
        categories=order_categories["ind_id"],
        ordered=True,
    )
    individual_traits["ind_id"] = individual_traits["ind_id"].cat.codes

    n_prot, n_treat, n_ind, n_behav, n_draw = response_guild.shape

    df_response_guild = pd.DataFrame(
        {
            "Protection Level": np.repeat(
                ["Outside PA", "Inside PA"], n_treat * n_ind * n_behav * n_draw
            ),
            "Treatment": np.tile(
                np.repeat(
                    ["Grouper", "Barracuda", "Positive Control"],
                    n_ind * n_behav * n_draw,
                ),
                n_prot,
            ),
            "ind_id": np.tile(
                np.repeat(individual_traits["ind_id"], n_behav * n_draw),
                n_prot * n_treat,
            ),
            "Behaviour": np.tile(
                np.repeat(["Foraging", "Vigilance", "Movement", "Bites"], n_draw),
                n_prot * n_treat * n_ind,
            ),
            "Draw": np.tile(np.arange(n_draw), n_prot * n_treat * n_ind * n_behav),
            "Response": response_guild.flatten(),
        }
    )

    # Merge with individual traits to get guild info
    df_response_guild = df_response_guild.merge(
        individual_traits[["ind_id", "guild"]], on="ind_id", how="left"
    )

    # Summarise the response by guild
    summary_response_guild = (
        df_response_guild.groupby(
            ["Treatment", "Protection Level", "Behaviour", "guild"]
        )["Response"]
        .agg(
            Mean="mean",
            Median="median",
            p5=lambda x: x.quantile(0.05),
            p25=lambda x: x.quantile(0.25),
            p75=lambda x: x.quantile(0.75),
            p95=lambda x: x.quantile(0.95),
        )
        .reset_index()
    )

    # Calculate P(> 0)
    test_response_guild = (
        df_response_guild.groupby(
            ["Treatment", "Protection Level", "Behaviour", "guild"]
        )["Response"]
        .apply(lambda x: np.mean(x > 0))
        .reset_index(name="P(> 0)")
    )

    # Merge summaries
    summary_response_guild = summary_response_guild.merge(
        test_response_guild,
        on=["Treatment", "Protection Level", "Behaviour", "guild"],
    )

    # Reorder and rename columns for readability
    summary_response_guild.rename(
        columns={"p5": "5th", "p25": "25th", "p75": "75th", "p95": "95th"},
        inplace=True,
    )

    # save as csv
    summary_response_guild.to_csv(
        "outputs/analysis/summary_response_guild.csv", index=False
    )

    # --- Compare Responses Table ---
    compare_response_guild = df_response_guild.pivot_table(
        index=["Draw", "Behaviour", "guild"],
        columns=["Protection Level", "Treatment"],
        values="Response",
        aggfunc="mean",
    ).reset_index()

    compare_response_guild = (
        compare_response_guild.groupby(["Behaviour", "guild"])
        .apply(
            lambda x: pd.Series(
                {
                    "Outside PA > Inside PA (Grouper)": np.mean(
                        x["Outside PA"]["Grouper"] > x["Inside PA"]["Grouper"]
                    ),
                    "Outside PA > Inside PA (Barracuda)": np.mean(
                        x["Outside PA"]["Barracuda"] > x["Inside PA"]["Barracuda"]
                    ),
                    "Outside PA > Inside PA (Positive Control)": np.mean(
                        x["Outside PA"]["Positive Control"]
                        > x["Inside PA"]["Positive Control"]
                    ),
                }
            )
        )
        .reset_index()
    )

    # save as csv
    compare_response_guild.to_csv(
        "outputs/analysis/compare_response_guild.csv", index=False
    )

    # plot the difference in response across guilds
    print("\nPlotting difference in response across guilds...\n")
    plt.figure(figsize=(10, 6))
    # Create the faceted box plot
    g = sns.catplot(
        x="guild",
        y="Response",
        hue="Protection Level",
        col="Behaviour",
        row="Treatment",
        kind="box",
        data=df_response_guild,
        palette="pastel",
        height=4,
        aspect=1.2,
        width=0.5,
        legend="full",
        gap=0.1,
        whis=(5, 95),
        showfliers=False,
    )
    # Add horizontal line at y = 0 to each facet
    for ax in g.axes.flat:
        ax.axhline(0, color="black", linestyle="--", linewidth=1)
    # Set titles and labels
    g.set_titles("{row_name} | {col_name}")
    g.set_axis_labels("Foraging Guild", "Log-fold change")
    # Adjust legend
    g._legend.set_title("Protection Level")
    # Save figure
    g.figure.savefig(f"{directory}/response_guild.png", dpi=300, bbox_inches="tight")
    # Close to prevent display in non-interactive environments
    plt.close()


# Counterfactual analysis function


def counterfactual(model_data, directory="figures/counterfactual/"):
    if not os.path.exists(directory):
        os.makedirs(directory)

    # counterfactual predictions

    print("Creating counterfactual predictions...")

    D = az.extract(
        model_data.posterior_predictive, var_names=["D_pred_protection"]
    ).values
    bites = az.extract(
        model_data.posterior_predictive, var_names=["bites_pred_protection"]
    ).values

    response = np.concatenate((D, bites[:, :, :, np.newaxis, :]), axis=3)

    response = np.log(response + 1)

    del D, bites

    # plot the counterfactual predictions
    print("\nCalculating effects of treatment on behaviour...\n")

    effects_treatment(response, directory=directory)

    # plot the difference in response across protection levels
    print("\nCalculating difference in response across protection levels...\n")

    response_protection(response, directory=directory)

    # plot the difference in response across size classes
    print("\nCalculating difference in response across size classes...\n")
    response_size(response, directory=directory)

    # plot the difference in response across guilds
    print("\nCalculating difference in response across guilds...\n")
    response_guild(response, directory=directory)

    print("\nDone.\n")

    return 0
