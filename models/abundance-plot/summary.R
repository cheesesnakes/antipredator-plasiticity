pacman::p_load(brms, here, tidybayes, ggplot2, marginaleffects, flextable)

source(here("functions", "summaries.R"))

dir.create(here("outputs", "abundance-plot"), showWarnings = FALSE)

# analysis

# load models

model <- readRDS(here("outputs", "abundance-plot", paste0("model.rds")))

# Random effects

random_effects <- model %>%
    spread_draws(`r_deployment_id`[Deployment, ]) %>%
    summarise_draws() %>%
    ungroup() %>%
    select(-c(variable)) %>%
    mutate(Deployment = as.character(Deployment)) %>%
    select(Deployment, mean, median, sd, q5, q95)

# make table for random intercepts

table_re(df = random_effects, var_names = "Deployment", path = here("outputs", "abundance-plot", "intercepts.docx"))

# Parameters

get_variables(model)

summarise_params(model, type = "Fixed", vars = c(
    "b_Intercept",
    "b_protectionProtected",
    "b_treatmentgrouper",
    "b_treatmentnegativeMcontrol",
    "b_treatmentbarracuda",
    "b_guildInvertivore",
    "b_guildPiscivore",
    "b_rugosity_mean",
    "b_biomass",
    "b_protectionProtected:treatmentgrouper",
    "b_protectionProtected:treatmentnegativeMcontrol",
    "b_protectionProtected:treatmentbarracuda",
    "b_treatmentgrouper:guildInvertivore",
    "b_treatmentnegativeMcontrol:guildInvertivore",
    "b_treatmentbarracuda:guildInvertivore",
    "b_treatmentgrouper:guildPiscivore",
    "b_treatmentnegativeMcontrol:guildPiscivore",
    "b_treatmentbarracuda:guildPiscivore",
    "shape"
), path = here("outputs", "abundance-plot", "fixed_effects.docx"))

# Make tables for conditional and marginal R2

summarise_r2(model, path = here("outputs", "abundance-plot", "R2.docx"))
