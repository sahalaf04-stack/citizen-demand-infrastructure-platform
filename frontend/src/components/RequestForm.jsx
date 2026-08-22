import { useEffect, useState } from "react";

const API = "https://citizen-demand-infrastructure-platform-1.onrender.com/api";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "Hindi" },
  { code: "kn", label: "Kannada" },
];

export default function RequestForm({ onSubmitted }) {
  const [districts, setDistricts] = useState([]);
  const [districtId, setDistrictId] = useState("");
  const [language, setLanguage] = useState("en");
  const [text, setText] = useState("");
  const [status, setStatus] = useState(null); // null | "sending" | {category, urgency} | "error"

  useEffect(() => {
    fetch(`${API}/districts`)
      .then((res) => res.json())
      .then((data) => {
        setDistricts(data);
        if (data.length) setDistrictId(String(data[0].id));
      });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim() || !districtId) return;

    const district = districts.find((d) => String(d.id) === districtId);
    setStatus("sending");

    try {
      const res = await fetch(`${API}/requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: text.trim(),
          language,
          district_id: Number(districtId),
          // small jitter so multiple submissions in the same district don't
          // stack exactly on top of each other on the map
          lat: district.lat + (Math.random() - 0.5) * 0.08,
          lon: district.lon + (Math.random() - 0.5) * 0.08,
        }),
      });
      if (!res.ok) throw new Error("request failed");
      const data = await res.json();
      setStatus({ category: data.category, urgency: data.urgency });
      setText("");
      onSubmitted?.();
    } catch {
      setStatus("error");
    }
  };

  return (
    <form className="request-form" onSubmit={handleSubmit}>
      <div className="form-row">
        <label>
          District
          <select value={districtId} onChange={(e) => setDistrictId(e.target.value)}>
            {districts.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}, {d.state}
              </option>
            ))}
          </select>
        </label>

        <label>
          Language
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label>
        Describe the issue
        <textarea
          rows={3}
          placeholder="e.g. No water supply for the last two weeks in our locality."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </label>

      <button type="submit" className="submit-btn" disabled={status === "sending"}>
        {status === "sending" ? "submitting…" : "submit request"}
      </button>

      {status && status !== "sending" && status !== "error" && (
        <div className="form-feedback success">
          Logged as <strong>{status.category}</strong> · <strong>{status.urgency}</strong> urgency
        </div>
      )}
      {status === "error" && (
        <div className="form-feedback error">
          Something went wrong — check that the backend is running.
        </div>
      )}
    </form>
  );
}
