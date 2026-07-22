from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy import select
from sqlalchemy.orm import Session,joinedload,selectinload
from app.audit.service import audit,snapshot
from app.auth.dependencies import CurrentUserContext,require_active_clinic
from app.core.database import get_db
from app.models.domain import JourneyEncounter,PatientJourney
from app.schemas.journey_encounter import DiagnosisSuggestionDecision,DiagnosisSuggestionRequest,DiagnosisSuggestionsOut,EncounterOut,EncounterUpdate
from app.services.encounter_diagnosis import DiagnosisSuggestionUnavailable,ensure_diagnosis_suggestions_enabled,normalize_icd_code,suggest_icd10_diagnoses
from app.services.patient_journeys import transition
from app.core.config import get_settings
router=APIRouter(prefix="/api/patient-journeys",tags=["journey-encounter"])
def get_journey(db,id,clinic_id):
 item=db.scalar(select(PatientJourney).options(joinedload(PatientJourney.appointment),selectinload(PatientJourney.blockers),selectinload(PatientJourney.activities)).where(PatientJourney.id==id,PatientJourney.clinic_id==clinic_id))
 if not item: raise HTTPException(404,detail="Tijek pacijenta nije pronađen")
 return item
def deny_activity_legacy_write(journey,request,db,actor):
 activity_form_required = any(
  item.package_item_id is not None
  or item.activity_key != "primary"
  or item.form_resolution_status in {"resolved"}
  for item in journey.activities
 )
 if get_settings().clinical_activity_forms_required and activity_form_required:
  audit(db,"legacy_encounter_write_denied","PatientJourney",journey.id,"Novi klinički sadržaj mora se upisati u obrazac odabrane aktivnosti",actor.user_id,actor.actor_type,actor.api_key_id,None,{"activity_ids":[item.id for item in journey.activities]},request);db.commit()
  raise HTTPException(409,detail="Ovaj dolazak koristi obrasce po aktivnostima. Otvorite odabranu aktivnost i njezin klinički obrazac.")
def get_encounter(db,jid):
 item=db.scalar(select(JourneyEncounter).where(JourneyEncounter.journey_id==jid))
 if not item: raise HTTPException(404,detail="Klinički susret nije otvoren")
 return item
@router.post("/{journey_id}/encounter",response_model=EncounterOut)
def open_encounter(journey_id:int,request:Request,db:Session=Depends(get_db),context:CurrentUserContext=Depends(require_active_clinic("encounter.write"))):
 actor=context.actor;journey=get_journey(db,journey_id,context.active_clinic_id)
 deny_activity_legacy_write(journey,request,db,actor)
 if db.scalar(select(JourneyEncounter).where(JourneyEncounter.journey_id==journey.id)): raise HTTPException(409,detail="Klinički susret je već otvoren")
 transition(db,journey,"in_encounter",actor,request,"Liječnik otvorio klinički susret");item=JourneyEncounter(journey_id=journey.id,clinical_episode_id=journey.appointment.episode_id,opened_by=actor.user_id);db.add(item);db.flush();audit(db,"encounter_opened","JourneyEncounter",item.id,"Otvoren klinički susret",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();db.refresh(item);return item
@router.get("/{journey_id}/encounter",response_model=EncounterOut)
def encounter_detail(journey_id:int,db:Session=Depends(get_db),context:CurrentUserContext=Depends(require_active_clinic("encounter.read"))): get_journey(db,journey_id,context.active_clinic_id);return get_encounter(db,journey_id)
@router.patch("/{journey_id}/encounter",response_model=EncounterOut)
def update_encounter(journey_id:int,payload:EncounterUpdate,request:Request,db:Session=Depends(get_db),context:CurrentUserContext=Depends(require_active_clinic("encounter.write"))):
 actor=context.actor;deny_activity_legacy_write(get_journey(db,journey_id,context.active_clinic_id),request,db,actor)
 item=get_encounter(db,journey_id)
 if item.status!="in_progress": raise HTTPException(409,detail="Dovršeni susret nije moguće mijenjati")
 before=snapshot(item)
 for key,value in payload.model_dump(exclude_unset=True).items(): setattr(item,key,value)
 audit(db,"encounter_updated","JourneyEncounter",item.id,"Ažurirana bilješka kliničkog susreta",actor.user_id,actor.actor_type,actor.api_key_id,before,snapshot(item),request);db.commit();db.refresh(item);return item
@router.post("/{journey_id}/encounter/diagnosis-suggestions",response_model=DiagnosisSuggestionsOut)
def suggest_diagnoses(journey_id:int,payload:DiagnosisSuggestionRequest,request:Request,db:Session=Depends(get_db),context:CurrentUserContext=Depends(require_active_clinic("encounter.write"))):
 actor=context.actor;deny_activity_legacy_write(get_journey(db,journey_id,context.active_clinic_id),request,db,actor)
 item=get_encounter(db,journey_id)
 if item.status!="in_progress": raise HTTPException(409,detail="AI prijedlog nije dostupan za dovršeni pregled")
 try:
  ensure_diagnosis_suggestions_enabled()
  result=suggest_icd10_diagnoses(payload)
 except ValueError as exc: raise HTTPException(422,detail=str(exc)) from exc
 except DiagnosisSuggestionUnavailable as exc: raise HTTPException(503,detail=str(exc)) from exc
 audit(db,"ai_diagnosis_suggestions_requested","JourneyEncounter",item.id,"Stvoreni AI prijedlozi WHO ICD-10 dijagnoza",actor.user_id,actor.actor_type,actor.api_key_id,None,{"provider":result.provider,"model":result.model,"count":len(result.diagnoses),"suggestion_request_id":result.request_id},request);db.commit();return result
@router.post("/{journey_id}/encounter/diagnosis-suggestions/decision",response_model=EncounterOut)
def decide_diagnosis_suggestion(journey_id:int,payload:DiagnosisSuggestionDecision,request:Request,db:Session=Depends(get_db),context:CurrentUserContext=Depends(require_active_clinic("encounter.write"))):
 actor=context.actor;deny_activity_legacy_write(get_journey(db,journey_id,context.active_clinic_id),request,db,actor)
 item=get_encounter(db,journey_id)
 if item.status!="in_progress": raise HTTPException(409,detail="AI prijedlog nije dostupan za dovršeni pregled")
 try: catalog=ensure_diagnosis_suggestions_enabled()
 except DiagnosisSuggestionUnavailable as exc: raise HTTPException(503,detail=str(exc)) from exc
 code=normalize_icd_code(payload.code)
 canonical_title=catalog.get(code)
 if not canonical_title: raise HTTPException(422,detail="WHO ICD-10 šifra nije pronađena u kanonskom katalogu")
 event="ai_diagnosis_suggestion_rejected"
 after={"provider":payload.provider,"model":payload.model,"suggestion_request_id":payload.request_id,"code":code}
 if payload.action=="accept":
  line=f"{code} — {canonical_title}"
  lines=[value.strip() for value in (item.diagnosis or "").splitlines() if value.strip()]
  if line not in lines: lines.append(line)
  item.diagnosis="\n".join(lines)
  event="ai_diagnosis_suggestion_accepted"
  after["canonical_title"]=canonical_title
  after["final_code_added"]=code
 audit(db,event,"JourneyEncounter",item.id,"Liječnik je pojedinačno prihvatio AI prijedlog dijagnoze" if payload.action=="accept" else "Liječnik je pojedinačno odbio AI prijedlog dijagnoze",actor.user_id,actor.actor_type,actor.api_key_id,None,after,request)
 db.commit();db.refresh(item);return item
@router.post("/{journey_id}/encounter/complete",response_model=EncounterOut)
def complete_encounter(journey_id:int,request:Request,db:Session=Depends(get_db),context:CurrentUserContext=Depends(require_active_clinic("encounter.complete"))):
 actor=context.actor;journey=get_journey(db,journey_id,context.active_clinic_id);deny_activity_legacy_write(journey,request,db,actor);item=get_encounter(db,journey_id)
 if item.status!="in_progress": raise HTTPException(409,detail="Klinički susret je već dovršen")
 if not any((item.anamnesis,item.examination,item.patient_findings,item.opinion,item.procedure_findings,item.diagnosis,item.recommendations)): raise HTTPException(422,detail="Prije završetka upišite nalaz kliničkog susreta")
 item.status="completed";item.completed_by=actor.user_id;item.completed_at=datetime.now(timezone.utc);journey.encounter_status="completed";transition(db,journey,"procedure_completed",actor,request,"Liječnik dovršio postupak");audit(db,"encounter_completed","JourneyEncounter",item.id,"Dovršen klinički susret",actor.user_id,actor.actor_type,actor.api_key_id,None,snapshot(item),request);db.commit();db.refresh(item);return item
