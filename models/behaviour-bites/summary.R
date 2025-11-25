pacman::p_load(brms, here, ordbetareg, tidybayes, ggplot2, marginaleffects)

source(here("functions", "summaries.R"))

dir.create(here("outputs", "behaviour-bites"), showWarnings = FALSE)

# analysis

# load models

model <- readRDS(here("outputs", "behaviour-bites", "model.rds"))

# summarise model

summarise_params(model = model, type = "Hyperparameter", vars = c("shape"), path = here("outputs", "behaviour-bites", "hyperparameters.docx"))

# Random effects

random_effects <- model %>%
    spread_draws(`r_deployment_id`[Deployment, ]) %>%
    summarise_draws() %>%
    ungroup() %>%
    select(-c(variable)) %>%
    mutate(Deployment = as.character(Deployment)) %>%
    select(Deployment, mean, median, sd, q5, q95)

# make table for random intercepts

table_re(df = random_effects, var_names = "Site", path = here("outputs", "behaviour-bites", "intercepts.docx"))

# random effects across species

random_effects_species <- model %>%
    spread_draws(`r_family:species`[l_s, ]) %>%
    summarise_draws() %>%
    ungroup() %>%
    mutate(
        Family = str_split(l_s, "_", simplify = TRUE)[, 1],
        Species = str_split(l_s, "_", simplify = TRUE)[, 2]
    ) %>%
    select(-c(l_s, variable)) %>%
    select(Family, Species, mean, median, sd, q5, q95) %>%
    arrange(Family, Species)

# tables

table_re(df = random_effects_species, var_names = "Family", path = here("outputs", "behaviour-bites", "family.docx"))

# Parameters

summarise_params(model = model, type = "Parameter", vars = c(
    "b_Intercept",
    "b_protectionProtected",
    "b_treatmentgrouper",
    "b_treatmentnegativeMcontrol",
    "b_treatmentbarracuda",
    "b_guildInvertivore",
    "b_rugosity_mean",
    "b_biomass",
    "b_group",
    "b_protectionProtected:treatmentgrouper",
    "b_protectionProtected:treatmentnegativeMcontrol",
    "b_protectionProtected:treatmentbarracuda",
    "b_treatmentgrouper:guildInvertivore",
    "b_treatmentnegativeMcontrol:guildInvertivore",
    "b_treatmentbarracuda:guildInvertivore",
    "b_protectionProtected:treatmentnegativeMcontrol:guildInvertivore",
    "b_protectionProtected:treatmentgrouper:guildInvertivore",
    "b_protectionProtected:treatmentbarracuda:guildInvertivore"), path = here("outputs", "behaviour-bites", paste0("parameters", ".docx")))

# Make tables for conditional and marginal R2

summarise_r2(model = model, path = here("outputs", "behaviour-bites", "R2.docx"))

