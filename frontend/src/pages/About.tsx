// About: real model metrics from /meta vs the baselines, data sources, limitations and disclaimers.
import { useEffect, useState } from "react";
import { api, type Metrics } from "../api";

const MODELS = [["persistence", "Persistence"], ["linear", "Linear"], ["lightgbm", "LightGBM ✓"]] as const;

export default function About() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.meta().then((m) => setMetrics(m.model_metrics)).catch((e: Error) => setError(e.message));
  }, []);

  return (
    <>
      <div className="card">
        <h2>About Bio Mantra</h2>
        <p>Bio Mantra forecasts tomorrow's PM2.5 for the campus area, explains it in plain English/Hindi, and rewards
          eco-actions only when a live photo passes an anti-fraud check and an AI check. Uncertain cases go to a human reviewer.</p>
      </div>

      <div className="card">
        <h3>Forecast model results (test set)</h3>
        {error && <p className="error">{error}</p>}
        {metrics && (
          <>
            <p className="muted">Target: PM2.5 24 h ahead · {metrics.rows.toLocaleString()} hourly rows · test period {metrics.test_period[0]} → {metrics.test_period[1]} · data source: {metrics.data_source}</p>
            <div className="tablewrap">
              <table className="nowrap">
                <thead><tr><th>Model</th><th>MAE</th><th>RMSE</th><th>R²</th><th>Acc.</th><th>F1</th><th>Poor+</th></tr></thead>
                <tbody>
                  {MODELS.map(([key, label]) => {
                    const m = metrics[key];
                    return <tr key={key}><td>{label}</td><td>{m.mae}</td><td>{m.rmse}</td><td>{m.r2}</td><td>{m.acc_cat}</td><td>{m.macro_f1}</td><td>{m.recall_poor_plus}</td></tr>;
                  })}
                </tbody>
              </table>
            </div>
            <p className="muted">Persistence = "tomorrow will be like now". ✓ = model used in the app. Acc. = CPCB category accuracy, F1 = macro-F1, Poor+ = recall for Poor or worse days. MAE/RMSE in µg/m³; swipe the table sideways on a phone. LightGBM beats persistence but is only about as good as linear regression on this data.</p>
          </>
        )}
      </div>

      <div className="card">
        <h3>Data sources</h3>
        <ul>
          <li>PM2.5: Open-Meteo Air Quality API (CAMS model data), hourly, from Aug 2022. OpenWeather was planned but no API key was used.</li>
          <li>Weather: Open-Meteo historical archive and forecast APIs (temperature, humidity, wind, rain).</li>
          <li>Photo AI: Ultralytics YOLOv8n pretrained on the COCO dataset.</li>
          <li>Map tiles: © OpenStreetMap contributors.</li>
        </ul>
      </div>

      <div className="card">
        <h3>Limitations (please read)</h3>
        <ul>
          <li><strong>Modelled data:</strong> PM2.5 values are modelled/reanalysis estimates for a grid cell, not readings from a ground monitoring station.</li>
          <li><strong>COCO stand-in classes:</strong> COCO has no "sapling" or "dustbin" class. We use "potted plant" for saplings and
            bottles/cups/bowls/cutlery as "litter" for bins, clean-ups and dumping reports. The AI can be fooled and often is unsure — that is why a human reviewer checks uncertain cases.</li>
          <li><strong>Prototype scope:</strong> a 3-day student prototype with demo users and no passwords. Not for real-world enforcement.</li>
          <li>Anti-fraud checks (server time, geofence, near-duplicate photo hash) raise the bar but cannot stop every trick, e.g. photographing a screen.</li>
        </ul>
      </div>

      <div className="card">
        <h3>Health note</h3>
        <p>This is general awareness, not medical advice.</p>
        <p>यह सामान्य जानकारी है, चिकित्सा सलाह नहीं।</p>
      </div>
    </>
  );
}
