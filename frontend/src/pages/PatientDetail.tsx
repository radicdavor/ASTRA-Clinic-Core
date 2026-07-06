import { useParams } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { Patient } from "../types";
import { formatDate } from "../utils/date";

export function PatientDetail() {
  const { id } = useParams();
  const { data } = useApi<Patient>(`/api/patients/${id}`, {} as Patient);
  return (
    <section className="page narrow">
      <h1>{data.first_name} {data.last_name}</h1>
      <div className="detail-list">
        <p><strong>Datum rodenja</strong><span>{formatDate(data.date_of_birth)}</span></p>
        <p><strong>OIB</strong><span>{data.oib ?? "-"}</span></p>
        <p><strong>Telefon</strong><span>{data.phone ?? "-"}</span></p>
        <p><strong>E-posta</strong><span>{data.email ?? "-"}</span></p>
        <p><strong>Napomene</strong><span>{data.notes ?? "-"}</span></p>
      </div>
    </section>
  );
}
