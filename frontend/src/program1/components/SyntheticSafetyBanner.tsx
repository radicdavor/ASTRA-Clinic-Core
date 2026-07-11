import { FlaskConical, ShieldAlert } from "lucide-react";

export function SyntheticSafetyBanner() {
  return (
    <section className="program1-safety" aria-label="Program 1 synthetic safety boundary">
      <div className="program1-safety-title">
        <FlaskConical size={22} aria-hidden="true" />
        <div>
          <strong>SINTETICKI PODACI</strong>
          <span>Ovaj prikaz sluzi iskljucivo za lokalnu demonstraciju i evaluaciju koncepta.</span>
        </div>
      </div>
      <ul>
        <li><ShieldAlert size={16} aria-hidden="true" /> NIJE ZA KLINICKU UPORABU</li>
        <li>NE SADRZI PODATKE STVARNIH PACIJENATA</li>
        <li>Ne koristiti za dijagnozu, terapiju ili trijazu</li>
        <li>Ne unositi podatke stvarnih pacijenata</li>
        <li>Nema spremanja, izvoza ni klinickog writebacka</li>
      </ul>
    </section>
  );
}
