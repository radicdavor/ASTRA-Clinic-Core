# Program 1 Phase C104 - Acknowledgment Read Audit Policy Design

Status: audit policy design

## Svrha

C104 definira politiku za buduce auditiranje read pristupa Human Review Acknowledgment zapisima.

Ova faza ne uvodi runtime read audit.

## Sto Je Read Audit

Read audit je access/security zapis o pokusaju citanja acknowledgment podataka.

Moze dokumentirati:

- tko je pokusao citati
- koji appointment context je bio trazen
- je li trazen list ili detail read
- je li pristup odbijen ili je read failao

## Sto Read Audit Nije

Read audit nije:

- clinical approval
- readiness clearance
- override
- Outcome Evidence
- Task
- appointment status
- patient message
- dokaz da je advisory signal rijesen

## Access Audit vs Clinical Evidence

Access audit dokazuje dogadjaj pristupa.

Clinical evidence dokazuje klinicki sadrzaj ili odluku.

Acknowledgment read audit, ako se kasnije uvede, mora ostati access/security evidence i ne smije postati Outcome Evidence.

## List Read vs Detail Read

List read:

- moze biti cest zbog Appointment Workspace renderiranja
- ima visok audit-noise rizik
- ne treba se automatski auditirati bez dodatne odluke

Detail read:

- moze biti osjetljiviji jer korisnik trazi specifican record
- moze biti kandidat za selektivni audit kasnije
- i dalje nije automatski odobren za runtime audit

## Permission Denied Read

Permission denied read ima vecu sigurnosnu vrijednost od normalnog list refresha.

Buduci denied-read audit moze biti dobar prvi runtime korak jer hvata:

- korisnika bez read permissiona
- API key pokusaj
- AI/system pokusaj
- out-of-scope access pokusaj

## Failed Read

Failed read moze ukljucivati:

- nepostojeci appointment
- nepostojeci acknowledgment
- appointment/snapshot/patient mismatch
- neocekivani server error

Failed read treba auditirati samo ako payload ostaje privacy-safe i ne stvara audit-noise.

## Audit-Noise Rizik

Auditiranje svakog read requesta moze brzo zatrpati audit log jer Appointment Workspace i frontend refresh mogu ponavljati list read.

Noise smanjuje vrijednost sigurnosne analize i moze sakriti stvarno sumnjive dogadjaje.

## Privacy Implications

Read audit payload mora biti minimalan.

Ne smije spremati puni reason text ili klinicki sadrzaj osim ako se kasnije posebno odobri.

## Demo/Pilot Assumption

Ova politika je za guarded demo/pilot razvoj.

Ne odobrava production niti stvarne podatke pacijenata.

## Why Implementation Is Not Automatic

Runtime implementation se ne uvodi u C104 jer:

- treba odluciti selective audit opseg
- treba sprijeciti audit-noise
- treba definirati privacy-safe payload
- treba potvrditi da read audit nije clinical evidence

## Policy Position

Najbolji buduci implementacijski kandidat je:

`denied-read audit only`

Normalni list/detail read audit ostaje deferred.

