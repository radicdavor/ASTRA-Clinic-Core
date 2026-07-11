import { SyntheticScenario } from "../types/syntheticReview";
import { SyntheticEmptyState } from "./SyntheticEmptyState";

export function SyntheticTimeline({ scenario, categoryFilter }: { scenario: SyntheticScenario; categoryFilter: string }) {
  const events = categoryFilter ? scenario.timeline.filter((event) => event.category === categoryFilter) : scenario.timeline;
  if (events.length === 0) {
    return <SyntheticEmptyState title="Nema sinteticnih dogadaja" message="Promijenite kategoriju vremenske crte." />;
  }
  return (
    <div className="timeline" role="list" aria-label="Sinteticna vremenska crta">
      {events.map((event) => (
        <article key={event.id} role="listitem">
          <span>{event.relativeTime} / {event.category}</span>
          <strong>{event.title}</strong>
          <p>{event.description}</p>
          <small>Dokazi: {event.evidenceIds.join(", ")}</small>
        </article>
      ))}
    </div>
  );
}
