pacman::p_load(brms, here, ordbetareg, tidybayes, ggplot2, marginaleffects, flextable)

responses <- read.csv(here("outputs", "data", "response.csv"))
predictors <- read.csv(here("outputs", "data", "predictors.csv"))

source(here("functions", "summaries.R"))


moments_rugosity <- c(mean(predictors$rugosity_mean), sd(predictors$rugosity_mean))
moments_biomass <- c(mean(predictors$biomass), sd(predictors$biomass))

data <- responses %>%
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

dir.create(here("outputs", "behaviour-time"), showWarnings = FALSE)
dir.create(here("figures", "behaviour-time"), showWarnings = FALSE)

# analysis

behaviours <- c("foraging", "vigilance", "movement")
counterfactual_treatment <- data.frame()

for (b in behaviours) {
    # load models

    model <- readRDS(here("outputs", "behaviour-time", paste0("model_", b, ".rds")))

    # plot posterior proportions by protection

    posterior_treatment <- data %>%
        ungroup() %>%
        select(ind_id, plot_id, deployment_id, family, species, guild, size_class, protection, group, rugosity_mean, biomass) %>%
        distinct() %>%
        expand_grid(treatment = c("positive-control", "negative-control", "grouper", "barracuda")) %>%
        add_epred_draws(model, value = "prop") %>%
        ungroup() %>%
        mutate(behaviour = str_to_title(b))


    counterfactual_treatment <- rbind(counterfactual_treatment, posterior_treatment)

}

# Calculate and summarise effect

effect <- counterfactual_treatment %>%
    pivot_wider(names_from = treatment, values_from = prop, id_cols = c(".draw", "ind_id", "plot_id", "deployment_id", "protection", "size_class", "guild", "behaviour", "rugosity_mean", "biomass")) %>%
    mutate(
        effect_grouper = log2(grouper/(1-grouper)) - log2(`positive-control`/(1-`positive-control`)),
        effect_barracuda = log2(barracuda/(1-barracuda)) - log2(`positive-control`/(1-`positive-control`)),
        effect_control = log2(`positive-control`/(1-`positive-control`)) - log2(`negative-control`/(1-`negative-control`))
    ) %>%
    select(.draw, plot_id, deployment_id, protection, size_class, guild, behaviour, effect_grouper, effect_barracuda, effect_control) %>%
    pivot_longer(cols = starts_with("effect"), names_to = "treatment", values_to = "effect") %>%
    mutate(treatment = recode(treatment, effect_grouper = "grouper", effect_barracuda = "barracuda", effect_control = "control"))


head(effect)

# Counterfactual effect of control on number individuals in plot

effect %>%
    filter(treatment == "control") %>%
    group_by(treatment, behaviour, guild, protection) %>%
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
    ggplot(aes(x = behaviour, y = effect, col = protection, shape = protection)) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
    geom_pointinterval(aes(ymin = .lower, ymax = .upper), position = position_dodge(width = 0.5)) +
    labs(x = "Behaviour", y = "Log odds ratio", col = "", shape = "") +
    facet_wrap(~guild)+
    theme(text = element_text(size = 16)) 

ggsave(here("figures", "behaviour-time", "control_plot.png"), plot = last_plot(), width = 10, height = 6)

# Summary control

P <- effect %>%
    filter(treatment == "control") %>%
    group_by(behaviour, treatment) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment == "control") %>%
    group_by(behaviour, treatment) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(behaviour, treatment, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)


table <- effect_summary %>%
    arrange(behaviour, treatment) %>%
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

save_as_docx(table, path = here("outputs", "behaviour-time", "counterfactual_control.docx"))

# Counterfactual effect of treatment on number individuals in plot

effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, behaviour, guild, protection) %>%
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
    # set x order to formation, vigilance, movement
    mutate(behaviour = factor(behaviour, levels = c("Foraging", "Vigilance", "Movement"))) %>%
    ggplot(aes(x = behaviour, y = effect, col = protection, shape = protection)) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
    geom_pointinterval(aes(ymin = .lower, ymax = .upper), position = position_dodge(width = 0.5),
                       interval_size_domain = c(1, 6),
                       interval_size_range = c(1, 3)) +
    labs(x = "Behaviour", y = "Log odds ratio", col = "", shape = "") +
    scale_color_brewer(palette = "Set1") +
    facet_grid(guild~treatment)+
    theme(legend.position = "top", 
    text = element_text(size = 20),
    # increase text size
    axis.title.x = element_text(size = 18),
    axis.title.y = element_text(size = 18),
    axis.text.x = element_text(size = 16),    
    axis.text.y = element_text(size = 16),
    strip.text = element_text(size = 18),
    legend.text = element_text(size = 16))

ggsave(here("figures", "behaviour-time", "effect_plot.png"), plot = last_plot(), width = 10, height = 10, dpi = 300)

# Summary table

## Full

P <- effect %>%
    filter(treatment != "control") %>%
    filter(guild %in% c("Herbivore", "Invertivore")) %>%
    group_by(treatment, behaviour, guild, protection) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment != "control") %>%
    filter(guild %in% c("Herbivore", "Invertivore")) %>%
    group_by(treatment, behaviour, guild, protection) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(behaviour, treatment, guild, protection, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)

table <- effect_summary %>%
    arrange(behaviour, treatment, guild, protection) %>%
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
        behaviour = "Behaviour",
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

save_as_docx(table, path = here("outputs", "behaviour-time", "counterfactual_treatment_guild_protection.docx"))

## Treatmen x protection

P <- effect %>%
    filter(treatment != "control") %>%
    group_by(behaviour, treatment, protection) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment != "control") %>%
    group_by(behaviour, treatment, protection) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(behaviour, treatment, protection, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)


table <- effect_summary %>%
    filter(treatment != "control") %>%
    arrange(behaviour, treatment, protection) %>%
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

save_as_docx(table, path = here("outputs", "behaviour-time", "counterfactual_treatment_protection.docx"))

## Treatment x Guild

P <- effect %>%
    filter(treatment != "control") %>%
    group_by(behaviour, treatment, guild) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment != "control") %>%
    group_by(behaviour, treatment, guild) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(behaviour, treatment, guild, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)


table <- effect_summary %>%
    arrange(behaviour, treatment, guild) %>%
    filter(guild %in% c("Herbivore", "Invertivore")) %>%
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

save_as_docx(table, path = here("outputs", "behaviour-time", "counterfactual_treatment_guild.docx"))
