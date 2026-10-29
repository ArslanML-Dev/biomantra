// Map: forecast circle in the category colour around the campus, markers for open dumping hotspots.
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
      <div className="eyebrow">Campus map</div>
      <h2>Air &amp; hotspots</h2>
      {error && <p className="error">{error}</p>}
      {!forecast && !error && <p className="muted">Loading…</p>}
      {forecast && (
        <>
          <div className="maphead" style={{ "--cat": forecast.color } as React.CSSProperties}>
            <span className="chip"><span className="dot" />{forecast.category}</span>
            <span className="muted">Tomorrow {forecast.pm25_tomorrow.toFixed(0)} µg/m³ · {open.length} open hotspot{open.length === 1 ? "" : "s"}</span>
          </div>
          <div className="mapbox">
            <MapContainer center={[forecast.location.lat, forecast.location.lon]} zoom={13} style={{ height: "100%" }}>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <Circle center={[forecast.location.lat, forecast.location.lon]} radius={3000}
                pathOptions={{ color: forecast.color, weight: 1.5, fillColor: forecast.color, fillOpacity: 0.16 }}>
                <Popup>Forecast area: {forecast.category}, {forecast.pm25_tomorrow.toFixed(0)} µg/m³ tomorrow</Popup>
              </Circle>
              {open.map((h) => (
                <CircleMarker key={h.id} center={[h.lat, h.lon]} radius={8}
                  pathOptions={{ color: "#ead7a8", weight: 2, fillColor: "#e58b85", fillOpacity: 0.95 }}>
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
