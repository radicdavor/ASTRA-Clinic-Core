import { SyntheticScenario } from "../types/syntheticReview";

export function SyntheticTimeline({ scenario, categoryFilter }: { scenario: SyntheticScenario; categoryFilter: string }) {
  const events = categoryFilter ? scenario.timeline.filter((event) => event.category === categoryFilter) : scenario.timeline;
  return (
    <div className="timeline">
      {events.map((event) => (
        <article key={event.id}>
          <span>{event.relativeTime} / {event.category}</span>
          <strong>{event.title}</strong>
          <p>{event.description}</p>
          <small>Dokazi: {event.evidenceIds.join(", ")}</small>
        </article>
      ))}
    </div>
  );
}
