"""Bio Mantra backend package."""
# LightGBM must load its native library before pandas: on Windows, importing pandas first makes
# LightGBM's SHAP call (predict(pred_contrib=True)) crash with an access violation.
import lightgbm  # noqa: F401
