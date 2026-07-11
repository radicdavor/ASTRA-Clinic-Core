import { ShieldAlert } from "lucide-react";

export function SyntheticEvaluationBoundary() {
  return (
    <section className="program1-evaluation-boundary" aria-label="Granica lokalne sintetičke evaluacije">
      <ShieldAlert size={22} aria-hidden="true" />
      <div>
        <strong>LOKALNA SINTETIČKA EVALUACIJA</strong>
        <p>Nije za kliničku uporabu. Ne unosite ni ne izgovarajte podatke stvarnih pacijenata.</p>
        <p>Napredak postoji samo u memoriji ovog taba. Ne sprema se i nije dokaz provedene sesije.</p>
      </div>
    </section>
  );
}
