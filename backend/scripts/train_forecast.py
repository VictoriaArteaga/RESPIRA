"""Entrena y evalúa los modelos de predicción de IRA de RESPIRA.

Uso (desde la carpeta backend, con el entorno virtual activado):
    python scripts/train_forecast.py

Lee data/respira_v2/dataset_entrenamiento.csv y escribe en backend/ml_artifacts/:
modelos (*.joblib), metrics.json y metrics_by_municipality.csv. No se conecta a la base de datos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ml.training import train_all  # noqa: E402

if __name__ == "__main__":
    result = train_all()
    print("\nAporte de las variables climáticas (MAE con clima vs. base, mismos municipios):")
    for row in result["aporte_variables_climaticas"]:
        print(f"  {row['modelo']} h{row['horizonte']} {row['periodo']:20s} n={row['n']:5d} "
              f"clima={row['mae_con_clima']:.3f} base={row['mae_base']:.3f} mejora={row['mejora_mae_pct']:+.1f}%")
