import marimo

__generated_with = "0.12.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from scipy.stats import bernoulli as bern
    from scipy.stats import dirichlet
    from random import choices
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="white", palette="pastel")
    return bern, choices, dirichlet, mo, np, plt, sns


@app.cell
def _():
    states = [1, 2, 3]  # fear, hunger, rest

    # transition between states p(s_i | s_{i-1})

    T_s = [[0.0, 0.5, 0.5], [0.5, 0.0, 0.5], [0.5, 0.5, 0.0]]

    # duration in each state

    alpha_s = [2.0, 2.0, 2.0]  # shape: variance
    theta_s = [1.0, 1.0, 1.0]  # scale: mean

    behaviours = [1, 2, 3]  # foraging, vigilance, moving <-- emmission

    # p(b_i | s_i) states x behaviours

    p_b = [[0.1, 0.8, 0.1], [0.8, 0.1, 0.1], [0.3, 0.3, 0.4]]

    # duration in each behaviour

    alpha_b = [2.0, 2.0, 2.0]  # shape: variance
    theta_b = [1.0, 1.0, 1.0]  # scale: mean
    return T_s, alpha_b, alpha_s, behaviours, p_b, states, theta_b, theta_s


@app.cell
def _(T_s, alpha_b, alpha_s, behaviours, np, p_b, states, theta_b, theta_s):
    # Simulation

    T = 120.0  # max duration
    dt = 0.1
    tao = 0.0

    # initial state
    p_x = [0.4, 0.3, 0.3]
    x_t = np.random.choice(states, p=p_x)

    x_i = []
    t_x_i = []
    b_i = []
    t_b_i = []

    while tao < T:
        x_i.append(x_t)

        # how much time does the individual spend in this state (x_t)
        d_x_t = np.random.gamma(alpha_s[x_t - 1], theta_s[x_t - 1])
        end_s = tao + d_x_t
        t_x_i.append(min(end_s, 120))

        # make emission

        tao_b = tao

        while tao_b < end_s:
            # pick behaviour
            p_b_t = p_b[x_t - 1]

            b_t = np.random.choice(behaviours, p=p_b_t)
            b_i.append(b_t)

            # how much time does the individual spend in this behaviour (b_t)
            d_b_t = np.random.gamma(alpha_b[x_t - 1], theta_b[x_t - 1])
            end = tao_b + d_b_t
            t_b_i.append(min(end, 120))

            # update time
            tao_b = end

        # pick next state

        p_x_t = T_s[x_t - 1]

        x_t = np.random.choice(states, p=p_x_t)

        # update time

        tao = end
    return (
        T,
        b_i,
        b_t,
        d_b_t,
        d_x_t,
        dt,
        end,
        end_s,
        p_b_t,
        p_x,
        p_x_t,
        t_b_i,
        t_x_i,
        tao,
        tao_b,
        x_i,
        x_t,
    )


@app.cell
def _(plt, sns, t_x_i, x_i):
    sns.lineplot(x=t_x_i, y=x_i, drawstyle="steps-post")
    plt.xlim(0, 120)
    plt.xlabel("Time")
    plt.ylabel("State")
    plt.yticks([1, 2, 3], ["Fear", "Hunger", "Rest"])
    plt.show()
    return


@app.cell
def _(b_i, plt, sns, t_b_i):
    sns.lineplot(x=t_b_i, y=b_i, drawstyle="steps-post")
    plt.xlim(0, 120)
    plt.xlabel("Time")
    plt.ylabel("Behaviour")
    plt.yticks([1, 2, 3], ["Foraging", "Vigilance", "Moving"])
    plt.show()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
