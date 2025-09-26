pacman::p_load(brms, here, tidybayes, ggplot2, marginaleffects, flextable)

# Load clean data

plot_abundance <- read.csv(here("outputs", "data", "abundance.csv"), stringsAsFactors = TRUE)
predictors <- read.csv(here("outputs", "data", "predictors.csv"), stringsAsFactors = TRUE)

source(here("functions", "summaries.R"))

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
        guild = factor(guild, levels = c("Herbivore", "Invertivore", "Piscivore"))
    ) %>%
    filter(!is.na(treatment), !is.na(guild))

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

dir.create(here("outputs", "abundance-plot"), showWarnings = FALSE)
dir.create(here("figures", "abundance-plot"), showWarnings = FALSE)

# analysis

# load models

model <- readRDS(here("outputs", "abundance-plot", paste0("model.rds")))

# plot posterior proportions by treatment

posterior_treatment <- data %>%
    ungroup() %>%
    select(plot_id, deployment_id, guild, protection, rugosity_mean, biomass) %>%
    distinct() %>%
    expand_grid(treatment = c("positive-control", "negative-control", "grouper", "barracuda")) %>%
    add_epred_draws(model, value = "prop") %>%
    ungroup()

# Calculate and summarise effect

effect <- posterior_treatment %>%
    pivot_wider(names_from = treatment, values_from = prop, id_cols = c(".draw", "plot_id", "deployment_id", "protection", "guild", "rugosity_mean", "biomass")) %>%
    mutate(
        effect_grouper = log2(grouper) - log2(`positive-control`),
        effect_barracuda = log2(barracuda) - log2(`positive-control`),
        effect_control = log2(`positive-control`) - log2(`negative-control`)
    ) %>%
    select(.draw, plot_id, deployment_id, protection, guild, effect_grouper, effect_barracuda, effect_control) %>%
    pivot_longer(cols = starts_with("effect"), names_to = "treatment", values_to = "effect") %>%
    mutate(treatment = recode(treatment, effect_grouper = "grouper", effect_barracuda = "barracuda", effect_control = "control"))

head(effect)

# Counterfactual effect of control on number individuals in plot

effect %>%
    filter(treatment == "control") %>%
    group_by(treatment, guild, protection) %>%
    mutate(
        protection = case_when(
            protection == "Protected" ~ "Inside PA",
            protection == "Unprotected" ~ "Outside PA"
        ),
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    filter(guild %in% c("Herbivore", "Invertivore")) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    ggplot(aes(x = guild, y = effect, col = protection)) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
    geom_pointinterval(aes(ymin = .lower, ymax = .upper), position = position_dodge(width = 0.5)) +
    labs(x = "Guild", y = "Log odds ratio", col = "") 

ggsave(here("figures", "abundance-plot", "control_plot.png"), plot = last_plot(), width = 10, height = 6)

# Summary control

P <- effect %>%
    filter(treatment == "control") %>%
    group_by(treatment) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment == "control") %>%
    group_by(treatment) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(treatment, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)


table <- effect_summary %>%
    arrange(treatment) %>%
    mutate(
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    mutate(across(where(is.numeric), ~ round(., 3))) %>%
    flextable() %>%
    set_header_labels(
        behaviour = "Behaviour",
        treatment = "Treatment",
        protection = "Protection",
        effect = "Median",
        .lower_0.9 = "90% Lower CI",
        .lower_0.5 = "50% Lower CI",
        .upper_0.5 = "50% Upper CI",
        .upper_0.9 = "90% Upper CI",
        P = "P(>0)"
    ) %>%
    merge_v(j = ) %>%
    theme_box() %>%
    set_table_properties(width = 0.5, layout = "fixed")

print(table)

save_as_docx(table, path = here("outputs", "abundance-plot", "counterfactual_control.docx"))

# Counterfactual effect of treatment on number individuals in plot

effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, guild, protection) %>%
    mutate(
        protection = case_when(
            protection == "Protected" ~ "Inside PA",
            protection == "Unprotected" ~ "Outside PA"
        ),
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    ggplot(aes(x = guild, y = effect, col = protection)) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
    geom_pointinterval(aes(ymin = .lower, ymax = .upper), position = position_dodge(width = 0.5)) +
    labs(x = "Foraging Guild", y = "Log response ratio", col = "") +
    facet_wrap(~treatment)

ggsave(here("figures", "abundance-plot", "effect_plot.png"), plot = last_plot(), width = 10, height = 6)

# Summary table

## Full

P <- effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, guild, protection) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, guild, protection) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(treatment, guild, protection, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)

table <- effect_summary %>%
    mutate(
        protection = case_when(
            protection == "Protected" ~ "Inside PA",
            protection == "Unprotected" ~ "Outside PA"
        ),
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    mutate(across(where(is.numeric), ~ round(., 3))) %>%
    flextable() %>%
    set_header_labels(
        treatment = "Treatment",
        protection = "Protection",
        guild = "Foraging Guild",
        effect = "Median",
        .lower_0.9 = "90% Lower CI",
        .lower_0.5 = "50% Lower CI",
        .upper_0.5 = "50% Upper CI",
        .upper_0.9 = "90% Upper CI",
        P = "P(>0)"
    ) %>%
    merge_v(j = ) %>%
    theme_box() %>%
    set_table_properties(width = 0.5, layout = "fixed")

print(table)

save_as_docx(table, path = here("outputs", "abundance-plot", "counterfactual_treatment_guild_protection.docx"))

## Treatmen x protection

P <- effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, protection) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, protection) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(treatment, protection, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)


table <- effect_summary %>%
    mutate(
        protection = case_when(
            protection == "Protected" ~ "Inside PA",
            protection == "Unprotected" ~ "Outside PA"
        ),
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    flextable() %>%
    mutate(across(where(is.numeric), ~ round(., 3))) %>%
    set_header_labels(
        treatment = "Treatment",
        protection = "Protection",
        effect = "Median",
        .lower_0.9 = "90% Lower CI",
        .lower_0.5 = "50% Lower CI",
        .upper_0.5 = "50% Upper CI",
        .upper_0.9 = "90% Upper CI",
        P = "P(>0)"
    ) %>%
    merge_v(j = ) %>%
    theme_box() %>%
    set_table_properties(width = 0.5, layout = "fixed")

print(table)

save_as_docx(table, path = here("outputs", "abundance-plot", "counterfactual_treatment_protection.docx"))

## Treatment x Guild

P <- effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, guild) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, guild) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(treatment, guild, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)


table <- effect_summary %>%
    mutate(
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    flextable() %>%
    mutate(across(where(is.numeric), ~ round(., 3))) %>%
    set_header_labels(
        treatment = "Treatment",
        guild = "Foraging Guild",
        effect = "Median",
        .lower_0.9 = "90% Lower CI",
        .lower_0.5 = "50% Lower CI",
        .upper_0.5 = "50% Upper CI",
        .upper_0.9 = "90% Upper CI",
        P = "P(>0)"
    ) %>%
    merge_v(j = ) %>%
    theme_box() %>%
    set_table_properties(width = 0.5, layout = "fixed")

print(table)

save_as_docx(table, path = here("outputs", "abundance-plot", "counterfactual_treatment_guild.docx"))
