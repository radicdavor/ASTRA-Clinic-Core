import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { getToken } from "../api/client";
import { AppointmentForm } from "../pages/AppointmentForm";
import { AppointmentDetail } from "../pages/AppointmentDetail";
import { Appointments } from "../pages/Appointments";
import { AuditLog } from "../pages/AuditLog";
import { ApiKeys } from "../pages/ApiKeys";
import { Dashboard } from "../pages/Dashboard";
import { ClinicalDocumentDetail } from "../pages/ClinicalDocumentDetail";
import { ClinicalDocuments } from "../pages/ClinicalDocuments";
import { EpisodeDetail } from "../pages/EpisodeDetail";
import { EpisodeForm } from "../pages/EpisodeForm";
import { Episodes } from "../pages/Episodes";
import { Inventory } from "../pages/Inventory";
import { Invoices } from "../pages/Invoices";
import { Login } from "../pages/Login";
import { Modules } from "../pages/Modules";
import { PatientDetail } from "../pages/PatientDetail";
import { PatientForm } from "../pages/PatientForm";
import { Patients } from "../pages/Patients";
import { PurchaseOrders } from "../pages/PurchaseOrders";
import { Readiness } from "../pages/Readiness";
import { Reception } from "../pages/Reception";
import { Services } from "../pages/Services";
import { Suppliers } from "../pages/Suppliers";

function Protected() {
  return getToken() ? <AppShell /> : <Navigate to="/login" replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Protected />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/patients" element={<Patients />} />
        <Route path="/patients/new" element={<PatientForm />} />
        <Route path="/patients/:id" element={<PatientDetail />} />
        <Route path="/reception" element={<Reception />} />
        <Route path="/episodes" element={<Episodes />} />
        <Route path="/episodes/new" element={<EpisodeForm />} />
        <Route path="/episodes/:id" element={<EpisodeDetail />} />
        <Route path="/clinical-documents" element={<ClinicalDocuments />} />
        <Route path="/clinical-documents/:id" element={<ClinicalDocumentDetail />} />
        <Route path="/appointments" element={<Appointments />} />
        <Route path="/appointments/new" element={<AppointmentForm />} />
        <Route path="/appointments/:id" element={<AppointmentDetail />} />
        <Route path="/services" element={<Services />} />
        <Route path="/modules" element={<Modules />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/suppliers" element={<Suppliers />} />
        <Route path="/purchase-orders" element={<PurchaseOrders />} />
        <Route path="/invoices" element={<Invoices />} />
        <Route path="/audit-log" element={<AuditLog />} />
        <Route path="/api-keys" element={<ApiKeys />} />
        <Route path="/readiness" element={<Readiness />} />
      </Route>
    </Routes>
  );
}
