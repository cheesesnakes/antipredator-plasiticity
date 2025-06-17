# make sure pacman is installed and loaded
if (!requireNamespace("pacman", quietly = TRUE)) {
    install.packages("pacman")
}

# Load necessary packages

pacman::p_load("here", "dplyr", "tidyr", "flextable", "stringr")

i_am("functions/species_table.R")

folder <- "outputs/"

# 1. Comparing effects across treatments

df <- read.csv(here(folder, "species_list.csv"))

df <- df %>%
    pivot_longer(
        cols = -c("species", "abundance"),
        names_to = "guild",
        values_to = "value"
    ) %>%
    filter(value > 0) %>%
    group_by(species) %>%
    summarise(
        abundance = last(abundance),
        guild = paste(guild, collapse = ", ")
    )

table <- flextable(df) %>%
    set_header_labels(
        species = "Species",
        abundance = "Abundance",
        guild = "Guild"
    ) %>%
    set_table_properties(layout = "fixed", width = 0.9) %>%
    theme_box() %>%
    merge_v(j = "species") %>%
    align(j = "guild", align = "left", part = "body") %>%
    align(j = "abundance", align = "right", part = "body") %>%
    # make species column italic
    italic(j = "species", part = "body")

print(table)

# Save the table
save_as_docx(table, path = here("outputs", "species_table.docx"))
