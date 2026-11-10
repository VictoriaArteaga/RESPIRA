"""capa de integración de datos

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-28 13:00:00.000000

Agrega tablas nuevas (data_source, import_batch, weather_station, sivigila_report, climate_observation,
annual_population, data_quality_issue) y dos cambios compatibles sobre `municipalities`: columna opcional
`divipola_code` (única) y coordenadas opcionales. No elimina datos ni columnas, no toca `ira_cases` ni `users` y no
inserta datos. Las claves foráneas hacia `municipalities` desde las tablas nuevas son opcionales (NULL).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUSES = "('valid', 'pending', 'rejected', 'missing', 'derived')"
BIG = sa.BigInteger()


def upgrade() -> None:
    # --- municipalities: DIVIPOLA como identificador oficial; coordenadas opcionales (solo si están verificadas) ---
    op.add_column('municipalities', sa.Column('divipola_code', sa.String(length=5), nullable=True))
    op.create_unique_constraint('uq_municipalities_divipola_code', 'municipalities', ['divipola_code'])
    op.create_check_constraint('ck_municipalities_divipola_len', 'municipalities', 'divipola_code IS NULL OR length(divipola_code) = 5')
    op.create_check_constraint('ck_municipalities_divipola_format', 'municipalities', "divipola_code ~ '^[0-9]{5}$'")
    op.alter_column('municipalities', 'latitude', existing_type=sa.Float(), nullable=True)
    op.alter_column('municipalities', 'longitude', existing_type=sa.Float(), nullable=True)
    op.create_check_constraint('ck_municipalities_coordinates_paired', 'municipalities', '(latitude IS NULL) = (longitude IS NULL)')

    op.create_table('data_source',
    sa.Column('id', BIG, sa.Identity(always=False), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('institution', sa.String(length=200), nullable=True),
    sa.Column('source_url', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )

    op.create_table('import_batch',
    sa.Column('id', BIG, sa.Identity(always=False), nullable=False),
    sa.Column('source_id', BIG, nullable=False),
    sa.Column('source_filename', sa.String(length=300), nullable=False),
    sa.Column('file_sha256', sa.String(length=64), nullable=True),
    sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
    sa.Column('source_version', sa.String(length=100), nullable=True),
    sa.Column('schema_fingerprint', sa.String(length=64), nullable=True),
    sa.Column('format_name', sa.String(length=60), nullable=False),
    sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('transformation_version', sa.String(length=40), nullable=False),
    sa.Column('rows_read', sa.BigInteger(), nullable=True),
    sa.Column('completeness_status', sa.String(length=20), server_default=sa.text("'unknown'"), nullable=False),
    sa.Column('validation_status', sa.String(length=20), server_default=sa.text("'pending'"), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.CheckConstraint('file_size_bytes IS NULL OR file_size_bytes >= 0', name='ck_import_batch_size_non_negative'),
    sa.CheckConstraint("completeness_status IN ('unknown', 'claimed_complete', 'verified_complete', 'known_limited', 'rejected')", name='ck_import_batch_completeness_valid'),
    sa.CheckConstraint(f'validation_status IN {STATUSES}', name='ck_import_batch_validation_valid'),
    sa.CheckConstraint('file_sha256 IS NULL OR length(file_sha256) = 64', name='ck_import_batch_sha256_length'),
    sa.CheckConstraint("file_sha256 ~ '^[0-9a-f]{64}$'", name='ck_import_batch_sha256_hex'),
    sa.ForeignKeyConstraint(['source_id'], ['data_source.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_import_batch_source_id', 'import_batch', ['source_id'], unique=False)
    op.create_index('uq_import_batch_source_sha256', 'import_batch', ['source_id', 'file_sha256'], unique=True, postgresql_where=sa.text('file_sha256 IS NOT NULL'))

    op.create_table('weather_station',
    sa.Column('id', BIG, sa.Identity(always=False), nullable=False),
    sa.Column('ideam_station_code', sa.String(length=20), nullable=False),
    sa.Column('catalog_name', sa.String(length=200), nullable=True),
    sa.Column('municipality_code', sa.String(length=5), nullable=True),
    sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('altitude_m', sa.Numeric(precision=8, scale=2), nullable=True),
    sa.Column('station_status', sa.String(length=60), nullable=True),
    sa.Column('catalog_batch_id', BIG, nullable=True),
    sa.Column('validation_status', sa.String(length=20), server_default=sa.text("'pending'"), nullable=False),
    sa.CheckConstraint(f'validation_status IN {STATUSES}', name='ck_weather_station_validation_valid'),
    sa.CheckConstraint('latitude IS NULL OR latitude BETWEEN -90 AND 90', name='ck_weather_station_latitude_range'),
    sa.CheckConstraint('longitude IS NULL OR longitude BETWEEN -180 AND 180', name='ck_weather_station_longitude_range'),
    sa.ForeignKeyConstraint(['catalog_batch_id'], ['import_batch.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ideam_station_code')
    )

    op.create_table('sivigila_report',
    sa.Column('id', BIG, sa.Identity(always=False), nullable=False),
    sa.Column('batch_id', BIG, nullable=False),
    sa.Column('sheet_name', sa.String(length=100), nullable=False),
    sa.Column('source_row_number', sa.BigInteger(), nullable=False),
    sa.Column('municipality_code', sa.String(length=5), nullable=True),
    sa.Column('municipality_id', sa.Integer(), nullable=True),
    sa.Column('epi_year', sa.SmallInteger(), nullable=True),
    sa.Column('epi_week', sa.SmallInteger(), nullable=True),
    sa.Column('notification_date', sa.Date(), nullable=True),
    sa.Column('event_code', sa.String(length=10), nullable=True),
    sa.Column('provider_code', sa.String(length=30), nullable=True),
    sa.Column('provider_subsite_code', sa.String(length=30), nullable=True),
    sa.Column('report_consecutive', sa.String(length=30), nullable=True),
    sa.Column('ira_ext_under1', sa.Integer(), nullable=True),
    sa.Column('ira_ext_age1', sa.Integer(), nullable=True),
    sa.Column('ira_ext_age2_4', sa.Integer(), nullable=True),
    sa.Column('validation_status', sa.String(length=20), server_default=sa.text("'pending'"), nullable=False),
    sa.Column('report_group_status', sa.String(length=40), server_default=sa.text("'unreviewed'"), nullable=False),
    sa.CheckConstraint('source_row_number > 0', name='ck_sivigila_report_row_positive'),
    sa.CheckConstraint('epi_year IS NULL OR epi_year BETWEEN 2000 AND 2100', name='ck_sivigila_report_year_range'),
    sa.CheckConstraint('epi_week IS NULL OR epi_week BETWEEN 1 AND 53', name='ck_sivigila_report_week_range'),
    sa.CheckConstraint('municipality_code IS NULL OR length(municipality_code) = 5', name='ck_sivigila_report_muni_len'),
    sa.CheckConstraint("municipality_code ~ '^[0-9]{5}$'", name='ck_sivigila_report_muni_format'),
    sa.CheckConstraint('ira_ext_under1 IS NULL OR ira_ext_under1 >= 0', name='ck_sivigila_report_under1_non_negative'),
    sa.CheckConstraint('ira_ext_age1 IS NULL OR ira_ext_age1 >= 0', name='ck_sivigila_report_age1_non_negative'),
    sa.CheckConstraint('ira_ext_age2_4 IS NULL OR ira_ext_age2_4 >= 0', name='ck_sivigila_report_age2_4_non_negative'),
    sa.CheckConstraint(f'validation_status IN {STATUSES}', name='ck_sivigila_report_validation_valid'),
    sa.CheckConstraint("report_group_status IN ('unreviewed', 'single_report', 'unresolved_repeat', 'official_correction_confirmed', 'excluded_with_reason')", name='ck_sivigila_report_group_valid'),
    sa.CheckConstraint("validation_status <> 'valid' OR (epi_year IS NOT NULL AND epi_week IS NOT NULL AND municipality_code IS NOT NULL)", name='ck_sivigila_report_valid_requires_period'),
    sa.ForeignKeyConstraint(['batch_id'], ['import_batch.id'], ),
    sa.ForeignKeyConstraint(['municipality_id'], ['municipalities.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('batch_id', 'sheet_name', 'source_row_number', name='uq_sivigila_report_source_row')
    )
    op.create_index('ix_sivigila_report_batch_id', 'sivigila_report', ['batch_id'], unique=False)
    op.create_index('ix_sivigila_report_municipality_id', 'sivigila_report', ['municipality_id'], unique=False)
    op.create_index('ix_sivigila_report_period', 'sivigila_report', ['municipality_code', 'epi_year', 'epi_week'], unique=False)
    op.create_index('ix_sivigila_report_provider_group', 'sivigila_report', ['provider_code', 'provider_subsite_code', 'epi_year', 'epi_week'], unique=False)

    op.create_table('climate_observation',
    sa.Column('id', BIG, sa.Identity(always=False), nullable=False),
    sa.Column('batch_id', BIG, nullable=False),
    sa.Column('sheet_name', sa.String(length=100), server_default=sa.text("''"), nullable=False),
    sa.Column('source_row_number', sa.BigInteger(), nullable=False),
    sa.Column('station_id', BIG, nullable=True),
    sa.Column('station_code_source', sa.String(length=20), nullable=True),
    sa.Column('observed_date', sa.Date(), nullable=True),
    sa.Column('variable_code', sa.String(length=40), nullable=False),
    sa.Column('value_numeric', sa.Numeric(precision=16, scale=6), nullable=True),
    sa.Column('value_text_original', sa.String(length=60), nullable=True),
    sa.Column('unit_original', sa.String(length=30), nullable=True),
    sa.Column('validation_status', sa.String(length=20), server_default=sa.text("'pending'"), nullable=False),
    sa.CheckConstraint('source_row_number > 0', name='ck_climate_observation_row_positive'),
    sa.CheckConstraint(f'validation_status IN {STATUSES}', name='ck_climate_observation_validation_valid'),
    sa.CheckConstraint("validation_status <> 'missing' OR value_numeric IS NULL", name='ck_climate_observation_missing_is_null'),
    sa.CheckConstraint("validation_status <> 'valid' OR (value_numeric IS NOT NULL AND observed_date IS NOT NULL AND station_id IS NOT NULL)", name='ck_climate_observation_valid_requires_value'),
    sa.ForeignKeyConstraint(['batch_id'], ['import_batch.id'], ),
    sa.ForeignKeyConstraint(['station_id'], ['weather_station.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('batch_id', 'sheet_name', 'source_row_number', name='uq_climate_observation_source_row')
    )
    op.create_index('ix_climate_observation_batch_id', 'climate_observation', ['batch_id'], unique=False)
    op.create_index('ix_climate_observation_station_date', 'climate_observation', ['station_id', 'observed_date', 'variable_code'], unique=False)

    op.create_table('annual_population',
    sa.Column('id', BIG, sa.Identity(always=False), nullable=False),
    sa.Column('batch_id', BIG, nullable=False),
    sa.Column('municipality_code', sa.String(length=5), nullable=False),
    sa.Column('municipality_id', sa.Integer(), nullable=True),
    sa.Column('reference_year', sa.SmallInteger(), nullable=False),
    sa.Column('population_area', sa.String(length=30), nullable=False),
    sa.Column('age_min', sa.SmallInteger(), nullable=False),
    sa.Column('age_max', sa.SmallInteger(), nullable=False),
    sa.Column('sex_code', sa.String(length=20), nullable=False),
    sa.Column('population_count', sa.BigInteger(), nullable=True),
    sa.Column('workbook_version', sa.String(length=100), nullable=True),
    sa.Column('validation_status', sa.String(length=20), server_default=sa.text("'pending'"), nullable=False),
    sa.CheckConstraint('population_count IS NULL OR population_count >= 0', name='ck_annual_population_non_negative'),
    sa.CheckConstraint('reference_year BETWEEN 1950 AND 2100', name='ck_annual_population_year_range'),
    sa.CheckConstraint('age_min >= 0 AND age_max >= age_min', name='ck_annual_population_age_range'),
    sa.CheckConstraint('length(municipality_code) = 5', name='ck_annual_population_muni_len'),
    sa.CheckConstraint("municipality_code ~ '^[0-9]{5}$'", name='ck_annual_population_muni_format'),
    sa.CheckConstraint(f'validation_status IN {STATUSES}', name='ck_annual_population_validation_valid'),
    sa.CheckConstraint("validation_status <> 'missing' OR population_count IS NULL", name='ck_annual_population_missing_is_null'),
    sa.ForeignKeyConstraint(['batch_id'], ['import_batch.id'], ),
    sa.ForeignKeyConstraint(['municipality_id'], ['municipalities.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('batch_id', 'municipality_code', 'reference_year', 'population_area', 'age_min', 'age_max', 'sex_code', name='uq_annual_population_key')
    )
    op.create_index('ix_annual_population_batch_id', 'annual_population', ['batch_id'], unique=False)
    op.create_index('ix_annual_population_municipality', 'annual_population', ['municipality_code', 'reference_year'], unique=False)

    op.create_table('data_quality_issue',
    sa.Column('id', BIG, sa.Identity(always=False), nullable=False),
    sa.Column('batch_id', BIG, nullable=True),
    sa.Column('entity_name', sa.String(length=60), nullable=False),
    sa.Column('sheet_name', sa.String(length=100), nullable=True),
    sa.Column('source_row_number', sa.BigInteger(), nullable=True),
    sa.Column('entity_key', sa.String(length=200), nullable=True),
    sa.Column('issue_code', sa.String(length=80), nullable=False),
    sa.Column('severity', sa.String(length=10), nullable=False),
    sa.Column('issue_status', sa.String(length=25), server_default=sa.text("'open'"), nullable=False),
    sa.Column('evidence', sa.Text(), nullable=True),
    sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("severity IN ('info', 'warning', 'blocking')", name='ck_data_quality_issue_severity_valid'),
    sa.CheckConstraint("issue_status IN ('open', 'resolved', 'accepted_with_caveat')", name='ck_data_quality_issue_status_valid'),
    sa.ForeignKeyConstraint(['batch_id'], ['import_batch.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_data_quality_issue_batch_id', 'data_quality_issue', ['batch_id'], unique=False)
    op.create_index('ix_data_quality_issue_code', 'data_quality_issue', ['issue_code'], unique=False)


def downgrade() -> None:
    """Elimina únicamente las tablas de 0003, en orden inverso de dependencias.

    Es destructivo para los datos de integración que se hayan cargado y elimina `municipalities.divipola_code`; no
    afecta a `ira_cases` ni `users`. Con las tablas vacías (estado esperado antes de la primera importación) no se pierde información.
    """
    op.drop_table('data_quality_issue')
    op.drop_table('annual_population')
    op.drop_table('climate_observation')
    op.drop_table('sivigila_report')
    op.drop_table('weather_station')
    op.drop_table('import_batch')
    op.drop_table('data_source')
    op.drop_constraint('ck_municipalities_coordinates_paired', 'municipalities', type_='check')
    # Falla (sin perder datos) si ya existen municipios sin coordenadas: se deben completar o eliminar antes de revertir.
    op.alter_column('municipalities', 'longitude', existing_type=sa.Float(), nullable=False)
    op.alter_column('municipalities', 'latitude', existing_type=sa.Float(), nullable=False)
    op.drop_constraint('ck_municipalities_divipola_format', 'municipalities', type_='check')
    op.drop_constraint('ck_municipalities_divipola_len', 'municipalities', type_='check')
    op.drop_constraint('uq_municipalities_divipola_code', 'municipalities', type_='unique')
    op.drop_column('municipalities', 'divipola_code')
