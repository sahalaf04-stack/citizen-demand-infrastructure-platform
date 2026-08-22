import { useEffect, useRef } from "react";
import L from "leaflet";

/**
 * Plain-Leaflet (not react-leaflet) so this has zero extra dependency
 * surface - just the one leaflet package already in package.json.
 * Circle radius = distinct issue count, color = high-urgency share.
 */
export default function HotspotMap({ hotspots }) {
  const mapRef = useRef(null);
  const containerRef = useRef(null);
  const layerRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current) {
      mapRef.current = L.map(containerRef.current).setView([22.5, 79.0], 5);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(mapRef.current);
      layerRef.current = L.layerGroup().addTo(mapRef.current);
    }
  }, []);

  useEffect(() => {
    if (!layerRef.current) return;
    layerRef.current.clearLayers();

    hotspots.forEach((h) => {
      const urgencyShare = h.total_requests
        ? h.high_urgency_count / h.total_requests
        : 0;
      const color =
        urgencyShare > 0.3 ? "#a13d3d" : urgencyShare > 0.1 ? "#b5651d" : "#4a7a5c";

      L.circleMarker([h.lat, h.lon], {
        radius: 8 + h.distinct_issues * 1.5,
        color,
        fillColor: color,
        fillOpacity: 0.35,
        weight: 1.5,
      })
        .bindPopup(
          `<strong>${h.district_name}</strong><br/>${h.distinct_issues} distinct issues<br/>${h.total_requests} total requests<br/>${h.high_urgency_count} high urgency`
        )
        .addTo(layerRef.current);
    });
  }, [hotspots]);

  return <div id="map" ref={containerRef} />;
}
