export default function PriorityList({ priorities }) {
  if (!priorities.length) {
    return (
      <div className="empty-state">
        No ranked projects yet — seed demo data from the sidebar to populate this list.
      </div>
    );
  }

  return (
    <div className="priority-list">
      {priorities.map((p, i) => {
        const urgencyShare = p.total_requests
          ? p.high_urgency_count / p.total_requests
          : 0;
        const tagClass = urgencyShare > 0.3 ? "high" : urgencyShare > 0.1 ? "medium" : "low";
        const tagText = urgencyShare > 0.3 ? "high urgency" : urgencyShare > 0.1 ? "mixed urgency" : "low urgency";

        return (
          <div className="priority-card" key={p.district_id}>
            <div className="rank-badge">{i + 1}</div>
            <div>
              <div className="name">
                {p.district_name}, {p.state}
              </div>
              <div className="meta">
                {p.distinct_issues} distinct issues · {p.total_requests} requests ·{" "}
                budget on file ₹{p.planned_budget_cr} cr
              </div>
              <span className={`tag ${tagClass}`} style={{ marginTop: 6, display: "inline-block" }}>
                {tagText}
              </span>
            </div>
            <div>
              <div className="score">{p.priority_score.toFixed(3)}</div>
              <div className="score-label">priority score</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
