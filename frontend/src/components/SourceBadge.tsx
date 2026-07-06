import { Link } from "react-router-dom";
import { PatientKnowledgeSource } from "../types";
import { formatDate } from "../utils/date";

export function SourceBadge({ source }: { source: PatientKnowledgeSource }) {
  return (
    <Link className="source-badge" to={`/clinical-documents/${source.document_id}`}>
      {source.title} {source.document_date ? `/${formatDate(source.document_date)}` : ""}
    </Link>
  );
}
