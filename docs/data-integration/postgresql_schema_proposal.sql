-- RESPIRA: propuesta de esquema lógico PostgreSQL para revisión.
-- SOLO DOCUMENTACIÓN: no ejecutar, no conecta a servidor y no crea migraciones.
-- Fase 2.2: las tablas fuente se implementaron en backend/migrations/versions/0003 (esquema public, ver README);
-- este archivo conserva el diseño completo, incluidas las entidades derivadas aún no implementadas.
-- No contiene datos de pacientes, credenciales ni cargas de archivos fuente.

CREATE SCHEMA IF NOT EXISTS respira_data;

CREATE TABLE respira_data.data_source (
    source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name TEXT NOT NULL,
    institution TEXT,
    source_url TEXT,
    source_version TEXT,
    notes TEXT
);

CREATE TABLE respira_data.import_batch (
    batch_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES respira_data.data_source(source_id),
    source_filename TEXT NOT NULL,
    source_uri TEXT,
    file_sha256 CHAR(64),
    file_size_bytes BIGINT CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
    source_version TEXT,
    schema_fingerprint TEXT,
    received_at TIMESTAMPTZ,
    completeness_status TEXT NOT NULL CHECK (completeness_status IN
      ('unknown','claimed_complete','verified_complete','known_limited','rejected')),
    format_name TEXT NOT NULL,
    import_notes TEXT,
    CHECK (file_sha256 IS NULL OR file_sha256 ~ '^[0-9a-fA-F]{64}$')
);
CREATE INDEX import_batch_source_idx ON respira_data.import_batch(source_id);

CREATE TABLE respira_data.municipality (
    municipality_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    divipola_code CHAR(5) NOT NULL UNIQUE,
    municipality_name TEXT NOT NULL,
    department_code CHAR(2),
    department_name TEXT,
    CHECK (divipola_code ~ '^[0-9]{5}$')
);

CREATE TABLE respira_data.epidemiological_week (
    epi_year SMALLINT NOT NULL,
    epi_week SMALLINT NOT NULL CHECK (epi_week BETWEEN 1 AND 53),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    calendar_source_batch_id BIGINT REFERENCES respira_data.import_batch(batch_id),
    calendar_status TEXT NOT NULL CHECK (calendar_status IN ('official_verified','derived_pending_review')),
    PRIMARY KEY (epi_year, epi_week),
    CHECK (end_date >= start_date)
);

CREATE TABLE respira_data.weather_station (
    station_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ideam_station_code TEXT NOT NULL UNIQUE,
    catalog_name TEXT,
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6),
    altitude_m NUMERIC(8,2),
    station_status TEXT,
    catalog_batch_id BIGINT REFERENCES respira_data.import_batch(batch_id)
);

CREATE TABLE respira_data.station_assignment (
    assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    station_id BIGINT NOT NULL REFERENCES respira_data.weather_station(station_id),
    municipality_id BIGINT NOT NULL REFERENCES respira_data.municipality(municipality_id),
    valid_from DATE,
    valid_to DATE,
    relationship_status TEXT NOT NULL CHECK (relationship_status IN
      ('catalog_candidate','representativeness_review_pending','representative_verified','rejected')),
    evidence TEXT,
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
);

CREATE TABLE respira_data.sivigila_report (
    report_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id BIGINT NOT NULL REFERENCES respira_data.import_batch(batch_id),
    sheet_name TEXT NOT NULL,
    source_row_number BIGINT NOT NULL CHECK (source_row_number > 0),
    municipality_id BIGINT REFERENCES respira_data.municipality(municipality_id),
    epi_year SMALLINT,
    epi_week SMALLINT CHECK (epi_week IS NULL OR epi_week BETWEEN 1 AND 53),
    notification_date DATE,
    event_code TEXT,
    provider_code TEXT,
    provider_subsite_code TEXT,
    report_consecutive TEXT,
    ira_ext_under1 NUMERIC(12,2) CHECK (ira_ext_under1 IS NULL OR ira_ext_under1 >= 0),
    ira_ext_age1 NUMERIC(12,2) CHECK (ira_ext_age1 IS NULL OR ira_ext_age1 >= 0),
    ira_ext_age2_4 NUMERIC(12,2) CHECK (ira_ext_age2_4 IS NULL OR ira_ext_age2_4 >= 0),
    report_group_status TEXT NOT NULL DEFAULT 'unreviewed' CHECK (report_group_status IN
      ('unreviewed','single_report','unresolved_repeat','official_correction_confirmed','excluded_with_reason')),
    UNIQUE (batch_id, sheet_name, source_row_number)
);
CREATE INDEX sivigila_period_idx ON respira_data.sivigila_report(municipality_id, epi_year, epi_week);
CREATE INDEX sivigila_provider_group_idx ON respira_data.sivigila_report
  (provider_code, provider_subsite_code, event_code, epi_year, epi_week);
-- Intencionalmente NO hay UNIQUE para prestador/sede/evento/semana: las filas
-- repetidas necesitan revisión y conservación antes de cualquier consolidación.

CREATE TABLE respira_data.climate_observation (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id BIGINT NOT NULL REFERENCES respira_data.import_batch(batch_id),
    sheet_name TEXT NOT NULL DEFAULT '',
    source_row_number BIGINT NOT NULL CHECK (source_row_number > 0),
    station_id BIGINT REFERENCES respira_data.weather_station(station_id),
    observed_date DATE,
    variable_code TEXT NOT NULL,
    value_numeric NUMERIC(16,6),
    value_text_original TEXT,
    unit_original TEXT,
    quality_status TEXT NOT NULL CHECK (quality_status IN
      ('unknown','valid','flagged','invalid','missing','pending_semantics')),
    UNIQUE (batch_id, sheet_name, source_row_number)
);
CREATE INDEX climate_station_date_idx ON respira_data.climate_observation(station_id, observed_date, variable_code);

CREATE TABLE respira_data.annual_population (
    batch_id BIGINT NOT NULL REFERENCES respira_data.import_batch(batch_id),
    municipality_id BIGINT NOT NULL REFERENCES respira_data.municipality(municipality_id),
    reference_year SMALLINT NOT NULL,
    population_area TEXT NOT NULL,
    age_min SMALLINT NOT NULL,
    age_max SMALLINT NOT NULL,
    sex_code TEXT NOT NULL,
    population_count BIGINT NOT NULL CHECK (population_count >= 0),
    workbook_version TEXT NOT NULL,
    PRIMARY KEY (batch_id, municipality_id, reference_year, population_area, age_min, age_max, sex_code),
    CHECK (age_max >= age_min)
);

CREATE TABLE respira_data.processing_run (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    process_name TEXT NOT NULL,
    code_version TEXT NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    run_status TEXT NOT NULL CHECK (run_status IN ('planned','running','completed','failed')),
    notes TEXT
);
CREATE TABLE respira_data.processing_run_input (
    run_id BIGINT NOT NULL REFERENCES respira_data.processing_run(run_id),
    batch_id BIGINT NOT NULL REFERENCES respira_data.import_batch(batch_id),
    input_role TEXT NOT NULL,
    PRIMARY KEY (run_id, batch_id, input_role)
);

CREATE TABLE respira_data.weekly_ira_indicator (
    indicator_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES respira_data.processing_run(run_id),
    municipality_id BIGINT NOT NULL REFERENCES respira_data.municipality(municipality_id),
    epi_year SMALLINT NOT NULL,
    epi_week SMALLINT NOT NULL,
    definition_code TEXT NOT NULL,
    indicator_value NUMERIC(14,2),
    unit_label TEXT NOT NULL,
    observation_status TEXT NOT NULL CHECK (observation_status IN
      ('reported_value','reported_zero','no_source_row','unresolved_repeat','not_processed','invalid')),
    FOREIGN KEY (epi_year, epi_week) REFERENCES respira_data.epidemiological_week(epi_year, epi_week),
    UNIQUE (run_id, municipality_id, epi_year, epi_week, definition_code),
    CHECK ((observation_status IN ('reported_value','reported_zero') AND indicator_value IS NOT NULL)
        OR (observation_status NOT IN ('reported_value','reported_zero') AND indicator_value IS NULL)),
    CHECK (indicator_value IS NULL OR indicator_value >= 0)
);

CREATE TABLE respira_data.ira_report_lineage (
    indicator_id BIGINT NOT NULL REFERENCES respira_data.weekly_ira_indicator(indicator_id),
    report_id BIGINT NOT NULL REFERENCES respira_data.sivigila_report(report_id),
    contribution_role TEXT NOT NULL CHECK (contribution_role IN ('included','excluded','review_only')),
    reason TEXT,
    PRIMARY KEY (indicator_id, report_id)
);

CREATE TABLE respira_data.station_weekly_summary (
    summary_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES respira_data.processing_run(run_id),
    station_id BIGINT NOT NULL REFERENCES respira_data.weather_station(station_id),
    epi_year SMALLINT NOT NULL,
    epi_week SMALLINT NOT NULL,
    variable_code TEXT NOT NULL,
    summary_statistic TEXT NOT NULL,
    summary_value NUMERIC(16,6),
    unit_label TEXT,
    valid_day_count SMALLINT NOT NULL CHECK (valid_day_count BETWEEN 0 AND 7),
    expected_day_count SMALLINT NOT NULL CHECK (expected_day_count BETWEEN 1 AND 7),
    aggregation_rule TEXT NOT NULL,
    summary_status TEXT NOT NULL CHECK (summary_status IN ('valid','insufficient_coverage','pending_semantics','invalid')),
    FOREIGN KEY (epi_year, epi_week) REFERENCES respira_data.epidemiological_week(epi_year, epi_week),
    UNIQUE (run_id, station_id, epi_year, epi_week, variable_code, summary_statistic),
    CHECK (valid_day_count <= expected_day_count),
    CHECK ((summary_status = 'valid' AND summary_value IS NOT NULL) OR (summary_status <> 'valid' AND summary_value IS NULL))
);
CREATE TABLE respira_data.climate_summary_lineage (
    summary_id BIGINT NOT NULL REFERENCES respira_data.station_weekly_summary(summary_id),
    observation_id BIGINT NOT NULL REFERENCES respira_data.climate_observation(observation_id),
    contribution_role TEXT NOT NULL CHECK (contribution_role IN ('included','excluded')),
    reason TEXT,
    PRIMARY KEY (summary_id, observation_id)
);

CREATE TABLE respira_data.data_quality_issue (
    issue_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    batch_id BIGINT REFERENCES respira_data.import_batch(batch_id),
    entity_name TEXT NOT NULL,
    entity_key TEXT,
    issue_code TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('info','warning','blocking')),
    issue_status TEXT NOT NULL CHECK (issue_status IN ('open','resolved','accepted_with_caveat')),
    evidence TEXT,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ
);
