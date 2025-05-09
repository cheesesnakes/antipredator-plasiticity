params = {
    # effect of protection on predation
    "beta_protection_predator": [-0.5, 0.5],
    "alpha_protection_predator": -1,
    # effect of protection on rugosity
    "D_protection_mean": [150, 100],
    "D_protection_std": [10, 10],
    # effect of protection on resource availability
    "points_protection_mean": [50, 70],
    "points_protection_std": [2, 2],
    # engery variable
    "beta_energy_resource": 1,
    "beta_predator_energy": [0.5, -0.5],
    "alpha_energy": 1,
    "sigma_energy": 0.1,
    # risk variable
    "beta_risk_rugosity": -0.5,
    "beta_risk_predator": [-0.5, 0.5],
    "beta_risk_treatment": [0, 0.5, 2, 5],
    "alpha_risk": 0.01,
    "sigma_risk": 0.1,
    # time model: foraging, vigilance, movement
    "beta_energy": [-0.2, 0, 0.1],
    "beta_risk": [-0.2, 0.2, -0.1],
    "alpha": [0.2, 0.1, 0.1],
    "sigma": [1, 1, 1],
    "beta_pi_risk": [1, -1, 1],
    "beta_pi_energy": [1, 1, -1],
    "alpha_pi": [-2, -2, -2],
}
