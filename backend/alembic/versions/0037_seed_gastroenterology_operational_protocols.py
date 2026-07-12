"""seed gastroenterology operational protocols

Revision ID: 0037_seed_gastroenterology_operational_protocols
Revises: 0036_seed_gastroscopy_preparation_protocol
"""

from alembic import op
import sqlalchemy as sa


revision = "0037_seed_gastroenterology_operational_protocols"
down_revision = "0036_seed_gastroscopy_preparation_protocol"
branch_labels = None
depends_on = None


EVIDENCE = "Operativni draft prema navedenom izvoru – stručni pregled obavezan"


PROTOCOLS = [
    {
        "key": "colonoscopy-preparation-v1",
        "title": "Priprema za kolonoskopiju",
        "source_title": "ESGE guideline: Bowel preparation for colonoscopy – Update 2019",
        "source_url": "https://www.esge.com/bowel-preparation-for-colonoscopy-esge-guideline-update-2019",
        "rules": [
            ("Potvrda pacijenta i termina", "Prije davanja ili provjere uputa.", "Potvrditi identitet, datum, vrijeme i vrstu zakazanog postupka."),
            ("Upute za prehranu i pripravak", "Kada se pacijentu predaje plan pripreme.", "Evidentirati da su dane aktualne lokalno odobrene upute. Ne birati pripravak bez odobrenog plana."),
            ("Vrijeme uzimanja pripravka", "Prije postupka.", "Provjeriti je li pacijent slijedio propisani raspored doza i zabilježiti odstupanja."),
            ("Terapija, alergije i rizična stanja", "Pri provjeri pripreme.", "Evidentirati terapiju, alergije i stanja važna za izbor pripreme; ne mijenjati terapiju bez liječnika."),
            ("Procjena odgovora na pripremu", "Na dan postupka.", "Zabilježiti pacijentov opis provedene pripreme i moguće poteškoće bez automatske procjene dostatnosti."),
            ("Eskalacija odstupanja", "Ako priprema nije provedena prema planu ili postoje nejasnoće.", "Proslijediti odgovornom liječniku prije nastavka; sustav ne odobrava automatski postupak."),
        ],
    },
    {
        "key": "endoscopy-biopsy-specimen-handling-v1",
        "title": "Postupanje s biopsijskim uzorkom",
        "source_title": "ESGE guideline: Endoscopic tissue sampling – Part 1",
        "source_url": "https://www.esge.com/endoscopic-tissue-sampling-part1-esge-guideline",
        "rules": [
            ("Identifikacija uzorka", "Odmah nakon uzimanja biopsije.", "Povezati uzorak s potvrđenim pacijentom, postupkom i mjestom uzimanja."),
            ("Odvojeni spremnici", "Kada uzorci potječu iz različitih anatomskih mjesta.", "Koristiti odvojene, jasno označene spremnike prema lokalnom protokolu i zahtjevu liječnika."),
            ("Oznaka i sadržaj uputnice", "Prije slanja uzorka.", "Provjeriti oznaku spremnika, anatomsko mjesto, broj uzoraka i potrebne kliničke podatke na uputnici."),
            ("Medij i čuvanje", "Prije transporta.", "Primijeniti lokalno odobren medij i uvjete čuvanja; odstupanja odmah prijaviti."),
            ("Primopredaja i sljedivost", "Pri predaji laboratoriju ili transportu.", "Evidentirati vrijeme, osobu koja predaje i osobu/službu koja preuzima uzorak."),
            ("Nesukladan uzorak", "Ako oznaka, spremnik, uputnica ili uzorak nisu usklađeni.", "Zaustaviti slanje i uključiti liječnika ili odgovornu osobu; ne ispravljati identitet pretpostavkom."),
        ],
    },
    {
        "key": "endoscope-reprocessing-traceability-v1",
        "title": "Čišćenje i evidencija endoskopa",
        "source_title": "ESGE–ESGENA position statement: Reprocessing of flexible endoscopes – Update 2018",
        "source_url": "https://www.esge.com/reprocessing-of-flexible-endoscopes-and-endoscopic-accessories-used-in-gastrointestinal-endoscopy-esge-esgena-position-statement-update-2018",
        "rules": [
            ("Identifikacija uređaja", "Nakon svakog postupka.", "Evidentirati jedinstvenu oznaku endoskopa i postupak nakon kojeg ulazi u obradu."),
            ("Predčišćenje", "Neposredno nakon uporabe.", "Provesti predčišćenje prema uputi proizvođača i lokalno odobrenom postupku."),
            ("Test nepropusnosti i ručno čišćenje", "Prije dezinfekcije.", "Provesti propisane provjere i ručno čišćenje svih dostupnih kanala prema uputi proizvođača."),
            ("Dezinfekcija i ispiranje", "Nakon uspješnog čišćenja.", "Koristiti validirani postupak i evidentirati ciklus, uređaj i rezultat bez preskakanja upozorenja."),
            ("Sušenje i čuvanje", "Nakon dovršenog ciklusa.", "Potvrditi sušenje i čuvanje u uvjetima definiranima lokalnim pravilima i uputom proizvođača."),
            ("Sljedivost i nesukladnost", "Za svaki ciklus ili kvar.", "Evidentirati izvršitelja i vrijeme. Uređaj s neuspjelim ciklusom ili sumnjom na kontaminaciju povući iz uporabe."),
        ],
    },
    {
        "key": "post-sedation-patient-monitoring-v1",
        "title": "Kontrola pacijenta nakon sedacije",
        "source_title": "British Society of Gastroenterology guideline on sedation in gastrointestinal endoscopy",
        "source_url": "https://pubmed.ncbi.nlm.nih.gov/37816587/",
        "rules": [
            ("Primopredaja u oporavak", "Po završetku sediranog postupka.", "Predati pacijenta odgovornoj osobi uz podatke o postupku, sedaciji i uočenim događajima."),
            ("Nadzor tijekom oporavka", "Dok traje oporavak od sedacije.", "Pratiti parametre i stanje svijesti prema lokalnom protokolu te evidentirati opažanja."),
            ("Procjena simptoma i komplikacija", "Tijekom oporavka ili pri novim tegobama.", "Svako odstupanje ili novu tegobu odmah proslijediti odgovornom liječniku."),
            ("Kriteriji za otpust", "Prije razmatranja otpusta.", "Provjeriti lokalno odobrene kriterije. Ova lista sama ne odobrava otpust."),
            ("Upute i pratnja", "Prije odlaska pacijenta.", "Potvrditi da su dane usmene i pisane upute te provjeriti zahtjev za odgovornom pratnjom."),
            ("Odobrenje i dokumentiranje", "Na kraju oporavka.", "Evidentirati ovlaštenu osobu koja je odobrila otpust, vrijeme i sve predane upute."),
        ],
    },
    {
        "key": "inadequate-bowel-preparation-v1",
        "title": "Postupanje kod nedovoljne pripreme crijeva",
        "source_title": "ESGE guideline: Bowel preparation for colonoscopy – Update 2019",
        "source_url": "https://www.esge.com/bowel-preparation-for-colonoscopy-esge-guideline-update-2019",
        "rules": [
            ("Evidencija kvalitete pripreme", "Kada liječnik procijeni da priprema nije dostatna.", "Zabilježiti liječničku procjenu i korištenu standardiziranu ocjenu ako je primjenjiva."),
            ("Opseg dovršenog postupka", "Nakon nepotpunog ili ograničenog pregleda.", "Evidentirati dosegnuti segment, ograničenja pregleda i relevantnu dokumentaciju."),
            ("Razlog nedostatne pripreme", "Pri razgovoru s pacijentom i pregledu dokumentacije.", "Zabilježiti poznate razloge i odstupanja bez pripisivanja krivnje ili automatskog zaključka."),
            ("Odluka o ponavljanju", "Kada je potrebno razmotriti novi postupak.", "Termin i način ponavljanja određuje liječnik; sustav ne zakazuje automatski."),
            ("Revidirane upute", "Ako liječnik odredi ponavljanje.", "Predati individualizirane, liječnički odobrene upute i provjeriti razumijevanje pacijenta."),
            ("Zatvaranje zapisa", "Nakon dokumentirane odluke.", "Povezati odluku, upute i eventualni novi termin s izvornim postupkom radi sljedivosti."),
        ],
    },
    {
        "key": "histopathology-result-entry-review-v1",
        "title": "Unos i pregled patohistološkog nalaza",
        "source_title": "ESGE guideline: Endoscopic tissue sampling – Part 1",
        "source_url": "https://www.esge.com/endoscopic-tissue-sampling-part1-esge-guideline",
        "rules": [
            ("Povezivanje nalaza i uzorka", "Pri zaprimanju patohistološkog nalaza.", "Potvrditi pacijenta, postupak, datum i oznaku uzorka prije unosa nalaza."),
            ("Vjeran prijepis ili prilog", "Pri unosu sadržaja nalaza.", "Sačuvati izvorni dokument ili vjeran prijepis bez mijenjanja značenja i uz naveden izvor."),
            ("Status pregleda", "Nakon unosa nalaza.", "Označiti nalaz kao zaprimljen i nepregledan dok ga ovlašteni liječnik ne pregleda."),
            ("Liječnička interpretacija", "Kada liječnik otvori nalaz.", "Interpretaciju, zaključak i plan unosi liječnik; sustav ne izvodi dijagnozu iz teksta nalaza."),
            ("Nesklad identiteta ili sadržaja", "Ako podaci nalaza ne odgovaraju zapisu ili su nepotpuni.", "Zaustaviti potvrdu i zatražiti provjeru od laboratorija ili odgovorne osobe."),
            ("Sljedivost pregleda", "Po završetku liječničkog pregleda.", "Evidentirati liječnika, vrijeme pregleda, zaključak i povezane daljnje radnje."),
        ],
    },
    {
        "key": "endoscopy-antithrombotic-risk-v1",
        "title": "Postupak kod terapije koja povećava rizik krvarenja",
        "source_title": "BSG/ESGE guideline update: Endoscopy in patients on antiplatelet or anticoagulant therapy",
        "source_url": "https://doi.org/10.1055/a-1547-2282",
        "rules": [
            ("Potpuna lista terapije", "Prije endoskopskog postupka.", "Evidentirati naziv, dozu i raspored antikoagulantne i antiagregacijske terapije te druge relevantne lijekove."),
            ("Vrsta planiranog postupka", "Pri procjeni rizika.", "Potvrditi planirani dijagnostički ili terapijski postupak i mogućnost uzimanja uzorka ili intervencije."),
            ("Rizik krvarenja i tromboze", "Prije odluke o terapiji.", "Procjenu radi liječnik uzimajući u obzir postupak i individualni tromboembolijski rizik."),
            ("Bez samostalne promjene terapije", "Ako se razmatra prekid, nastavak ili prilagodba lijeka.", "Ne savjetovati niti provoditi promjenu bez dokumentirane liječničke odluke."),
            ("Koordinacija s drugim liječnikom", "Kada je terapiju uveo drugi specijalist ili je rizik nejasan.", "Evidentirati potrebu za konzultacijom i zaprimljenu preporuku prije postupka."),
            ("Dokumentirana odluka i uputa", "Nakon stručne procjene.", "Evidentirati odluku, odgovornu osobu, vrijeme i jasne upute pacijentu; sustav ne donosi odluku automatski."),
        ],
    },
]


def upgrade() -> None:
    bind = op.get_bind()
    for protocol in PROTOCOLS:
        protocol_id = bind.execute(
            sa.text(
                """
                INSERT INTO knowledge_protocols
                    (key, title, specialty, version, summary, source_title, source_url, status)
                VALUES
                    (:key, :title, 'Gastroenterologija', '1.0', :summary, :source_title, :source_url, 'draft')
                ON CONFLICT (key) DO NOTHING
                RETURNING id
                """
            ),
            {
                "key": protocol["key"],
                "title": protocol["title"],
                "summary": (
                    f"Operativna kontrolna lista: {protocol['title']}. Ne donosi automatsku kliničku odluku; "
                    "konačnu procjenu, odobrenje i terapijske odluke donosi ovlašteni liječnik."
                ),
                "source_title": protocol["source_title"],
                "source_url": protocol["source_url"],
            },
        ).scalar_one_or_none()
        if protocol_id is None:
            continue
        for position, (label, condition_text, guidance_text) in enumerate(protocol["rules"]):
            bind.execute(
                sa.text(
                    """
                    INSERT INTO knowledge_rules
                        (protocol_id, label, condition_text, guidance_text, evidence_level, position)
                    VALUES
                        (:protocol_id, :label, :condition_text, :guidance_text, :evidence_level, :position)
                    """
                ),
                {
                    "protocol_id": protocol_id,
                    "label": label,
                    "condition_text": condition_text,
                    "guidance_text": guidance_text,
                    "evidence_level": EVIDENCE,
                    "position": position,
                },
            )


def downgrade() -> None:
    bind = op.get_bind()
    keys = [protocol["key"] for protocol in PROTOCOLS]
    protocol_ids = bind.execute(
        sa.select(sa.column("id")).select_from(sa.table("knowledge_protocols")).where(sa.column("key").in_(keys))
    ).scalars().all()
    if protocol_ids:
        bind.execute(sa.text("DELETE FROM knowledge_rules WHERE protocol_id = ANY(:ids)"), {"ids": protocol_ids})
        bind.execute(sa.text("DELETE FROM knowledge_protocols WHERE id = ANY(:ids)"), {"ids": protocol_ids})
