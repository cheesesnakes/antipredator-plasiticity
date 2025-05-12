data {
  int<lower=0> N; // number of observations
  int<lower=0> T; // number of treatments
  int<lower=0> P; // number of protection levels
  int<lower=0> B; // number of behavioral types
  int<lower=0> S; // number of plots
  array[N, B] real<lower=0> D; // observed durations
  array[N] int<lower=0> bites; // number of bites observed
  
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
  
  array[S] real<lower=1e-6, upper=(1 - 1e-6)> rugosity; // accounting for multiple rugosity measurements
  array[S] real<lower=1e-6> phi_rug; // standard deviation of rugosity in each plot
  
  // Top-level coefficients for duration
  ordered[B] beta_risk; // effect of risk on duration
  
  ordered[B] alpha_pi; // baseline zero-inflation
  ordered[B] beta_pi_risk; // effect of risk on zero-inflation
  
  // Top-level coefficients for bites
  real beta_risk_bites; // effect of risk on bites
  
  // Risk model coefficients
  ordered[2] alpha_risk_protection; // random risk per individual
  ordered[2] beta_predator; // effect of predator presence on risk
  real beta_rug; // effect of rugosity on risk
  ordered[T] beta_treatment; // effect of treatment on risk
  real<lower=0> sigma_risk; // standard deviation of risk
  real beta_res; // effect of biomass availability on energy
  
  // Observation model
  array[B] real<lower=1e-6, upper=10> sigma_D; // standard deviation of duration, non-zero
  
  // Latent variables non-centred
  array[N] real z_risk; // latent risk variable
}
transformed parameters {
  array[S] real mu_risk; // mean risk
  
  array[N, B] real mu_D; // mean duration
  
  array[N] real lamba_risk; // mean bites
  
  array[N, B] real<lower=0, upper=1> pi; // zero-inflation probability
  
  // Latent variables per observation
  array[N] real risk; // latent risk variable
  
  // mean risk per plot
  for (s in 1 : S) {
    mu_risk[s] = alpha_risk_protection[protection[s]]
                 + beta_predator[predator[s]] + beta_rug * rugosity[s]
                 + beta_treatment[treatment[s]] + beta_res * biomass[s];
  }
  
  for (n in 1 : N) {
    // Latent variables
    risk[n] = mu_risk[plot[n]] + sigma_risk * z_risk[n];
    
    for (b in 1 : B) {
      // zero-inflation probability
      pi[n, b] = inv_logit(alpha_pi[b] + beta_pi_risk[b] * risk[n]);
      
      // Mean duration
      mu_D[n, b] = beta_risk[b] * risk[n];
    }
    
    // Mean bites
    
    lamba_risk[n] = exp(beta_risk_bites * risk[n]);
  }
}
model {
  // Priors
  
  // Top-level priors
  beta_risk_bites ~ normal(0, 1);
  
  // priors for foraging
  beta_risk[1] ~ normal(-1, 1);
  beta_pi_risk[1] ~ normal(1, 1);
  alpha_pi[1] ~ normal(-1, 2);
  
  // priors for vigilance
  beta_risk[2] ~ normal(1, 1);
  beta_pi_risk[2] ~ normal(-1, 1);
  alpha_pi[2] ~ normal(-1, 2);
  
  // priors for movement
  beta_risk[3] ~ normal(-1, 1);
  beta_pi_risk[3] ~ normal(0, 1);
  alpha_pi[3] ~ normal(-1, 2);
  
  // Risk model priors
  beta_rug ~ normal(-1, 1);
  beta_res ~ normal(0, 1);
  
  for (t in 1 : T) {
    beta_treatment[t] ~ normal(0, 1);
  }
  
  for (p in 1 : 2) {
    beta_predator[p] ~ normal(0, 1);
  }
  for (r in 1 : 2) {
    alpha_risk_protection[r] ~ normal(0, 1);
  }
  
  for (i in 1 : 3) {
    z_risk[i] ~ normal(0, 1); // risk latent variable
  }
  
  sigma_risk ~ exponential(1);
  
  // rugosity priors
  rugosity ~ beta(1, 1); // beta distribution for rugosity
  phi_rug ~ gamma(2, 2); // precision of rugosity
  
  // Latent variables priors
  
  for (b in 1 : B) {
    sigma_D[b] ~ exponential(1); // standard deviation of duration
  }
  
  // rugosity
  for (s in 1 : S) {
    for (i in 1 : 3) {
      rugosity_raw[s, i] ~ beta(rugosity[s] * phi_rug[s],
                                (1 - rugosity[s]) * phi_rug[s]);
    }
  }
  
  // Observation model
  
  for (n in 1 : N) {
    for (b in 1 : B) {
      if (D[n, b] == 0) {
        target += bernoulli_lpmf(1 | pi[n, b]); // zero-inflation
      } else {
        target += bernoulli_lpmf(0 | pi[n, b]); // non-zero inflation
        target += lognormal_lpdf(D[n, b] | mu_D[n, b], sigma_D[b]); // duration model
        if (b == 1 && D[n, b] > 0) {
          target += poisson_lpmf(bites[n] | lamba_risk[n]); // bites model
        }
      }
    }
  }
}
generated quantities {
  array[N, B] real D_pred; // predicted durations
  array[N] real bites_pred; // predicted bites
  
  // posterior predictive check
  for (n in 1 : N) {
    for (b in 1 : B) {
      if (bernoulli_rng(pi[n, b])) {
        D_pred[n, b] = 0; // zero-inflation
      } else {
        D_pred[n, b] = lognormal_rng(mu_D[n, b], sigma_D[b]);
      }
      
      if (b == 1 && D_pred[n, b] > 0) {
        bites_pred[n] = poisson_rng(lamba_risk[n]); // bites model
      } else {
        bites_pred[n] = 0;
      }
    }
  }
}
