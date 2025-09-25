pacman::p_load(brms, here, tidybayes, ggplot2, marginaleffects, tidyr, dplyr, stringr)

# Load clean data

plot_abundance <- read.csv(here("outputs", "data", "abundance.csv"), stringsAsFactors = TRUE)
predictors <- read.csv(here("outputs", "data", "predictors.csv"), stringsAsFactors = TRUE)

dir.create(here("outputs", "abundance-plot"), showWarnings = FALSE)
dir.create(here("figures", "abundance-plot"), showWarnings = FALSE)

# Set default ggplot theme
theme_set(
  theme_bw() +
    theme(
      legend.position = "top",
      legend.text = element_text(size = 14),
      strip.text = element_text(size = 14),
      axis.title = element_text(size = 14),
      axis.text = element_text(size = 12)
    )
)

# make data frame

moments_rugosity <- c(mean(predictors$rugosity_mean), sd(predictors$rugosity_mean))
moments_biomass <- c(mean(predictors$biomass), sd(predictors$biomass))

data <- plot_abundance %>%
  left_join(predictors, by = "plot_id") %>%
  ungroup() %>%
  mutate(
    deployment_id = str_split(plot_id, "_", simplify = TRUE)[, 1],
    rugosity_mean = (rugosity_mean - moments_rugosity[1]) / moments_rugosity[2],
    biomass = (biomass - moments_biomass[1]) / moments_biomass[2],
    treatment = factor(treatment, levels = c("positive-control", "negative-control", "grouper", "barracuda")),
    protection = factor(protection, levels = c("Unprotected", "Protected")),
  ) %>%
  filter(!is.na(treatment), guild != "Unknown")

print(paste0("N = ", length(unique(data$plot_id)), " plots"))

# define formula

formula <- bf(abundance ~ protection +
  treatment + guild +
  rugosity_mean + biomass +
  protection:treatment + treatment:guild +
  (1 | deployment_id))

# priors

priors <- c(
  set_prior("normal(0,0.5)", class = "Intercept"),
  set_prior("normal(0,0.5)", class = "b"),
  set_prior("exponential(2)", class = "sd"),
  set_prior("exponential(2)", class = "shape")
)

# run the model

model <- brm(
  formula = formula,
  prior = priors,
  data = data,
  chains = 4,
  cores = 4,
  iter = 2000,
  family = negbinomial(link = "log")
)

# generate stan code

stand_code <- make_stancode(
  formula = formula,
  data = data,
  family = negbinomial(link = "log"),
  prior = priors
)

writeLines(stand_code, con = here("models", "abundance-plot", "model.stan"))

# save model
saveRDS(model, here("outputs", "abundance-plot", "model.rds"))

# summarise model
print(summary(model))

# p1 <- plot(model)
# ggsave(here("models", "behaviour-prob", paste0("model_plot_", b, ".png")), plot = p1)

# posterior predictive check
p2 <- pp_check(model)
ggsave(here("figures", "abundance-plot", paste0("pp_check.png")), plot = p2)
