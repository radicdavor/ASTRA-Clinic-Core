import { SyntheticScenario } from "../types/syntheticReview";
import { validateSyntheticScenarios } from "../utils/syntheticReviewValidation";

const provenance = {
  source: "repository-controlled-synthetic-fixture",
  derivedFromExistingSandbox: true,
  sourceReference: "sandbox/program1",
  realDataUsed: false
} as const;

const commonLimitations = [
  "Sadrzaj je repo-kontrolirana sinteticna demonstracija.",
  "Ne sadrzi stvarne pacijente, PHI ili PII.",
  "Ne sprema stanje, ne izvozi podatke i ne salje poruke.",
  "Ne povezuje se s backend Program 1 podacima, bazom ili EHR/EMR sustavom."
];

const commonProhibited = [
  "Ne koristiti za dijagnozu, terapiju ili trijazu.",
  "Ne tumaciti kao klinicku preporuku ili prioritet.",
  "Ne koristiti za poruke pacijentu, promjenu termina ili klinicki writeback.",
  "Ne koristiti kao dokaz produkcijske, klinicke ili go-live spremnosti."
];

export const syntheticScenarios: SyntheticScenario[] = validateSyntheticScenarios([
  {
    id: "SYN-ALPHA",
    syntheticOnly: true,
    version: "ui-fixture-1",
    title: "Alpha: osnovni pregled s dva sinteticna nalaza",
    purpose: "Prikazuje osnovni tok pregleda s vise povezanih sinteticnih stavki.",
    subjectLabel: "Sinteticni subjekt Alpha",
    summary: "Alpha sluzi za pregled odnosa izmedu kratkog scenarija, dokaza, nalaza i biljeske za lokalnu evaluaciju.",
    reviewQuestion: "Moze li korisnik razumjeti koje sinteticne informacije su dostupne i koje su ogranicene?",
    timeline: [
      {
        id: "alpha-timeline-1",
        relativeTime: "Dan 0",
        category: "Scenarij",
        title: "Sinteticni pregled pokrenut",
        description: "Lokalni demo prikazuje pocetni kontekst bez stvarnih datuma ili identiteta.",
        evidenceIds: ["alpha-evidence-context"]
      },
      {
        id: "alpha-timeline-2",
        relativeTime: "Pregled 1",
        category: "Dokumentacija",
        title: "Druga sinteticna stavka dostupna",
        description: "Dodatna stavka postoji samo kao primjer povezivanja dokaza i nalaza.",
        evidenceIds: ["alpha-evidence-followup"]
      }
    ],
    evidence: [
      {
        id: "alpha-evidence-context",
        type: "Sinteticni zapis",
        title: "Kontekst pregleda",
        summary: "Kratak opis okolnosti scenarija bez stvarnih klinickih tvrdnji.",
        status: "available",
        sourceLabel: "Repository synthetic fixture"
      },
      {
        id: "alpha-evidence-followup",
        type: "Sinteticna biljeska",
        title: "Dodatni primjer",
        summary: "Primjer stavke koja pomaze provjeriti citljivost i povezivanje.",
        status: "available",
        sourceLabel: "Repository synthetic fixture"
      }
    ],
    findings: [
      {
        id: "alpha-finding-context",
        title: "Kontekst za ljudski pregled",
        description: "Nalaz opisuje samo sto korisnik treba procitati u demo prikazu.",
        state: "open",
        evidenceIds: ["alpha-evidence-context"],
        limitation: "Otvorenost znaci samo da je stavka vidljiva za pregled u scenariju."
      },
      {
        id: "alpha-finding-followup",
        title: "Dodatna stavka za usporedbu",
        description: "Stavka postoji radi prikaza vise povezanih dokaza.",
        state: "resolved-in-scenario",
        evidenceIds: ["alpha-evidence-followup"],
        limitation: "Rijeseno u scenariju ne znaci klinicko rjesenje."
      }
    ],
    readiness: [
      {
        id: "alpha-complete-summary",
        label: "Sažetak scenarija",
        state: "documented",
        rationale: "Pregledno su navedeni naslov, svrha i pitanje pregleda."
      },
      {
        id: "alpha-complete-evidence",
        label: "Sinteticni dokazi",
        state: "documented",
        rationale: "Obje stavke dokaza su dostupne u fixtureu."
      }
    ],
    limitations: commonLimitations,
    prohibitedInterpretations: commonProhibited,
    provenance
  },
  {
    id: "SYN-BETA",
    syntheticOnly: true,
    version: "ui-fixture-1",
    title: "Beta: vidljivost sigurnosne granice",
    purpose: "Naglasava da sinteticni prikaz ne aktivira klinicke ili operativne radnje.",
    subjectLabel: "Sinteticni subjekt Beta",
    summary: "Beta prikazuje kraci scenarij s jednim dokazom i jasnim ogranicenjima.",
    reviewQuestion: "Jesu li zabrane i sigurnosne granice dovoljno vidljive bez dodatnih radnji?",
    timeline: [
      {
        id: "beta-timeline-1",
        relativeTime: "Dan 0",
        category: "Granica",
        title: "Sigurnosna granica prikazana",
        description: "Korisnik vidi da nema stvarnih podataka, spremanja ili klinicke uporabe.",
        evidenceIds: ["beta-evidence-boundary"]
      }
    ],
    evidence: [
      {
        id: "beta-evidence-boundary",
        type: "Sinteticna sigurnosna biljeska",
        title: "Granica vidljiva u prikazu",
        summary: "Biljeska objasnjava da je modul lokalni read-only demo.",
        status: "available",
        sourceLabel: "Repository synthetic fixture"
      }
    ],
    findings: [
      {
        id: "beta-finding-boundary",
        title: "Granica ostaje vidljiva",
        description: "Nalaz opisuje vidljivost upozorenja, ne stanje pacijenta.",
        state: "uncertain",
        evidenceIds: ["beta-evidence-boundary"],
        limitation: "Neizvjesno oznacava samo da evaluator moze dodatno procijeniti tekst."
      }
    ],
    readiness: [
      {
        id: "beta-complete-warning",
        label: "Sigurnosna kopija",
        state: "documented",
        rationale: "Scenarij ima jasnu sinteticnu i neklinicku oznaku."
      },
      {
        id: "beta-complete-depth",
        label: "Dubina scenarija",
        state: "incomplete",
        rationale: "Namjerno je kratak i ne pokriva slozene tokove."
      }
    ],
    limitations: commonLimitations,
    prohibitedInterpretations: commonProhibited,
    provenance
  },
  {
    id: "SYN-GAMMA",
    syntheticOnly: true,
    version: "ui-fixture-1",
    title: "Gamma: nepotpuna sinteticna dokumentacija",
    purpose: "Prikazuje kako izgleda scenario s nedostajucim sinteticnim kontekstom.",
    subjectLabel: "Sinteticni subjekt Gamma",
    summary: "Gamma pokazuje da nedostajuci dokaz nije klinicki zakljucak.",
    reviewQuestion: "Je li korisniku jasno da nedostajuci sinteticni dokaz ne znaci odsutnost klinickog problema?",
    timeline: [
      {
        id: "gamma-timeline-1",
        relativeTime: "Dan 0",
        category: "Dokumentacija",
        title: "Osnovni kontekst dostupan",
        description: "Prvi sinteticni dokument postoji, ali drugi je namjerno oznacen kao nedostajuci.",
        evidenceIds: ["gamma-evidence-context", "gamma-evidence-missing"]
      }
    ],
    evidence: [
      {
        id: "gamma-evidence-context",
        type: "Sinteticni zapis",
        title: "Dostupan kontekst",
        summary: "Osnovni demo kontekst za citanje scenarija.",
        status: "available",
        sourceLabel: "Repository synthetic fixture"
      },
      {
        id: "gamma-evidence-missing",
        type: "Sinteticna referenca",
        title: "Nedostajuca referenca",
        summary: "Namjerno oznaceno kao nedostajuce za prikaz ogranicenja.",
        status: "missing",
        sourceLabel: "Repository synthetic fixture"
      }
    ],
    findings: [
      {
        id: "gamma-finding-missing",
        title: "Nedostajuci kontekst",
        description: "Opisuje da dio sinteticne dokumentacije nije prikazan.",
        state: "open",
        evidenceIds: ["gamma-evidence-missing"],
        limitation: "Nedostajanje dokaza nije klinicka tvrdnja."
      }
    ],
    readiness: [
      {
        id: "gamma-complete-evidence",
        label: "Dokazni kontekst",
        state: "incomplete",
        rationale: "Jedna sinteticna referenca je oznacena kao nedostajuca."
      }
    ],
    limitations: commonLimitations,
    prohibitedInterpretations: commonProhibited,
    provenance
  },
  {
    id: "SYN-DELTA",
    syntheticOnly: true,
    version: "ui-fixture-1",
    title: "Delta: neusklađene sinteticne informacije",
    purpose: "Prikazuje scenarij s ambivalentnim sinteticnim informacijama bez zakljucka.",
    subjectLabel: "Sinteticni subjekt Delta",
    summary: "Delta pomaze evaluirati kako su prikazane nejasne ili razlicite sinteticne stavke.",
    reviewQuestion: "Moze li korisnik vidjeti razliku izmedu deskriptivnog prikaza i klinickog zakljucka?",
    timeline: [
      {
        id: "delta-timeline-1",
        relativeTime: "Pregled 1",
        category: "Usporedba",
        title: "Dva sinteticna izvora nisu uskladena",
        description: "Prikaz ostaje deskriptivan i ne bira tocnu verziju.",
        evidenceIds: ["delta-evidence-a", "delta-evidence-b"]
      }
    ],
    evidence: [
      {
        id: "delta-evidence-a",
        type: "Sinteticni izvor A",
        title: "Prva sinteticna biljeska",
        summary: "Jedna verzija konteksta za lokalnu evaluaciju.",
        status: "ambiguous",
        sourceLabel: "Repository synthetic fixture"
      },
      {
        id: "delta-evidence-b",
        type: "Sinteticni izvor B",
        title: "Druga sinteticna biljeska",
        summary: "Druga verzija konteksta bez odabira pobjednika.",
        status: "ambiguous",
        sourceLabel: "Repository synthetic fixture"
      }
    ],
    findings: [
      {
        id: "delta-finding-ambiguous",
        title: "Neusklađenost za citanje",
        description: "Nalaz opisuje samo da se informacije razlikuju u sinteticnom scenariju.",
        state: "uncertain",
        evidenceIds: ["delta-evidence-a", "delta-evidence-b"],
        limitation: "Ne daje klinicki prioritet ili smjer postupanja."
      }
    ],
    readiness: [
      {
        id: "delta-complete-context",
        label: "Usklađenost scenarija",
        state: "blocked",
        rationale: "Sinteticni scenario namjerno ne daje zakljucak."
      }
    ],
    limitations: commonLimitations,
    prohibitedInterpretations: commonProhibited,
    provenance
  },
  {
    id: "SYN-EPSILON",
    syntheticOnly: true,
    version: "ui-fixture-1",
    title: "Epsilon: provjera zabranjenih radnji",
    purpose: "Prikazuje da pacijent-facing i workflow radnje ostaju iskljucene.",
    subjectLabel: "Sinteticni subjekt Epsilon",
    summary: "Epsilon je scenarij za citanje sigurnosnih ogranicenja bez aktivnih radnji.",
    reviewQuestion: "Jesu li korisniku jasne granice bez gumba za operativne ili klinicke radnje?",
    timeline: [
      {
        id: "epsilon-timeline-1",
        relativeTime: "Lokalni demo",
        category: "Zabrana",
        title: "Operativne radnje nisu dostupne",
        description: "Nema spremanja, slanja, promjene termina ili writebacka.",
        evidenceIds: ["epsilon-evidence-disabled"]
      }
    ],
    evidence: [
      {
        id: "epsilon-evidence-disabled",
        type: "Sinteticna granica",
        title: "Radnje iskljucene",
        summary: "Dokaz prikazuje samo opis zabrana, bez kontrola za izvrsenje.",
        status: "available",
        sourceLabel: "Repository synthetic fixture"
      }
    ],
    findings: [
      {
        id: "epsilon-finding-disabled",
        title: "Zabranjene radnje nisu kontrole",
        description: "Tekst objasnjava sto nije dostupno u modulu.",
        state: "resolved-in-scenario",
        evidenceIds: ["epsilon-evidence-disabled"],
        limitation: "Ovo nije implementacija odobrenja, zaobilazenja ili klinickog toka."
      }
    ],
    readiness: [
      {
        id: "epsilon-complete-actions",
        label: "Akcijske kontrole",
        state: "not-applicable",
        rationale: "Akcijske kontrole nisu dio synthetic read-only modula."
      }
    ],
    limitations: commonLimitations,
    prohibitedInterpretations: commonProhibited,
    provenance
  }
]);

export const defaultSyntheticScenarioId = syntheticScenarios[0].id;
