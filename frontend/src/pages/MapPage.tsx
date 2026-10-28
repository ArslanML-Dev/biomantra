// Map: forecast circle in the category colour around the campus, red markers for open hotspots.
import { useEffect, useState } from "react";
import { Circle, CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { api, type Forecast, type Hotspot } from "../api";

export default function MapPage() {
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.forecast("en").then(setForecast).catch((e: Error) => setError(e.message));
    api.hotspots().then(setHotspots).catch((e: Error) => setError(e.message));
  }, []);

  const open = hotspots.filter((h) => h.open);

  return (
    <>
      {error && <p className="error">{error}</p>}
      {!forecast && !error && <p className="muted">Loading…</p>}
      {forecast && (
        <>
          <p>
            Tomorrow: <span className="chip" style={{ background: forecast.color }}>{forecast.category}</span>{" "}
            {forecast.pm25_tomorrow.toFixed(0)} µg/m³ · {open.length} open hotspot{open.length === 1 ? "" : "s"}
          </p>
          <div className="mapbox">
            <MapContainer center={[forecast.location.lat, forecast.location.lon]} zoom={13} style={{ height: "100%" }}>
              <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <Circle center={[forecast.location.lat, forecast.location.lon]} radius={3000}
                pathOptions={{ color: forecast.color, fillColor: forecast.color, fillOpacity: 0.25 }}>
                <Popup>Forecast area: {forecast.category}, {forecast.pm25_tomorrow.toFixed(0)} µg/m³ tomorrow</Popup>
              </Circle>
              {open.map((h) => (
                <CircleMarker key={h.id} center={[h.lat, h.lon]} radius={9}
                  pathOptions={{ color: "#8B0000", fillColor: "#FF0000", fillOpacity: 0.9 }}>
                  <Popup>Dumping hotspot #{h.id}<br />reported {new Date(h.created_at).toLocaleString()}</Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>
        </>
      )}
    </>
  );
}
