import marimo

__generated_with = "0.12.10"
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
    return bern, beta, choices, dirichlet, expit, mo, np, params, pd, plt, sns


@app.cell
def _(bern, beta, expit, np, params, pd):
    # experiment definition

    n_protection = 2
    n_treatment = 4
    n_ind = 20
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
        alpha = params["alpha_protection_predator"]

        beta = params["beta_protection_predator"]

        p = expit(alpha + beta[protection])

        return bern.rvs(p, size=1)


    def rugosity(protection):
        """
        Simulate a rugosity covariate.
        """

        D_max = 190

        D_chain_mean = params["D_protection_mean"]

        D_chain_var = params["D_protection_std"]

        a = np.random.normal(0, 1)

        a = (a * D_chain_var[protection]) + D_chain_mean[protection]

        b = D_max - a

        return beta.rvs(a, b, size=1)


    def resource(protection):
        """
        Simulate a resource covariate.
        """

        points = 100

        points_mean = params["points_protection_mean"]

        points_var = params["points_protection_std"]

        a = np.random.normal(0, 1)

        a = a * points_var[protection] + points_mean[protection]

        b = points - a

        return beta.rvs(a, b, size=1)


    predator = [predator(p) for p in protection]
    predator = np.array(predator).flatten()
    rugosity = [rugosity(p) for p in protection]
    rugosity = np.array(rugosity).flatten()
    resource = [resource(p) for p in protection]
    resource = np.array(resource).flatten()

    # predictor dataframe

    predictor_df = pd.DataFrame(
        {
            "plot_id": plot_id,
            "protection": protection,
            "treatment": treatment,
            "replicate": replicate,
            "predator": predator,
            "rugosity": rugosity,
            "resource": resource,
        }
    )

    predictor_df
    return (
        n_ind,
        n_protection,
        n_rep,
        n_treatment,
        plot_id,
        predator,
        predictor_df,
        protection,
        replicate,
        resource,
        rugosity,
        treatment,
    )


@app.cell
def _(predictor_df):
    predictor_df.to_csv("outputs/generated_data_predictors.csv", index=False)
    return


@app.cell
def _(plt, predictor_df, sns):
    plt.figure(figsize=(18, 6))
    plt.subplot(1, 3, 1)
    sns.histplot(data=predictor_df, x="predator", hue="protection", kde=True)
    plt.title("Predator Presence")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 2)
    sns.histplot(data=predictor_df, x="rugosity", hue="protection", kde=True)
    plt.title("Rugosity")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 3)
    sns.histplot(data=predictor_df, x="resource", hue="protection", kde=True)
    plt.title("Resource Availability")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(n_ind, np, params, pd, plot_id, predictor_df):
    # unobserved variables


    def energy(resource, predator):
        """
        Simulate an energy covariate.
        """

        beta_resource = params["beta_energy_resource"]

        beta_predator = params["beta_predator_energy"][predator]

        alpha = params["alpha_energy"]

        mu = alpha + beta_resource * resource + beta_predator

        sigma = params["sigma_energy"]

        return np.random.normal(mu, sigma, size=1)


    def risk(rugosity, predator, treatment):
        """
        Simulate a risk covariate.
        """

        beta_rugosity = params["beta_risk_rugosity"]

        beta_predator = params["beta_risk_predator"][predator]

        beta_treatment = params["beta_risk_treatment"][treatment - 1]

        alpha = params["alpha_risk"]

        mu = alpha + (beta_rugosity * rugosity) + beta_predator + beta_treatment

        sigma = params["sigma_risk"]

        return np.random.normal(mu, sigma, size=1)


    indiviudals = list(range(1, (len(plot_id) * n_ind) + 1))
    plot_ind = [plot for i in range(n_ind) for plot in plot_id]

    energy = [
        energy(
            predictor_df.loc[predictor_df["plot_id"] == i, "resource"].iloc[0],
            predictor_df.loc[predictor_df["plot_id"] == i, "predator"].iloc[0],
        )
        for i in plot_ind
    ]
    energy = np.array(energy).flatten()

    risk = [
        risk(
            predictor_df.loc[predictor_df["plot_id"] == i, "rugosity"].iloc[0],
            predictor_df.loc[predictor_df["plot_id"] == i, "predator"].iloc[0],
            predictor_df.loc[predictor_df["plot_id"] == i, "treatment"].iloc[0],
        )
        for i in plot_ind
    ]
    risk = np.array(risk).flatten()

    # unobserved variables dataframe
    unobserved_df = pd.DataFrame(
        {
            "ind_id": indiviudals,
            "plot_id": plot_ind,
            "energy": energy,
            "risk": risk,
        }
    )

    unobserved_df = unobserved_df.merge(predictor_df, on="plot_id")
    unobserved_df
    return energy, indiviudals, plot_ind, risk, unobserved_df


@app.cell
def _(plt, sns, unobserved_df):
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    sns.histplot(data=unobserved_df, x="energy", hue="protection", kde=True)
    plt.title("Energy")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 2, 2)
    sns.histplot(data=unobserved_df, x="risk", hue="protection", kde=True)
    plt.title("Risk")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(bern, expit, indiviudals, np, params, pd, plot_ind, unobserved_df):
    # response variable


    def total_time(behaviour, energy, risk):
        """
        Simulate a behavioural response.
        """

        beta_energy = params["beta_energy"][behaviour]

        beta_risk = params["beta_risk"][behaviour]

        alpha = params["alpha"][behaviour]

        mu = alpha + beta_energy * energy + beta_risk * risk

        sigma = params["sigma"][behaviour]

        # zero inflation
        pi_0 = expit(
            params["alpha_pi"][behaviour] + params["beta_pi_risk"][behaviour] * risk + params["beta_pi_energy"][behaviour] * energy
        )

        zero = bern.rvs(pi_0)

        if zero:
            return [0]
        else:
            return np.random.lognormal(mu, sigma, size=1)


    foraging = [total_time(0, row["energy"], row["risk"]) for _, row in unobserved_df.iterrows()]
    foraging = np.array(foraging).flatten()
    vigilance = [total_time(1, row["energy"], row["risk"]) for _, row in unobserved_df.iterrows()]
    vigilance = np.array(vigilance).flatten()
    movement = [total_time(2, row["energy"], row["risk"]) for _, row in unobserved_df.iterrows()]
    movement = np.array(movement).flatten()

    # response dataframe
    response_df = pd.DataFrame(
        {
            "ind_id": indiviudals,
            "plot_id": plot_ind,
            "foraging": foraging,
            "vigilance": vigilance,
            "movement": movement,
        }
    )

    response_df
    return foraging, movement, response_df, total_time, vigilance


@app.cell
def _(response_df):
    response_df.to_csv("outputs/generated_data_response.csv", index=False)
    return


@app.cell
def _(plt, predictor_df, response_df, sns):
    behaviour = response_df.merge(predictor_df, on="plot_id")

    plt.figure(figsize=(18, 6))
    plt.subplot(1, 3, 1)
    sns.histplot(data=behaviour, x="foraging", hue="protection", kde=False)
    plt.title("Foraging")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 2)
    sns.histplot(data=behaviour, x="vigilance", hue="protection", kde=False)
    plt.title("Vigilance")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 3)
    sns.histplot(data=behaviour, x="movement", hue="protection", kde=False)
    plt.title("Movement")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.tight_layout()
    plt.show()
    return (behaviour,)


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
