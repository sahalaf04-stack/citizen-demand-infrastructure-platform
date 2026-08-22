import { useEffect, useState, useCallback } from "react";
import HotspotMap from "./components/HotspotMap.jsx";
import PriorityList from "./components/PriorityList.jsx";
import RequestForm from "./components/RequestForm.jsx";

const API = "https://citizen-demand-infrastructure-platform-1.onrender.com/api";

export default function App() {
  const [hotspots, setHotspots] = useState([]);
  const [priorities, setPriorities] = useState([]);
  const [requestCount, setRequestCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    const [h, p, r] = await Promise.all([
      fetch(`${API}/hotspots`).then((res) => res.json()),
      fetch(`${API}/priorities`).then((res) => res.json()),
      fetch(`${API}/requests`).then((res) => res.json()),
    ]);
    setHotspots(h);
    setPriorities(p);
    setRequestCount(r.length);
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSeed = async () => {
    setLoading(true);
    await fetch(`${API}/seed`, { method: "POST" });
    await refresh();
    setLoading(false);
  };

  const totalIssues = hotspots.reduce((sum, h) => sum + h.distinct_issues, 0);
  const totalHighUrgency = hotspots.reduce((sum, h) => sum + h.high_urgency_count, 0);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="eyebrow">Digital Public Good · demo</div>
        <h1>Citizen Demand &amp; Infrastructure Priority Platform</h1>

        <div className="stat-row">
          <span>Requests logged</span>
          <span className="value">{requestCount}</span>
        </div>
        <div className="stat-row">
          <span>Distinct issues (deduped)</span>
          <span className="value">{totalIssues}</span>
        </div>
        <div className="stat-row">
          <span>High-urgency requests</span>
          <span className="value">{totalHighUrgency}</span>
        </div>
        <div className="stat-row">
          <span>Districts ranked</span>
          <span className="value">{priorities.length}</span>
        </div>

        <button className="seed-btn" onClick={handleSeed} disabled={loading}>
          {loading ? "seeding…" : "seed demo data"}
        </button>
      </aside>

      <main className="main">
        <section>
          <h2>Submit a request</h2>
          <p className="subtitle">
            This is the citizen-facing intake path — in production it's also reachable via WhatsApp, SMS, and IVR, all calling the same endpoint.
          </p>
          <RequestForm onSubmitted={refresh} />
        </section>

        <section>
          <h2>Demand hotspots</h2>
          <p className="subtitle">
            Circle size = distinct issues after deduplication. Color = share of high-urgency requests.
          </p>
          <HotspotMap hotspots={hotspots} />
        </section>

        <section>
          <h2>Recommended priority projects</h2>
          <p className="subtitle">
            Ranked by a transparent weighted score: demand, infrastructure deficit, urgency, population affected.
          </p>
          <PriorityList priorities={priorities} />
        </section>
      </main>
    </div>
  );
}
