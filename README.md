# Out of sight, out of mind: Removal of predators by fisheries alters reef fish behaviour.

## Abstract

Pervasive human activities have led to the extirpation of predator species in many  ecosystems. Understanding the extent and mechanisms by which such predator loss influences prey behaviour is critical for predicting the ecological consequences of trophic downgrading. We investigated reef fish behaviour in response to predator presence within and outside a protected area in the South Andaman Islands, India. We used 3D printed models to simulate the presence of two different types of predators; a sit-and-wait predator, a grouper (Mycteroperca rosacea) and a wide-ranging pursuit predator, a barracuda (Sphyraena barracuda). We recorded foraging, vigilance, and movement behaviours of herbivorous and invertivorous fish encountered in each plot. Overall, we found that fish were significantly more vigilant in response to both predator models compared to a non-predator control within protected areas but not outside protected areas. Foraging behaviour was suppressed by the predator treatments; however, herbivorous and invertivorous fish responded differently within protected areas. Fish movement behaviours also differed across predator treatments, prey foraging guilds, and areas. Anti-predator responses are thus highly contingent on habitat and both predator and prey traits. We highlight how the selective removal of predators by humans alters predation risk for prey and hence their risk-sensitive behaviours.



## Data

### Individuals (`data/individuals.csv`)
- **Description**: Sampled individuals in each plot.
- **Columns**:
  - `ind_id`: Unique individual ID.
  - `species`: Species identity.
  - `group`: Observed as part of a group (bool).
  - `size_class`: Approximate size class.
  - `coordinates`: Bounding box coordinates (list of integers).
  - `file`: Video file name.
  - `time_in`: Time first recorded (ms).
  - `time_out`: Time last recorded (ms).
  - `remarks`: Additional notes.

### Observations (`data/observations.csv`)
- **Description**: Behavioral observations of sampled individuals.
- **Columns**:
  - `ind_id`: Unique individual ID.
  - `time`: Time of behavior observation (ms).
  - `behaviour`: Observed behavior.

### Predators (`data/predators.csv`)
- **Description**: Predator presence in each plot.
- **Columns**:
  - `predator_id`: Unique predator observation ID.
  - `species`: Predator species.
  - `size_class`: Predator size class.
  - `time`: Time first recorded (ms).
  - `remarks`: Additional notes.

### Sites (`data/sites.csv`)
- **Description**: Sampling site information.
- **Columns**:
  - `date`: Sampling date.
  - `deployment_id`: Unique deployment ID.
  - `location`: Sampled location name.
  - `protection`: Protection status (MPA or not).
  - `time_in`: Dive start time.
  - `time_out`: Dive end time.
  - `depth_avg`: Mean depth (m).
  - `depth_max`: Max depth (m).
  - `visibility`: Visibility (m).
  - `lat`, `lon`: Latitude and longitude.
  - `crew`: Boat crew names.
  - `remarks`: Additional notes.

### Plots (`data/plots.csv`)
- **Description**: Plot-level information.
- **Columns**:
  - `index`: Unique plot ID.
  - `time`: Total sampling time (s).
  - `min_vid`, `max_vid`: Min and max video lengths (s).
  - `n_videos`: Number of videos.
  - `path`: Relative path to plot folder.

### Samples (`data/samples.csv`)
- **Description**: Subsamples within each plot (2-minute intervals).
- **Columns**:
  - `plot`: Unique plot ID.
  - `sample`: Unique subsample ID.
  - `start_time`: Subsample start time (s).
  - `video`: Video file name.
  - `status`: Completion status.

### Benthic Cover (`data/benthic-cover.csv`)
- **Description**: Benthic cover analysis of plots.
- **Columns**:
  - `plot_id`: Unique plot ID.
  - `label`: Benthic cover class label.
  - `category`: Cover class category.
  - `subcategory`: Cover class subcategory.

### Rugosity (`data/rugosity.csv`)
- **Description**: Chain transect data from each plot.
- **Columns**:
  - `deployment_id`: Unique deployment ID.
  - `treatment`: Plot treatment.
  - `sample`: Sample number.
  - `measured_length_cm`: Chain length on benthos (cm).

### Traits (`data/traits.csv`)
- **Description**: Species trait data including feeding guilds.
- **Columns**: Family, genus, species, feeding guild, and other traits.

### Behaviours (`data/behaviours.csv`)
- **Description**: List of observed behaviours and their types (State/Event).

## Usage

### Python
- Install dependencies with [uv](https://github.com/astral-sh/uv):
  ```bash
  uv sync
  ```
- Clean and standardize data:
  ```bash
  uv run cleaning.py
  ```
- Generate dashboard and data summaries:
  ```bash
  uv run summaries.py
  ```
- Run statistical models and generate figures/tables:
  ```bash
  uv run run.py
  ```

### R
- Use scripts in the `functions/` and `models/` folders for analysis:
  - `model.R`: Defines and runs the GLM.
  - `counterfactuals.R`: Runs counterfactual simulations from the GLM posterior.
  - `summary.R`: Creates summary tables for the GLM.
  - Other scripts generate tables and summaries for bite rates and time budgets.

- The R environment is managed with `renv`. To restore:
  ```R
  renv::restore()
  ```

### Notes
- Helper functions for table creation and model summaries are in the `functions/` folder.
- Analysis for bite rates and time budgets is outlined in the `models/` folder.

## License

This project is licensed under the MIT License.