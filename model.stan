data {
  int<lower=0> N; // number of observations
  int<lower=0> T; // number of treatments
  int<lower=0> P; // number of protection levels
  int<lower=0> S; // number of plots
  array[N] real<lower=0> D; // observed durations
  
  // Predictor variables
  array[S] int<lower=1, upper=2> predator; // predator presence (0 or 1)
  array[N] int<lower=1, upper=S> plot; // plot number
  array[S] real<lower=0, upper=1> rugosity; // rugosity (continuous variable)
  array[S] int<lower=1, upper=2> protection; // protection level (0 or 1)
  array[S] int<lower=1, upper=4> treatment; // treatment group (0, 1, 2, or 3)
  array[S] real<lower=0, upper=1> resource; // resource availability (continuous variable)
}
parameters {
  // Top-level coefficients
  real beta_risk; // effect of risk on duration
  real beta_energy; // effect of energy on duration
  
  real alpha_pi; // baseline zero-inflation
  real beta_pi_risk; // effect of risk on zero-inflation
  real beta_pi_energy; // effect of energy on zero-inflation
  
  // Risk model coefficients
  array[N] real alpha_risk; // random risk per individual
  ordered[P] beta_predator; // effect of predator presence on risk
  real beta_rug; // effect of rugosity on risk
  ordered[T] beta_treatment; // effect of treatment on risk
  array[S] real<lower=0> sigma_risk; // standard deviation of risk
  
  // Energy model coefficients
  array[N] real alpha_energy; // random energy per individual
  real beta_res; // effect of resource availability on energy
  ordered[2] beta_predator_energy; // effect of predator presence on energy through unobserved variables
  array[S] real<lower=0> sigma_energy; // standard deviation of energy
  
  // protection model coefficients
  
  ordered[P] beta_risk_protection; // effect on risk
  ordered[P] beta_energy_protection; // effect on energy
  
  // Observation model
  real alpha_D; // baseline duration
  real<lower=1e-6, upper=10> sigma_D; // standard deviation of duration, non-zero
  
  // Latent variables non-centred
  array[N] real z_risk; // latent risk variable
  array[N] real z_energy; // latent energy variable
}
transformed parameters {
  array[S] real beta_mu_risk; // mean risk
  array[S] real beta_mu_energy; // mean energy
  
  array[N] real mu_risk; // mean risk
  array[N] real mu_energy; // mean energy
  
  array[N] real<upper=20> mu_D; // mean duration
  
  array[N] real pi; // zero-inflation probability
  
  // Latent variables per observation
  array[N] real risk; // latent risk variable
  array[N] real energy; // latent energy variable
  
  for (s in 1 : S) {
    // Risk model parameters
    beta_mu_risk[s] = beta_predator[predator[s]] + beta_rug * rugosity[s]
                      + beta_treatment[treatment[s]]
                      + beta_risk_protection[protection[s]];
    
    // Energy model parameters
    beta_mu_energy[s] = beta_res * resource[s]
                        + beta_predator_energy[predator[s]]
                        + beta_risk_protection[protection[s]];
  }
  
  for (n in 1 : N) {
    mu_risk[n] = alpha_risk[n] + beta_mu_risk[plot[n]];
    mu_energy[n] = alpha_energy[n] + beta_mu_energy[plot[n]];
    
    // Latent variables
    risk[n] = mu_risk[plot[n]] + sigma_risk[plot[n]] * z_risk[n];
    energy[n] = mu_energy[plot[n]] + sigma_energy[plot[n]] * z_energy[n];
    
    // Zero-inflation probability
    pi[n] = inv_logit(alpha_pi + beta_pi_risk * risk[n]
                      + beta_pi_energy * energy[n]);
    
    // Duration model parameters
    
    mu_D[n] = alpha_D + beta_risk * risk[n] + beta_energy * energy[n];
  }
}
model {
  // Priors
  beta_risk ~ normal(0, 0.5);
  beta_energy ~ normal(0, 0.5);
  beta_pi_risk ~ normal(0, 0.5);
  beta_pi_energy ~ normal(0, 0.5);
  
  alpha_risk ~ normal(0, 0.5);
  beta_predator ~ normal(0, 0.1);
  beta_rug ~ normal(0, 0.1);
  beta_treatment ~ normal(0, 0.1);
  sigma_risk ~ exponential(1);
  beta_risk_protection ~ normal(0, 0.5);
  
  beta_predator_energy ~ normal(0, 0.5);
  alpha_energy ~ normal(0, 0.5);
  beta_res ~ normal(0, 0.5);
  sigma_energy ~ exponential(1);
  beta_energy_protection ~ normal(0, 0.5);
  
  alpha_D ~ normal(0, 0.5);
  sigma_D ~ normal(0, 0.5) T[1e-6, ]; // truncated lognormal scale
  
  z_risk ~ normal(0, 0.5); // latent risk variable
  z_energy ~ normal(0, 0.5); // latent energy variable
  
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
  array[T, N] real mu_energy_treatment;
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
        mu_risk_treatment[t, n] = alpha_risk[s] + beta_predator[predator[s]]
                                  + beta_rug * rugosity[s]
                                  + beta_treatment[t]
                                  + beta_risk_protection[p];
        
        // 2️⃣ Compute mu_energy for this treatment & obs
        mu_energy_treatment[t, n] = alpha_energy[s] + beta_res * resource[s]
                                    + beta_predator_energy[predator[s]]
                                    + beta_energy_protection[p];
        
        // 3️⃣ Compute mean duration (log scale) for this treatment & obs
        mu_D_treatment[t, n] = alpha_D + beta_risk * mu_risk_treatment[t, n]
                               + beta_energy * mu_energy_treatment[t, n];
        
        // 4️⃣ Predict new duration:
        if (bernoulli_rng(inv_logit(alpha_pi
                                    + beta_pi_risk * mu_risk_treatment[t, n]
                                    + beta_pi_energy
                                      * mu_energy_treatment[t, n]))) {
          D_pred_treatment[t, p, n] = 0;
        } else {
          D_pred_treatment[t, p, n] = lognormal_rng(mu_D_treatment[t, n],
                                                    sigma_D);
        }
      }
    }
  }
}
