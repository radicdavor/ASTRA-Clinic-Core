import { Fragment } from "react";
import { Location, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { RouteModal } from "../components/RouteModal";
import { getToken } from "../api/client";
import { AppointmentForm } from "../pages/AppointmentForm";
import { PackageBooking } from "../pages/PackageBooking";
import { AppointmentDetail } from "../pages/AppointmentDetail";
import { Appointments } from "../pages/Appointments";
import { AuditLog } from "../pages/AuditLog";
import { ApiKeys } from "../pages/ApiKeys";
import { DailyClinicDashboard } from "../pages/DailyClinicDashboard";
import { PatientJourneyWorkspace } from "../pages/PatientJourneyWorkspace";
import { ClinicalDocumentDetail } from "../pages/ClinicalDocumentDetail";
import { ClinicalDocuments } from "../pages/ClinicalDocuments";
import { Clinics } from "../pages/Clinics";
import { EpisodeDetail } from "../pages/EpisodeDetail";
import { EpisodeForm } from "../pages/EpisodeForm";
import { Episodes } from "../pages/Episodes";
import { Inventory } from "../pages/Inventory";
import { Invoices } from "../pages/Invoices";
import { Login } from "../pages/Login";
import { Laboratory } from "../pages/Laboratory";
import { Therapies } from "../pages/Therapies";
import { Modules } from "../pages/Modules";
import { PatientDetail } from "../pages/PatientDetail";
import { PatientForm } from "../pages/PatientForm";
import { Patients } from "../pages/Patients";
import { PurchaseOrders } from "../pages/PurchaseOrders";
import { Readiness } from "../pages/Readiness";
import { Reception } from "../pages/Reception";
import { Services } from "../pages/Services";
import { Suppliers } from "../pages/Suppliers";
import { WorkflowTaskDetail } from "../pages/WorkflowTaskDetail";
import { WorkflowTasks } from "../pages/WorkflowTasks";
import { KnowledgeProtocolDetail } from "../pages/KnowledgeProtocolDetail";
import { KnowledgeProtocols } from "../pages/KnowledgeProtocols";
import { GastroenterologyWorkspace } from "../pages/GastroenterologyWorkspace";
import { SyntheticReviewWorkspace } from "../program1/pages/SyntheticReviewWorkspace";
import { SyntheticEvaluationRunner } from "../program1/pages/SyntheticEvaluationRunner";

function Protected() {
  return getToken() ? <AppShell /> : <Navigate to="/login" replace />;
}

export function AppRoutes() {
  const location = useLocation();
  const state = location.state as { backgroundLocation?: Location } | null;
  const backgroundLocation = state?.backgroundLocation;

  return (
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
      {backgroundLocation && getToken() && (
        <Routes>
          <Route path="/appointments/new" element={<RouteModal title="Novi termin"><AppointmentForm /></RouteModal>} />
          <Route path="/appointments/:id" element={<RouteModal title="Detalj termina"><AppointmentDetail /></RouteModal>} />
          <Route path="/knowledge/:id" element={<RouteModal title="Klinički protokol"><KnowledgeProtocolDetail /></RouteModal>} />
        </Routes>
      )}
    </Fragment>
  );
}
