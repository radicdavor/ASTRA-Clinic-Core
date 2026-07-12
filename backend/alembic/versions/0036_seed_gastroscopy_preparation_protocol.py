"""seed gastroscopy preparation protocol

Revision ID: 0036_seed_gastroscopy_preparation_protocol
Revises: 0035_complete_laboratory_v1
"""

from alembic import op
import sqlalchemy as sa


revision = "0036_seed_gastroscopy_preparation_protocol"
down_revision = "0035_complete_laboratory_v1"
branch_labels = None
depends_on = None


PROTOCOL_KEY = "gastroscopy-preparation-v1"


def upgrade() -> None:
    bind = op.get_bind()
    protocol_id = bind.execute(
        sa.text(
            """
            INSERT INTO knowledge_protocols
                (key, title, specialty, version, summary, source_title, source_url, status)
            VALUES
                (:key, :title, :specialty, :version, :summary, :source_title, :source_url, 'draft')
            ON CONFLICT (key) DO NOTHING
            RETURNING id
            """
        ),
        {
            "key": PROTOCOL_KEY,
            "title": "Priprema za gastroskopiju",
            "specialty": "Gastroenterologija",
            "version": "1.0",
            "summary": (
                "Operativna kontrolna lista prije gastroskopije. Protokol ne donosi automatsku "
                "odluku o izvođenju zahvata; svaku nejasnoću i konačnu procjenu preuzima liječnik."
            ),
            "source_title": "ESGE/ESGENA guidance for a gastrointestinal endoscopy safety checklist",
            "source_url": "https://pubmed.ncbi.nlm.nih.gov/34905797/",
        },
    ).scalar_one_or_none()
    if protocol_id is None:
        return

    rules = [
        (
            "Potvrda identiteta i postupka",
            "Prije početka pripreme za zakazanu gastroskopiju.",
            "Potvrditi identitet pacijenta i zakazani postupak prema dostupnoj dokumentaciji.",
        ),
        (
            "Posljednji unos hrane i tekućine",
            "Tijekom prijema i provjere pripreme.",
            "Provjeriti i evidentirati kada je pacijent posljednji put jeo i pio; odstupanja proslijediti liječniku.",
        ),
        (
            "Terapija i lijekovi koji utječu na krvarenje",
            "Kada pacijent navodi redovitu ili povremenu terapiju.",
            "Evidentirati terapiju, posebno antikoagulantne i antiagregacijske lijekove. Ne mijenjati terapiju bez odluke liječnika.",
        ),
        (
            "Poznate alergije",
            "Prije primjene lijekova, lokalnog anestetika ili sedacije.",
            "Provjeriti i evidentirati poznate alergije te nejasne ili rizične podatke proslijediti liječniku.",
        ),
        (
            "Planirana sedacija",
            "Kada je sedacija navedena u planu postupka ili dokumentaciji.",
            "Potvrditi postoji li planirana sedacija i jesu li potrebne pripremne provjere evidentirane.",
        ),
        (
            "Razumijevanje uputa",
            "Nakon što su pacijentu dane upute za pripremu.",
            "Potvrditi da je pacijent dobio i razumio upute; otvorena pitanja uputiti odgovornom zdravstvenom radniku.",
        ),
        (
            "Evidencija provedene provjere",
            "Po završetku pripremne kontrolne liste.",
            "Evidentirati tko je proveo provjeru i vrijeme kada je provjera završena.",
        ),
        (
            "Eskalacija nejasnoća",
            "Ako bilo koji podatak nedostaje, proturječan je ili zahtijeva kliničku procjenu.",
            "Ne donositi automatski zaključak. Sve nejasnoće proslijediti odgovornom liječniku prije nastavka postupka.",
        ),
    ]
    for position, (label, condition_text, guidance_text) in enumerate(rules):
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
                "evidence_level": "Interni operativni korak – liječnički pregled obavezan",
                "position": position,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    protocol_id = bind.execute(
        sa.text("SELECT id FROM knowledge_protocols WHERE key = :key"),
        {"key": PROTOCOL_KEY},
    ).scalar_one_or_none()
    if protocol_id is not None:
        bind.execute(sa.text("DELETE FROM knowledge_rules WHERE protocol_id = :protocol_id"), {"protocol_id": protocol_id})
        bind.execute(sa.text("DELETE FROM knowledge_protocols WHERE id = :protocol_id"), {"protocol_id": protocol_id})
