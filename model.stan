data {
  int<lower=0> N; // number of observations
  int<lower=0> T; // number of treatments
  int<lower=0> P; // number of protection levels
  int<lower=0> S; // number of plots
  array[N] real<lower=0> D; // observed durations
  
  // Predictor variables
  array[S] int<lower=1, upper=2> predator; // predator presence (0 or 1)
  array[N] int<lower=1, upper=S> plot; // plot number
  array[S, 3] real<lower=0, upper=1> rugosity_raw; // rugosity (continuous variable)
  array[S] int<lower=1, upper=2> protection; // protection level (0 or 1)
  array[S] int<lower=1, upper=4> treatment; // treatment group (0, 1, 2, or 3)
  array[S] real<lower=0, upper=1> biomass; // biomass availability (continuous variable)
}
parameters {
  // Rugosity
  
  array[S] real<lower=0, upper=1> rugosity; // accounting for multiple rugosity measurements
  array[S] real<lower=0> phi_rug; // standard deviation of rugosity in each plot
  
  // Top-level coefficients
  real beta_risk; // effect of risk on duration
  
  real alpha_pi; // baseline zero-inflation
  real beta_pi_risk; // effect of risk on zero-inflation
  
  // Risk model coefficients
  real alpha_risk_protection; // random risk per individual
  real beta_predator; // effect of predator presence on risk
  real beta_rug; // effect of rugosity on risk
  ordered[T] beta_treatment; // effect of treatment on risk
  array[N] real<lower=0> sigma_risk; // standard deviation of risk
  real beta_res; // effect of biomass availability on energy
  
  // Observation model
  real<lower=1e-6, upper=10> sigma_D; // standard deviation of duration, non-zero
  
  // Latent variables non-centred
  array[N] real z_risk; // latent risk variable
}
transformed parameters {
  array[S] real mu_risk; // mean risk
  
  array[N] real mu_D; // mean duration
  
  array[N] real pi; // zero-inflation probability
  
  // Latent variables per observation
  array[N] real risk; // latent risk variable
  
  // mean risk per plot
  for (s in 1 : S) {
    mu_risk[s] = alpha_risk_protection * (protection[s] - 1)
                 + beta_predator * (predator[s] - 1) + beta_rug * rugosity[s]
                 + beta_treatment[treatment[s]] + beta_res * biomass[s];
  }
  
  for (n in 1 : N) {
    // Latent variables
    risk[n] = mu_risk[plot[n]] + sigma_risk[plot[n]] * z_risk[n];
    
    // Zero-inflation probability
    pi[n] = inv_logit(alpha_pi + beta_pi_risk * risk[n]);
    
    // Duration model parameters
    
    mu_D[n] = beta_risk * risk[n];
  }
}
model {
  // Priors
  
  // Top-level priors
  beta_risk ~ normal(0, 1);
  
  mu_D ~ normal(0, 2);
  
  beta_pi_risk ~ normal(0, 1);
  alpha_pi ~ normal(-2, 1);
  
  pi ~ beta(1, 1);
  
  // Risk model priors
  beta_rug ~ normal(0, 1);
  sigma_risk ~ exponential(1);
  beta_res ~ normal(0, 1);
  alpha_risk_protection ~ normal(0, 0.5);
  beta_predator ~ normal(0, 1);
  
  beta_treatment[1] ~ normal(0, 0.5);
  beta_treatment[2] ~ normal(0, 1);
  beta_treatment[3] ~ normal(1, 1);
  beta_treatment[4] ~ normal(2, 1);
  
  // rugosity priors
  rugosity ~ beta(2, 2); // beta distribution for rugosity
  phi_rug ~ gamma(2, 1); // precision of rugosity
  
  // Latent variables priors
  mu_risk ~ normal(0, 2);
  
  sigma_D ~ normal(0, 0.5) T[1e-6, ]; // truncated normal scale
  
  z_risk ~ normal(0, 1); // latent risk variable
  
  // rugosity
  for (s in 1 : S) {
    for (i in 1 : 3) {
      rugosity_raw[s, i] ~ beta(rugosity[s] * phi_rug[s],
                                (1 - rugosity[s]) * phi_rug[s]);
    }
  }
  
  // Observation model
  
  for (n in 1 : N) {
    if (D[n] == 0) {
      target += bernoulli_lpmf(1 | pi[n]); // zero-inflation
    } else {
      target += bernoulli_lpmf(0 | pi[n]); // non-zero inflation
      target += lognormal_lpdf(D[n] | mu_D[n], sigma_D); // duration model
    }
  }
}
generated quantities {
  array[N] real D_pred; // predicted durations
  // For treatment-specific predictions per observation (N-scale)
  array[T, N] real mu_risk_treatment;
  array[T, N] real mu_D_treatment;
  array[T, P, N] real D_pred_treatment;
  
  // posterior predictive check
  for (n in 1 : N) {
    if (bernoulli_rng(pi[n])) {
      D_pred[n] = 0; // zero-inflation
    } else {
      D_pred[n] = lognormal_rng(mu_D[n], sigma_D);
    }
  }
  
  // Posterior predictive per treatment × observation
  for (t in 1 : T) {
    for (p in 1 : P) {
      for (n in 1 : N) {
        int s = plot[n]; // plot index for observation n
        
        // 1️⃣ Compute mu_risk for this treatment & obs
        mu_risk_treatment[t, n] = alpha_risk_protection * (protection[s] - 1)
                                  + beta_predator * (predator[s] - 1)
                                  + beta_rug * rugosity[s]
                                  + beta_treatment[t] + beta_res * biomass[s]
                                  + sigma_risk[n] * z_risk[n];
        // 3️⃣ Compute mean duration (log scale) for this treatment & obs
        mu_D_treatment[t, n] = beta_risk * mu_risk_treatment[t, n];
        
        // 4️⃣ Predict new duration:
        if (bernoulli_rng(inv_logit(alpha_pi
                                    + beta_pi_risk * mu_risk_treatment[t, n]))) {
          D_pred_treatment[t, p, n] = 0;
        } else {
          D_pred_treatment[t, p, n] = lognormal_rng(mu_D_treatment[t, n],
                                                    sigma_D);
        }
      }
    }
  }
}
