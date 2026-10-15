from __future__ import annotations

from math import floor
from statistics import mean, median

from app.models.ira_case import IraCase
from app.models.municipality import Municipality
from app.repositories.ira_case_repository import IraCaseRepository
from app.repositories.municipality_repository import MunicipalityRepository


def _percentile(values: list[int], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * percentile
    lower = floor(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


class RiskService:
    """Descriptive risk and endemic channel calculations from recorded data only."""

    def __init__(self, municipalities: MunicipalityRepository, cases: IraCaseRepository) -> None:
        self.municipalities = municipalities
        self.cases = cases

    def available_years(self) -> list[int]:
        return sorted({row.year for row in self.cases.list_filtered()}, reverse=True)

    def risk_map(self, year: int | None = None, week: int | None = None) -> dict:
        rows = self.cases.list_filtered(year=year)
        if not rows:
            return {"year": year, "week": week, "available_years": self.available_years(), "municipalities": []}
        chosen_year = year if year is not None else max(row.year for row in rows)
        current_year = [row for row in rows if row.year == chosen_year]
        if not current_year:
            return {"year": chosen_year, "week": week, "available_years": self.available_years(), "municipalities": []}
        chosen_week = week if week is not None else max(row.epidemiological_week for row in current_year)
        return {
            "year": chosen_year,
            "week": chosen_week,
            "available_years": self.available_years(),
            "municipalities": [
                self._municipality_risk(municipality, chosen_year, chosen_week)
                for municipality in self.municipalities.list_all()
            ],
        }

    def municipality_risk(self, municipality_id: int, year: int | None = None, week: int | None = None) -> dict | None:
        municipality = self.municipalities.get_by_id(municipality_id)
        if municipality is None:
            return None
        rows = self.cases.list_filtered(municipality_id=municipality_id, year=year)
        if not rows:
            return {"municipality_id": municipality.id, "municipality": municipality.name,
                    "department": municipality.department, "latitude": municipality.latitude,
                    "longitude": municipality.longitude, "year": year, "week": week,
                    "current_cases": None, "historical_average": None, "variation_percent": None,
                    "risk_level": "no_data"}
        chosen_year = year if year is not None else max(row.year for row in rows)
        year_rows = [row for row in rows if row.year == chosen_year]
        if not year_rows:
            return {"municipality_id": municipality.id, "municipality": municipality.name,
                    "department": municipality.department, "latitude": municipality.latitude,
                    "longitude": municipality.longitude, "year": chosen_year, "week": week,
                    "current_cases": None, "historical_average": None, "variation_percent": None,
                    "risk_level": "no_data"}
        chosen_week = week if week is not None else max(row.epidemiological_week for row in year_rows)
        return self._municipality_risk(municipality, chosen_year, chosen_week)

    def _municipality_risk(self, municipality: Municipality, year: int, week: int) -> dict:
        rows = self.cases.list_filtered(municipality_id=municipality.id)
        observed = next((row.cases for row in rows if row.year == year and row.epidemiological_week == week), None)
        historical = [row.cases for row in rows if row.year < year and row.epidemiological_week == week]
        baseline = mean(historical) if historical else None
        if observed is None:
            level, variation = "no_data", None
        elif baseline is None:
            level, variation = "no_data", None
        elif baseline == 0:
            level, variation = "low", None
        else:
            variation = (observed - baseline) / baseline * 100
            ratio = observed / baseline
            level = "high" if ratio >= 1.5 else "moderate" if ratio >= 1.2 else "low"
        return {"municipality_id": municipality.id, "municipality": municipality.name,
                "department": municipality.department, "latitude": municipality.latitude,
                "longitude": municipality.longitude, "year": year, "week": week,
                "current_cases": observed, "historical_average": round(baseline, 1) if baseline is not None else None,
                "variation_percent": round(variation, 1) if variation is not None else None,
                "risk_level": level}

    def endemic_channel(self, municipality_id: int, year: int | None = None) -> dict | None:
        municipality = self.municipalities.get_by_id(municipality_id)
        if municipality is None:
            return None
        rows = self.cases.list_filtered(municipality_id=municipality_id)
        if not rows:
            return {"municipality_id": municipality_id, "municipality": municipality.name,
                    "year": year, "available_years": [], "statistics": None, "weeks": []}
        years = sorted({row.year for row in rows}, reverse=True)
        selected_year = year if year is not None else years[0]
        observed = {row.epidemiological_week: row.cases for row in rows if row.year == selected_year}
        historical_years = [value for value in years if value < selected_year]
        points = []
        for week in range(1, 54):
            if week not in observed:
                continue
            values = [row.cases for row in rows if row.year in historical_years and row.epidemiological_week == week]
            points.append({"week": week, "observed_cases": observed[week],
                           "historical_median": round(median(values), 1) if values else None,
                           "lower_limit": round(_percentile(values, .25), 1) if values else None,
                           "upper_limit": round(_percentile(values, .75), 1) if values else None,
                           "upper_alert_limit": round(_percentile(values, .90), 1) if values else None})
        counts = list(observed.values())
        current = next((item for item in points if item["week"] == max(observed)), None)
        risk = self._municipality_risk(municipality, selected_year, max(observed))["risk_level"] if observed else "no_data"
        return {"municipality_id": municipality.id, "municipality": municipality.name, "year": selected_year,
                "available_years": years, "statistics": {"total_cases": sum(counts), "average": round(mean(counts), 1),
                "median": round(median(counts), 1), "minimum": min(counts), "maximum": max(counts),
                "risk_level": risk, "latest_week": current["week"] if current else None}, "weeks": points}
