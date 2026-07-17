source("models/behaviour-time/counterfactuals.R")

# foraging

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
    # select single behaviour
    filter(behaviour == "Foraging")%>%
    ggplot(aes(x = guild, y = effect, col = treatment, shape = treatment)) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
    geom_pointinterval(aes(ymin = .lower, ymax = .upper),
        position = position_dodge(width = 0.5),
        interval_size_domain = c(1, 6),
        interval_size_range = c(1, 3)
    ) +
    labs(x = "Behaviour", y = "Log odds ratio", col = "", shape = "") +
    scale_color_brewer(palette = "Set1") +
    facet_wrap(~ protection) +
    theme(
        legend.position = "top",
        text = element_text(size = 20),
        # increase text size
        axis.title.x = element_text(size = 18),
        axis.title.y = element_text(size = 18),
        axis.text.x = element_text(size = 16),
        axis.text.y = element_text(size = 16),
        strip.text = element_text(size = 18),
        legend.text = element_text(size = 16)
    )

ggsave(here("figures", "behaviour-time", "effect_plot_foraging.png"), plot = last_plot(), width = 10, height = 6, dpi = 300)

# vigilance

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
    # select single behaviour
    filter(behaviour == "Vigilance")%>% 
    ggplot(aes(x = guild, y = effect, col = treatment, shape = treatment)) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
    geom_pointinterval(aes(ymin = .lower, ymax = .upper),
        position = position_dodge(width = 0.5),
        interval_size_domain = c(1, 6),
        interval_size_range = c(1, 3)
    ) +
    labs(x = "Behaviour", y = "Log odds ratio", col = "", shape = "") +
    scale_color_brewer(palette = "Set1") +
    facet_wrap(~ protection) +
    theme(
        legend.position = "top",
        text = element_text(size = 20),
        # increase text size
        axis.title.x = element_text(size = 18),
        axis.title.y = element_text(size = 18),
        axis.text.x = element_text(size = 16),
        axis.text.y = element_text(size = 16),
        strip.text = element_text(size = 18),
        legend.text = element_text(size = 16)
    )

ggsave(here("figures", "behaviour-time", "effect_plot_vigilance.png"), plot = last_plot(), width = 10, height = 6, dpi = 300)
