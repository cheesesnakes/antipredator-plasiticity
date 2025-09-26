pacman::p_load(brms, here, tidybayes, ggplot2, marginaleffects, dplyr, tidyr, stringr)

responses <- read.csv(here("outputs", "data", "response.csv"))
predictors <- read.csv(here("outputs", "data", "predictors.csv"))

dir.create(here("outputs", "behaviour-bites"), showWarnings = FALSE)

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

moments_rugosity <- c(mean(predictors$rugosity_mean), sd(predictors$rugosity_mean))
moments_biomass <- c(mean(predictors$biomass), sd(predictors$biomass))

data <- responses %>%
  filter(bites > 0, !is.infinite(bites)) %>%
  left_join(predictors, by = c("plot_id" = "plot_id")) %>%
  select(-c(sponge)) %>%
  filter(guild != "Piscivore", guild != "Unknown")%>%
  filter(observed_duration > 45) %>%
  mutate(
    deployment_id = str_split(plot_id, "_", simplify = TRUE)[, 1],
    rugosity_mean = (rugosity_mean - moments_rugosity[1]) / moments_rugosity[2],
    biomass = (biomass - moments_biomass[1]) / moments_biomass[2],
    treatment = factor(treatment, levels = c("positive-control", "negative-control", "grouper", "barracuda")),
    protection = factor(protection, levels = c("Unprotected", "Protected")),
  ) %>%
  filter(!is.na(treatment), guild != "Unknown", guild != "") %>%
  distinct()

print(paste0("N = ", length(unique(data$ind_id)), " individuals"))

formula <- bf(bites ~ protection + treatment + rugosity_mean + biomass + group + guild + size_class + protection:guild + treatment:guild + treatment:protection + treatment:guild:protection + (1 | deployment_id) + (1 | family:species))

# priors

priors <- c(
  set_prior("normal(0,1)", class = "Intercept"),
  set_prior("normal(0,0.5)", class = "b"),
  set_prior("exponential(2)", class = "sd"),
  set_prior("exponential(1)", class = "shape")
)

# run model
model <- brm(
  formula = formula,
  prior = priors,
  data = data,
  chains = 4,
  cores = 4,
  iter = 2000,
  family = Gamma(link = "log")
)


# save model
saveRDS(model, here("outputs", "behaviour-bites", "model.rds"))

# summarise model
# p1 <- plot(model)
# ggsave(here("figures", "behaviour-bites", paste0("model_plot_", b, ".png")), plot = p1)

print(summary(model))

# posterior predictive check
p2 <- pp_check(model)
ggsave(here("figures", "behaviour-bites", "pp_check.png"), plot = p2)
