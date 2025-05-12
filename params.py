params = {
    # effect of protection on predation
    "alpha_predator": [-0.5, 0],
    # effect of protection on rugosity
    "D_protection_mean": [150, 100],
    "D_protection_std": [10, 10],
    # effect of protection on resource availability
    "points_protection_mean": [50, 70],
    "points_protection_std": [2, 2],
    # risk variable
    "beta_risk_resource": -1,
    "beta_risk_rugosity": -1,
    "beta_risk_predator": [0, 0.5],
    "beta_risk_treatment": [0, 0.5, 1, 2],
    "alpha_risk": [0, 0.5],
    "sigma_risk": 1,
    # time model: foraging, vigilance, movement
    "beta_risk": [-0.5, 0.5, -0.1],
    "beta_risk_bites": -0.5,
    "sigma": [1, 1, 1],
    "beta_pi_risk": [0.5, -0.5, 0.5],
    "alpha_pi": [-5, -5, -5],
}
