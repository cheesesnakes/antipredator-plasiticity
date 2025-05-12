import marimo

__generated_with = "0.13.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from scipy.stats import bernoulli as bern
    from scipy.stats import dirichlet
    from scipy.stats import beta
    from scipy.special import expit
    from random import choices
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    from params import params

    sns.set_theme(style="white", palette="pastel")
    return bern, beta, expit, np, params, pd, plt, sns


@app.cell
def _(bern, beta, expit, np, params, pd):
    # experiment definition

    n_protection = 2
    n_treatment = 4
    n_ind = 10
    n_rep = 5

    # treatment and protection levels

    plot_id = list(range(1, (n_protection * n_treatment * n_rep) + 1))
    protection = [p for i in range((n_treatment * n_rep)) for p in range(n_protection)]
    treatment = [t for t in range(n_treatment) for i in range(n_rep) for p in range(n_protection)]
    replicate = [r for r in range(n_rep) for i in range(n_treatment * n_protection)]

    # covariates


    def predator(protection):
        """
        Simulate a predator covariate.
        """
        alpha = np.random.normal(params["alpha_predator"][protection], 0.1)  # plot-level random effect

        # link

        p = expit(alpha)

        return bern.rvs(p, size=1)


    def rugosity(protection):
        """
        Simulate a rugosity covariate.
        """

        D_max = 190

        D_chain_mean = params["D_protection_mean"][protection]

        D_chain_var = params["D_protection_std"][protection]

        a = np.random.normal(0, 1, size=3)  # plot level randomness, three measurements

        a = D_chain_mean + D_chain_var * a

        b = D_max - a

        return np.array(1 - beta.rvs(a, b, size=3))


    def biomass(protection):
        """
        Simulate a biomass covariate.
        """

        points = 100

        points_mean = params["points_protection_mean"][protection]

        points_var = params["points_protection_std"][protection]

        a = np.random.normal(0, 1)  # plot - level randomness

        a = a * points_var + points_mean

        b = points - a

        return beta.rvs(a, b, size=1)


    predator = [predator(p) for p in protection]
    predator = np.array(predator).flatten()
    biomass = [biomass(p) for p in protection]
    biomass = np.array(biomass).flatten()
    rugosity = [rugosity(p) for p in protection]
    rugosity = np.array(rugosity).reshape(40, 3)

    rugosity_df = pd.DataFrame(
        {
            "plot_id": plot_id,
            "sample_1": rugosity[:, 0],
            "sample_2": rugosity[:, 1],
            "sample_3": rugosity[:, 2],
        }
    )

    rugosity_mean = [
        np.mean(rugosity_df.loc[rugosity_df["plot_id"] == i, ["sample_1", "sample_2", "sample_3"]].values) for i in plot_id
    ]
    rugosity_mean = np.array(rugosity_mean).flatten()

    # predictor dataframe

    predictor_df = pd.DataFrame(
        {
            "plot_id": plot_id,
            "protection": protection,
            "treatment": treatment,
            "replicate": replicate,
            "rugosity": rugosity_mean,
            "predator": predator,
            "biomass": biomass,
        }
    )

    rugosity_df
    return n_ind, plot_id, predictor_df, rugosity_df


@app.cell
def _(predictor_df):
    predictor_df
    return


@app.cell
def _(predictor_df, rugosity_df):
    predictor_df.to_csv("outputs/generated_data_predictor.csv", index=False)
    rugosity_df.to_csv("outputs/generated_data_rugosity.csv", index=False)
    return


@app.cell
def _(plt, predictor_df, sns):
    plt.figure(figsize=(18, 6))
    plt.subplot(1, 3, 1)
    sns.boxplot(data=predictor_df, x="protection", y="predator", hue="protection")
    plt.title("Predator Presence")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 2)
    sns.boxplot(data=predictor_df, x="protection", y="rugosity", hue="protection")
    plt.title("Rugosity")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 3)
    sns.boxplot(data=predictor_df, x="protection", y="biomass", hue="protection")
    plt.title("Resource Availability")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(n_ind, np, params, pd, plot_id, predictor_df):
    # unobserved variables


    def risk(rugosity, predator, treatment, protection, biomass):
        """
        Simulate a risk covariate.
        """

        beta_rugosity = params["beta_risk_rugosity"]

        beta_predator = params["beta_risk_predator"][predator]

        beta_treatment = params["beta_risk_treatment"][treatment]

        beta_resource = params["beta_risk_resource"]

        alpha_risk = params["alpha_risk"][protection]  # effect of protection on risk

        eta = alpha_risk + (beta_rugosity * rugosity) + beta_predator + beta_treatment + beta_resource * biomass

        mu = np.random.normal(eta, 0.1)  # individual-level random effect

        sigma = params["sigma_risk"]

        return np.random.normal(mu, sigma, size=1)


    indiviudals = list(range(1, (len(plot_id) * n_ind) + 1))
    plot_ind = [plot for i in range(n_ind) for plot in plot_id]

    risk = [
        risk(
            predictor_df.loc[predictor_df["plot_id"] == i, "rugosity"].iloc[0],
            predictor_df.loc[predictor_df["plot_id"] == i, "predator"].iloc[0],
            predictor_df.loc[predictor_df["plot_id"] == i, "treatment"].iloc[0],
            predictor_df.loc[predictor_df["plot_id"] == i, "protection"].iloc[0],
            predictor_df.loc[predictor_df["plot_id"] == i, "biomass"].iloc[0],
        )
        for i in plot_ind
    ]
    risk = np.array(risk).flatten()

    # unobserved variables dataframe
    unobserved_df = pd.DataFrame(
        {
            "ind_id": indiviudals,
            "plot_id": plot_ind,
            "risk": risk,
        }
    )

    unobserved_df = unobserved_df.merge(predictor_df, on="plot_id")
    unobserved_df
    return indiviudals, plot_ind, risk, unobserved_df


@app.cell
def _(plt, sns, unobserved_df):
    plt.figure(figsize=(8, 6))
    sns.boxplot(data=unobserved_df, y="risk", x="protection", hue="protection")
    plt.title("Risk")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(plt, sns, unobserved_df):
    sns.boxplot(x="treatment", y="risk", hue="protection", data=unobserved_df)
    plt.title("Risk by Treatment")
    plt.show()
    return


@app.cell
def _(bern, expit, indiviudals, np, params, pd, plot_ind, risk, unobserved_df):
    # response variable


    def total_time(behaviour, risk):
        """
        Simulate a behavioural response.
        """

        beta_risk = params["beta_risk"][behaviour]

        mu = beta_risk * risk

        sigma = params["sigma"][behaviour]

        # zero inflation
        pi_0 = expit(params["alpha_pi"][behaviour] + params["beta_pi_risk"][behaviour] * risk)

        zero = bern.rvs(pi_0)

        if zero:
            return [0]
        else:
            return np.random.lognormal(mu, sigma, size=1)


    def bites(foraging, risk):
        """
        Simulate bite rates
        """

        if foraging > 0:
            beta_risk = params["beta_risk_bites"]

            mu = beta_risk * risk

            rate = np.exp(mu)

            return np.random.poisson(rate, size=1)
        else:
            return [0]


    foraging = [total_time(0, row["risk"]) for _, row in unobserved_df.iterrows()]
    foraging = np.array(foraging).flatten()
    vigilance = [total_time(1, row["risk"]) for _, row in unobserved_df.iterrows()]
    vigilance = np.array(vigilance).flatten()
    movement = [total_time(2, row["risk"]) for _, row in unobserved_df.iterrows()]
    movement = np.array(movement).flatten()
    bites = [bites(f, r) for f, r in zip(foraging, risk)]
    bites = np.array(bites).flatten()

    # response dataframe
    response_df = pd.DataFrame(
        {
            "ind_id": indiviudals,
            "plot_id": plot_ind,
            "foraging": foraging,
            "vigilance": vigilance,
            "movement": movement,
            "bites": bites,
        }
    )

    response_df
    return (response_df,)


@app.cell
def _(response_df):
    response_df.to_csv("outputs/generated_data_response.csv", index=False)
    return


@app.cell
def _(plt, predictor_df, response_df, sns):
    behaviour_df = response_df.copy().merge(predictor_df, on="plot_id")

    plt.figure(figsize=(18, 6))
    plt.subplot(1, 3, 1)
    sns.histplot(data=behaviour_df, x="foraging", hue="protection", kde=False)
    plt.title("Foraging")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 2)
    sns.histplot(data=behaviour_df, x="vigilance", hue="protection", kde=False)
    plt.title("Vigilance")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 3)
    sns.histplot(data=behaviour_df, x="movement", hue="protection", kde=False)
    plt.title("Movement")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.tight_layout()
    plt.show()
    return (behaviour_df,)


@app.cell
def _(behaviour_df, plt, sns):
    plt.figure(figsize=(10, 6))
    sns.histplot(data=behaviour_df, x="bites", hue="protection", kde=False)
    plt.title("Bites")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(behaviour_df, plt, sns):
    plt.figure(figsize=(18, 6))
    plt.subplot(1, 3, 1)
    sns.histplot(data=behaviour_df, x="foraging", hue="treatment", kde=False)
    plt.title("Foraging")
    plt.legend(
        title="Protection",
        labels=["Negative", "Positive", "Treatment 1", "Treatment 2"],
    )
    plt.xscale("log")
    plt.subplot(1, 3, 2)
    sns.histplot(data=behaviour_df, x="vigilance", hue="treatment", kde=False)
    plt.title("Vigilance")
    plt.legend(
        title="Protection",
        labels=["Negative", "Positive", "Treatment 1", "Treatment 2"],
    )
    plt.xscale("log")
    plt.subplot(1, 3, 3)
    sns.histplot(data=behaviour_df, x="movement", hue="treatment", kde=False)
    plt.title("Movement")
    plt.legend(
        title="Protection",
        labels=["Negative", "Positive", "Treatment 1", "Treatment 2"],
    )
    plt.xscale("log")
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
