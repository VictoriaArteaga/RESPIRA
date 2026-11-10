from datetime import date

import pytest

from app.importers import dane, ideam, sivigila
from app.importers.common import ImporterError, normalize_divipola, parse_integer

KNOWN = frozenset({"52001", "52240"})


def siv(**overrides):
    raw = dict(event_code="995", municipality_code="52240", epi_year=2016, epi_week=43, provider_code="P1", provider_subsite_code="1",
               report_consecutive="263", ira_ext_under1=3, ira_ext_age1=2, ira_ext_age2_4=1)
    raw.update(overrides)
    return sivigila.validate_row(raw, sheet_name="995", source_row_number=2, known_municipality_codes=KNOWN)


def codes(row):
    return {i.code for i in row.issues}


# ---------------------------------------------------------------- utilidades

def test_divipola_keeps_leading_zeros_and_rejects_garbage():
    assert normalize_divipola(5001) == "05001"
    assert normalize_divipola("52240.0") == "52240"
    for bad in (None, "", "abc", "123456", "5 2", "NA"):
        assert normalize_divipola(bad) is None


def test_parse_integer_is_strict():
    assert parse_integer("3") == 3 and parse_integer(3.0) == 3
    for bad in ("3.5", "abc", True, float("nan")):
        with pytest.raises(ValueError):
            parse_integer(bad)


# ------------------------------------------------------------------ SIVIGILA

def test_sivigila_valid_row():
    row = siv()
    assert row.status == "valid" and not row.issues
    assert row.record["report_consecutive"] == "263"


@pytest.mark.parametrize("override,code", [
    ({"epi_week": 0}, "week_out_of_range"),
    ({"epi_week": 54}, "week_out_of_range"),
    ({"epi_week": "x"}, "epi_week_not_integer"),
    ({"epi_week": None}, "epi_week_missing"),
    ({"epi_year": 1999}, "year_out_of_range"),
    ({"epi_year": None}, "epi_year_missing"),
    ({"municipality_code": "99999"}, "municipality_unknown"),
    ({"municipality_code": "abc"}, "municipality_code_invalid"),
    ({"event_code": "100"}, "event_code_unexpected"),
    ({"ira_ext_age1": -2}, "ira_ext_age1_negative"),
    ({"ira_ext_age1": 1.5}, "ira_ext_age1_not_integer"),
    ({"ira_ext_age1": "abc"}, "ira_ext_age1_not_integer"),
])
def test_sivigila_rejections(override, code):
    row = siv(**override)
    assert row.status == "rejected" and code in codes(row)


def test_sivigila_missing_counts_are_never_zero():
    row = siv(ira_ext_under1=None, ira_ext_age1="", ira_ext_age2_4="NA")
    assert row.status == "missing"
    assert [row.record[k] for k in sivigila.COUNT_FIELDS] == [None, None, None]


def test_sivigila_partial_counts_stay_null_and_pending():
    row = siv(ira_ext_age1=None)
    assert row.status == "pending" and row.record["ira_ext_age1"] is None and row.record["ira_ext_under1"] == 3


def test_sivigila_zero_is_a_real_value():
    row = siv(ira_ext_under1=0, ira_ext_age1=0, ira_ext_age2_4=0)
    assert row.status == "valid" and row.record["ira_ext_under1"] == 0


def test_sivigila_week_53_pending_until_calendar_is_verified():
    assert siv(epi_week=53).status == "pending"
    verified = sivigila.validate_row(dict(event_code="995", municipality_code="52240", epi_year=2020, epi_week=53, provider_code="P", report_consecutive="1",
                                          ira_ext_under1=1, ira_ext_age1=1, ira_ext_age2_4=1), sheet_name="s", source_row_number=2, years_with_53_weeks=frozenset({2020}))
    assert verified.status == "valid"


def test_sivigila_bad_notification_date_does_not_reject():
    row = siv(notification_date="not a date")
    assert row.status == "valid" and row.record["notification_date"] is None and "notification_date_invalid" in codes(row)


def test_sivigila_repeats_are_flagged_not_dropped_or_merged():
    """D-01: mismo prestador-semana con distinto NUM_CON → dos filas conservadas, ambas 'unresolved_repeat'."""
    rows = [siv(report_consecutive="263", ira_ext_under1=8), siv(report_consecutive="264", ira_ext_under1=1), siv(provider_code="OTHER")]
    assert sivigila.flag_repeats(rows) == 1
    assert [r.record["report_group_status"] for r in rows] == ["unresolved_repeat", "unresolved_repeat", "single_report"]
    assert [r.record["ira_ext_under1"] for r in rows[:2]] == [8, 1]  # valores originales intactos
    assert all(r.status == "valid" for r in rows)  # una repetición no invalida la fila


def test_sivigila_columns_resolved_by_name_not_position():
    mapping = sivigila.resolve_columns(["X", "COD_EVE", "Año", "Semana", "COD_MUN", "COD_PRE", "NUM_CON", "IRACEXT_1", "IRACEXT_2", "IRACEXT_3", "extra"])
    assert mapping["epi_year"] == 2 and mapping["municipality_code"] == 4


def test_sivigila_missing_required_columns_fail_the_batch():
    with pytest.raises(ImporterError, match="semana|epi_week"):
        sivigila.resolve_columns(["cod_eve", "año", "cod_mun", "cod_pre", "num_con", "iracext_1", "iracext_2", "iracext_3"])


# --------------------------------------------------------------------- IDEAM

def obs(value="12.5", date_text="2016-01-03 07:00:00", variable="TSSM_MN_D", station="52045020", **kw):
    return ideam.validate_observation({"date": date_text, "value": value}, station_code=station, variable_code=variable, source_row_number=2,
                                      known_station_codes=kw.get("known"), today=date(2026, 1, 1))


def test_ideam_valid_observation():
    row = obs()
    assert row.status == "valid" and row.record["value_numeric"] == 12.5 and row.record["unit_original"] == "°C"
    assert row.record["observed_date"] == date(2016, 1, 3)


def test_ideam_negative_temperature_is_allowed_but_negative_precipitation_is_not():
    assert obs("-3.0").status == "valid"
    assert obs("-1", variable="PTPM_CON_INTER").status == "rejected"


@pytest.mark.parametrize("value", ["", "  ", "NA", "NaN"])
def test_ideam_missing_value_is_null_not_zero(value):
    row = obs(value)
    assert row.status == "missing" and row.record["value_numeric"] is None


def test_ideam_zero_precipitation_is_kept_as_pending_semantics():
    row = obs("0.0", variable="PTPM_CON_INTER")
    assert row.record["value_numeric"] == 0.0 and row.status == "pending" and "variable_semantics_pending" in codes(row)


def test_ideam_unconfirmed_variables_are_pending_never_valid():
    for variable in ("HR_CAL_MEDIA_D", "TPR_CAL", "TV_CAL", "PTPM_CON_INTER", "TSSM_CON"):
        assert obs("10", variable=variable).status == "pending"


@pytest.mark.parametrize("kwargs,code", [
    (dict(variable="UNKNOWN_X"), "variable_unrecognized"),
    (dict(value="abc"), "value_not_numeric"),
    (dict(value="inf"), "value_not_numeric"),
    (dict(date_text="31/31/2020"), "date_invalid"),
    (dict(date_text=""), "date_invalid"),
    (dict(date_text="2030-01-01 07:00:00"), "date_in_future"),
    (dict(station="ABC"), "station_code_invalid"),
    (dict(station="999", known=frozenset({"52045020"})), "station_unknown"),
])
def test_ideam_rejections(kwargs, code):
    row = obs(**kwargs)
    assert row.status == "rejected" and code in codes(row)


def test_ideam_duplicate_dates_are_flagged_not_removed():
    rows = [obs("1.0"), obs("2.0"), obs("3.0", date_text="2016-01-04 07:00:00")]
    assert ideam.flag_duplicate_dates(rows) == 2
    assert [r.status for r in rows] == ["pending", "pending", "valid"] and len(rows) == 3


def test_ideam_temporal_coverage_reports_gaps_without_filling():
    cov = ideam.temporal_coverage([date(2020, 1, 1), date(2020, 1, 2), date(2020, 1, 5)], date(2020, 1, 1), date(2020, 1, 5))
    assert cov == {"expected_days": 5, "observed_days": 3, "missing_days": 2, "coverage_pct": 60.0, "first_missing_date": "2020-01-03"}


def test_ideam_reader_enforces_header_and_filename(tmp_path):
    good = tmp_path / "TSSM_MN_D@52045020.data"
    good.write_text("Fecha|Valor\n2016-01-03 07:00:00|15.0\n\n2016-01-04 07:00:00|\nmalformed\n", encoding="utf-8")
    assert ideam.parse_filename(good) == ("TSSM_MN_D", "52045020")
    lines = list(ideam.read_data_file(good))
    assert [n for n, _ in lines] == [2, 4, 5]
    assert lines[1][1]["value"] == "" and lines[2][1].get("malformed")
    bad = tmp_path / "wrong.data"
    bad.write_text("Fecha,Valor\n", encoding="utf-8")
    with pytest.raises(ImporterError):
        list(ideam.read_data_file(bad))
    with pytest.raises(ImporterError):
        ideam.parse_filename(bad)


# ---------------------------------------------------------------------- DANE

def pop(**overrides):
    raw = dict(municipality_code="52001", reference_year=2020, age_min=0, age_max=4, population_area="Total", sex_code="Total", population_count=1500, workbook_version="v1")
    raw.update(overrides)
    return dane.validate_population_row(raw, source_row_number=2, known_municipality_codes=KNOWN)


def test_dane_valid_row():
    assert pop().status == "valid"


@pytest.mark.parametrize("override,code", [
    ({"municipality_code": "05001"}, "divipola_outside_department"),
    ({"municipality_code": "abc"}, "divipola_invalid"),
    ({"municipality_code": "52999"}, "municipality_unknown"),
    ({"reference_year": 1990}, "year_out_of_range"),
    ({"reference_year": None}, "reference_year_missing"),
    ({"age_max": 9}, "age_group_unexpected"),
    ({"population_count": -5}, "population_negative"),
    ({"population_count": 12.5}, "population_not_integer"),
    ({"sex_code": None}, "sex_code_missing"),
])
def test_dane_rejections(override, code):
    row = pop(**override)
    assert row.status == "rejected" and code in codes(row)


def test_dane_missing_population_is_null_and_zero_is_valid():
    assert pop(population_count=None).status == "missing" and pop(population_count=None).record["population_count"] is None
    assert pop(population_count=0).status == "valid"
