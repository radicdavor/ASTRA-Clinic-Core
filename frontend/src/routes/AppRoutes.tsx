import { Fragment, lazy, Suspense, useEffect, useState } from "react";
import { Location, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { RouteModal } from "../components/RouteModal";
import { fetchSession, getSessionUser } from "../api/client";
import { DailyClinicDashboard } from "../pages/DailyClinicDashboard";
import { Login } from "../pages/Login";

const AppointmentForm = lazy(() => import("../pages/AppointmentForm").then(module => ({ default: module.AppointmentForm })));
const PackageBooking = lazy(() => import("../pages/PackageBooking").then(module => ({ default: module.PackageBooking })));
const AppointmentDetail = lazy(() => import("../pages/AppointmentDetail").then(module => ({ default: module.AppointmentDetail })));
const Appointments = lazy(() => import("../pages/Appointments").then(module => ({ default: module.Appointments })));
const AuditLog = lazy(() => import("../pages/AuditLog").then(module => ({ default: module.AuditLog })));
const ApiKeys = lazy(() => import("../pages/ApiKeys").then(module => ({ default: module.ApiKeys })));
const PatientJourneyWorkspace = lazy(() => import("../pages/PatientJourneyWorkspace").then(module => ({ default: module.PatientJourneyWorkspace })));
const ClinicalDocumentDetail = lazy(() => import("../pages/ClinicalDocumentDetail").then(module => ({ default: module.ClinicalDocumentDetail })));
const ClinicalDocuments = lazy(() => import("../pages/ClinicalDocuments").then(module => ({ default: module.ClinicalDocuments })));
const Clinics = lazy(() => import("../pages/Clinics").then(module => ({ default: module.Clinics })));
const EpisodeDetail = lazy(() => import("../pages/EpisodeDetail").then(module => ({ default: module.EpisodeDetail })));
const EpisodeForm = lazy(() => import("../pages/EpisodeForm").then(module => ({ default: module.EpisodeForm })));
const Episodes = lazy(() => import("../pages/Episodes").then(module => ({ default: module.Episodes })));
const Inventory = lazy(() => import("../pages/Inventory").then(module => ({ default: module.Inventory })));
const Invoices = lazy(() => import("../pages/Invoices").then(module => ({ default: module.Invoices })));
const Laboratory = lazy(() => import("../pages/Laboratory").then(module => ({ default: module.Laboratory })));
const Therapies = lazy(() => import("../pages/Therapies").then(module => ({ default: module.Therapies })));
const Modules = lazy(() => import("../pages/Modules").then(module => ({ default: module.Modules })));
const PatientDetail = lazy(() => import("../pages/PatientDetail").then(module => ({ default: module.PatientDetail })));
const PatientForm = lazy(() => import("../pages/PatientForm").then(module => ({ default: module.PatientForm })));
const Patients = lazy(() => import("../pages/Patients").then(module => ({ default: module.Patients })));
const PurchaseOrders = lazy(() => import("../pages/PurchaseOrders").then(module => ({ default: module.PurchaseOrders })));
const Readiness = lazy(() => import("../pages/Readiness").then(module => ({ default: module.Readiness })));
const Reception = lazy(() => import("../pages/Reception").then(module => ({ default: module.Reception })));
const Services = lazy(() => import("../pages/Services").then(module => ({ default: module.Services })));
const Suppliers = lazy(() => import("../pages/Suppliers").then(module => ({ default: module.Suppliers })));
const WorkflowTaskDetail = lazy(() => import("../pages/WorkflowTaskDetail").then(module => ({ default: module.WorkflowTaskDetail })));
const WorkflowTasks = lazy(() => import("../pages/WorkflowTasks").then(module => ({ default: module.WorkflowTasks })));
const KnowledgeProtocolDetail = lazy(() => import("../pages/KnowledgeProtocolDetail").then(module => ({ default: module.KnowledgeProtocolDetail })));
const KnowledgeProtocols = lazy(() => import("../pages/KnowledgeProtocols").then(module => ({ default: module.KnowledgeProtocols })));
const GastroenterologyWorkspace = lazy(() => import("../pages/GastroenterologyWorkspace").then(module => ({ default: module.GastroenterologyWorkspace })));
const SyntheticReviewWorkspace = lazy(() => import("../program1/pages/SyntheticReviewWorkspace").then(module => ({ default: module.SyntheticReviewWorkspace })));
const SyntheticEvaluationRunner = lazy(() => import("../program1/pages/SyntheticEvaluationRunner").then(module => ({ default: module.SyntheticEvaluationRunner })));

function Protected() {
  const [status, setStatus] = useState<"loading" | "authenticated" | "unauthenticated">(() => getSessionUser() ? "authenticated" : "loading");
  useEffect(() => {
    let active = true;
    fetchSession()
      .then((session) => {
        if (active) setStatus(session ? "authenticated" : "unauthenticated");
      })
      .catch(() => {
        if (active) setStatus("unauthenticated");
      });
    return () => {
      active = false;
    };
  }, []);
  if (status === "loading") return <div className="page"><p>Provjera prijave…</p></div>;
  return status === "authenticated" ? <AppShell /> : <Navigate to="/login" replace />;
}

export function AppRoutes() {
  const location = useLocation();
  const state = location.state as { backgroundLocation?: Location } | null;
  const backgroundLocation = state?.backgroundLocation;

  return (
    <Suspense fallback={<div className="page"><p>Učitavanje…</p></div>}>
      <Fragment>
      <Routes location={backgroundLocation ?? location}>
        <Route path="/login" element={<Login />} />
        <Route element={<Protected />}>
          <Route path="/" element={<DailyClinicDashboard />} />
          <Route path="/patients" element={<Patients />} />
          <Route path="/patients/new" element={<PatientForm />} />
          <Route path="/patients/:id" element={<PatientDetail />} />
          <Route path="/reception" element={<Reception />} />
          <Route path="/episodes" element={<Episodes />} />
          <Route path="/episodes/new" element={<EpisodeForm />} />
          <Route path="/episodes/:id" element={<EpisodeDetail />} />
          <Route path="/clinical-documents" element={<ClinicalDocuments />} />
          <Route path="/laboratory" element={<Laboratory />} />
          <Route path="/therapies" element={<Therapies />} />
          <Route path="/clinical-documents/:id" element={<ClinicalDocumentDetail />} />
          <Route path="/appointments" element={<Appointments />} />
          <Route path="/appointments/new" element={<AppointmentForm />} />
          <Route path="/appointments/package" element={<PackageBooking />} />
          <Route path="/appointments/:id" element={<AppointmentDetail />} />
          <Route path="/journeys/:id" element={<PatientJourneyWorkspace />} />
          <Route path="/workflow" element={<WorkflowTasks />} />
          <Route path="/workflow/:id" element={<WorkflowTaskDetail />} />
          <Route path="/knowledge" element={<KnowledgeProtocols />} />
          <Route path="/knowledge/:id" element={<KnowledgeProtocolDetail />} />
          <Route path="/gastroenterology" element={<GastroenterologyWorkspace />} />
          <Route path="/services" element={<Services />} />
          <Route path="/clinics" element={<Clinics />} />
          <Route path="/modules" element={<Modules />} />
          <Route path="/inventory" element={<Inventory />} />
          <Route path="/suppliers" element={<Suppliers />} />
          <Route path="/purchase-orders" element={<PurchaseOrders />} />
          <Route path="/invoices" element={<Invoices />} />
          <Route path="/audit-log" element={<AuditLog />} />
          <Route path="/api-keys" element={<ApiKeys />} />
          <Route path="/readiness" element={<Readiness />} />
          <Route path="/program1/synthetic-review" element={<SyntheticReviewWorkspace />} />
          <Route path="/program1/synthetic-evaluation" element={<SyntheticEvaluationRunner />} />
        </Route>
      </Routes>
      {backgroundLocation && getSessionUser() && (
        <Routes>
          <Route path="/appointments/new" element={<RouteModal title="Novi termin"><AppointmentForm /></RouteModal>} />
          <Route path="/appointments/:id" element={<RouteModal title="Detalj termina"><AppointmentDetail /></RouteModal>} />
          <Route path="/knowledge/:id" element={<RouteModal title="Klinički protokol"><KnowledgeProtocolDetail /></RouteModal>} />
        </Routes>
      )}
      </Fragment>
    </Suspense>
  );
}
