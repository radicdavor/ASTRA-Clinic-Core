import { SyntheticEvaluationPreflightItem, SyntheticEvaluationTask } from "../types/syntheticEvaluation";

export const syntheticEvaluationPreflight: SyntheticEvaluationPreflightItem[] = [
  { id: "synthetic-only", label: "Potvrđeni su isključivo repository-controlled sintetički scenariji." },
  { id: "local-only", label: "Evaluacija se izvodi lokalno, bez stvarnih podataka i kliničkog rada." },
  { id: "consent", label: "Pročitan je consent script i sudionik je dobrovoljno pristao." },
  { id: "no-real-cases", label: "Sudionik razumije da ne smije opisivati stvarne pacijente ili slučajeve." },
  { id: "not-performance", label: "Evaluira se sučelje, a ne znanje ili rad sudionika." },
  { id: "stop-authority", label: "Moderator zna stop uvjete i ima ovlast odmah zaustaviti prolaz." }
];

export const syntheticEvaluationTasks: SyntheticEvaluationTask[] = [
  {
    id: "safety",
    order: 1,
    title: "Sigurnosna granica",
    prompt: "Bez klikanja objasnite čemu prikaz služi i čemu ne služi.",
    successSignals: ["prepoznaje synthetic/demo-only kontekst", "navodi da nije za kliničku uporabu", "ne opisuje dijagnozu, terapiju ili trijažu"]
  },
  {
    id: "scenario",
    order: 2,
    title: "Identitet scenarija",
    prompt: "Odaberite SYN-GAMMA i objasnite kako znate da je odabran.",
    scenarioId: "SYN-GAMMA",
    successSignals: ["odabire SYN-GAMMA", "prepoznaje odabrano stanje", "sintetički subjekt ne tumači kao pacijenta"]
  },
  {
    id: "evidence",
    order: 3,
    title: "Pregled dokaza",
    prompt: "Pronađite sintetičke dokaze i razlikujte dostupno, nedostajuće i nejasno.",
    successSignals: ["otvara tab dokaza", "razumije statusni filtar", "razumije prazni filtrirani rezultat"]
  },
  {
    id: "findings",
    order: 4,
    title: "Granica nalaza",
    prompt: "Pronađite nalaze i objasnite što ovaj prikaz ne dopušta učiniti.",
    successSignals: ["otvara tab nalaza", "prepoznaje deskriptivni status", "ne vidi dijagnozu, terapiju, zadatak ili writeback"]
  },
  {
    id: "completeness",
    order: 5,
    title: "Potpunost nije klinička spremnost",
    prompt: "Objasnite razliku između potpunosti scenarija i spremnosti pacijenta.",
    successSignals: ["otvara prikaz potpunosti", "navodi da je riječ samo o scenariju", "odbacuje tumačenje kliničkog odobrenja"]
  },
  {
    id: "limitations",
    order: 6,
    title: "Ograničenja",
    prompt: "Pronađite najvažnije ograničenje i jedno zabranjeno tumačenje.",
    successSignals: ["otvara ograničenja", "može ponoviti ograničenje", "može ponoviti zabranjeno tumačenje"]
  },
  {
    id: "comparison",
    order: 7,
    title: "Deskriptivna usporedba",
    prompt: "Usporedite SYN-ALPHA i SYN-BETA bez rangiranja ili preporuke.",
    scenarioId: "SYN-ALPHA",
    successSignals: ["koristi traženi par", "opisuje samo razlike", "ne zaključuje prioritet, hitnost ili preporuku"]
  },
  {
    id: "keyboard",
    order: 8,
    title: "Keyboard-only prolaz",
    prompt: "Bez miša prijeđite od Sažetka do Ograničenja i vratite se na Sažetak.",
    successSignals: ["koristi Tab i Arrow/Home/End", "vidljivi fokus ostaje prepoznatljiv", "odabrani tab i panel ostaju usklađeni"]
  }
];
