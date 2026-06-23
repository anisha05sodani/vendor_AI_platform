import { useState } from "react";
import { MetricCard, JsonBlock } from "./widgets.jsx";

const DECISION_STYLES = {
  APPROVED: { dot: "🟢", badge: "bg-green-100 text-green-800 ring-green-600/20" },
  REJECTED: { dot: "🔴", badge: "bg-red-100 text-red-800 ring-red-600/20" },
  PENDING_REVIEW: {
    dot: "🟡",
    badge: "bg-amber-100 text-amber-800 ring-amber-600/20",
  },
};

const DOC_STATUS_ICON = {
  complete: "🟢",
  incomplete: "🔴",
  flagged: "🟡",
};

const TABS = [
  { key: "documents", label: "📁 Documents" },
  { key: "qualification", label: "🏷️ Qualification" },
  { key: "fraud", label: "🔍 Fraud Detection" },
  { key: "compliance", label: "📄 Compliance" },
  { key: "kpi", label: "📊 KPI Summary" },
];

function titleCase(value) {
  if (!value) return "N/A";
  return String(value)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function Results({ data }) {
  const [tab, setTab] = useState("documents");

  const decision = data.final_decision || "UNKNOWN";
  const style = DECISION_STYLES[decision] || {
    dot: "⚪",
    badge: "bg-slate-100 text-slate-700 ring-slate-600/20",
  };

  const kpi = data.kpi_summary || {};
  const fraud = data.fraud_result || {};
  const qual = data.qualification_result || {};
  const comp = data.compliance_result || {};
  const docver = data.document_verification_result || {};

  return (
    <div className="space-y-6">
      {/* Final decision */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-xl font-semibold text-slate-800">
          {style.dot} Final Decision:
        </span>
        <span
          className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-bold ring-1 ring-inset ${style.badge}`}
        >
          {decision}
        </span>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          label="Overall Score"
          value={`${kpi.overall_score ?? "N/A"}/100`}
        />
        <MetricCard
          label="Fraud Score"
          value={`${fraud.fraud_score ?? "N/A"}/100`}
        />
        <MetricCard
          label="Risk Level"
          value={(qual.risk_level || "N/A").toUpperCase()}
        />
        <MetricCard
          label="Compliance"
          value={titleCase(comp.compliance_status)}
        />
      </div>

      {/* Tabs */}
      <div>
        <div className="flex flex-wrap gap-1 border-b border-slate-200">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`-mb-px rounded-t-lg px-4 py-2 text-sm font-medium transition ${
                tab === t.key
                  ? "border border-b-white border-slate-200 bg-white text-indigo-700"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="rounded-b-lg rounded-tr-lg border border-t-0 border-slate-200 bg-white p-5">
          {tab === "documents" && <DocumentsTab docver={docver} />}
          {tab === "qualification" && (
            <SimpleTab title="Vendor Qualification Agent" data={qual} />
          )}
          {tab === "fraud" && <FraudTab fraud={fraud} />}
          {tab === "compliance" && <ComplianceTab comp={comp} />}
          {tab === "kpi" && <KpiTab kpi={kpi} />}
        </div>
      </div>
    </div>
  );
}

function DocumentsTab({ docver }) {
  if (!docver || Object.keys(docver).length === 0) {
    return <Empty>No document verification data.</Empty>;
  }
  const status = docver.overall_document_status || "N/A";
  const checked = docver.documents_checked || [];
  const missing = docver.missing_required_documents || [];

  return (
    <div className="space-y-4">
      <h3 className="text-base font-semibold text-slate-800">
        Document Verification Agent
      </h3>
      <p className="text-sm text-slate-700">
        <span className="font-medium">Overall Status:</span>{" "}
        {DOC_STATUS_ICON[status] || "⚪"} <code>{status}</code>
      </p>
      {docver.summary && (
        <p className="text-sm text-slate-600">
          <span className="font-medium">Summary:</span> {docver.summary}
        </p>
      )}
      {missing.length > 0 && (
        <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          Missing required documents: {missing.join(", ")}
        </div>
      )}
      {checked.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2">Document Type</th>
                <th className="px-3 py-2">Uploaded File</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Validity</th>
                <th className="px-3 py-2">Comments</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {checked.map((row, i) => (
                <tr key={i} className="text-slate-700">
                  <td className="px-3 py-2 font-medium">{row.document_type}</td>
                  <td className="px-3 py-2">
                    {row.filename ? (
                      <span>
                        {row.filename}
                        {row.detected_confidence && (
                          <span className="ml-1 text-xs text-slate-400">
                            ({row.detected_confidence})
                          </span>
                        )}
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>
                  <td className="px-3 py-2">{row.status}</td>
                  <td className="px-3 py-2">{row.validity}</td>
                  <td className="px-3 py-2">{row.comments}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Raw data={docver} />
    </div>
  );
}

function FraudTab({ fraud }) {
  if (!fraud || Object.keys(fraud).length === 0) {
    return <Empty>No fraud data.</Empty>;
  }
  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold text-slate-800">
        Fraud Detection Agent
      </h3>
      {(fraud.flags || []).map((flag, i) => (
        <div
          key={i}
          className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800"
        >
          ⚠️ {flag}
        </div>
      ))}
      <JsonBlock data={fraud} />
    </div>
  );
}

function ComplianceTab({ comp }) {
  if (!comp || Object.keys(comp).length === 0) {
    return <Empty>No compliance data.</Empty>;
  }
  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold text-slate-800">
        Compliance Reporting Agent
      </h3>
      {(comp.action_items || []).map((item, i) => (
        <div
          key={i}
          className="rounded-lg bg-sky-50 px-3 py-2 text-sm text-sky-800"
        >
          📌 {item}
        </div>
      ))}
      <JsonBlock data={comp} />
    </div>
  );
}

function KpiTab({ kpi }) {
  if (!kpi || Object.keys(kpi).length === 0) {
    return <Empty>No KPI data.</Empty>;
  }
  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold text-slate-800">
        Executive KPI Summary Agent
      </h3>
      {kpi.executive_summary && (
        <p className="text-sm text-slate-700">
          <span className="font-medium">Executive Summary:</span>{" "}
          {kpi.executive_summary}
        </p>
      )}
      {(kpi.next_steps || []).length > 0 && (
        <div>
          <p className="text-sm font-medium text-slate-700">Next Steps:</p>
          <ul className="ml-5 list-disc text-sm text-slate-600">
            {kpi.next_steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ul>
        </div>
      )}
      <JsonBlock data={kpi} />
    </div>
  );
}

function SimpleTab({ title, data }) {
  if (!data || Object.keys(data).length === 0) {
    return <Empty>No data.</Empty>;
  }
  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold text-slate-800">{title}</h3>
      <JsonBlock data={data} />
    </div>
  );
}

function Raw({ data }) {
  return (
    <details className="text-sm">
      <summary className="cursor-pointer text-slate-500 hover:text-slate-700">
        Raw JSON
      </summary>
      <div className="mt-2">
        <JsonBlock data={data} />
      </div>
    </details>
  );
}

function Empty({ children }) {
  return (
    <div className="rounded-lg bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
      {children}
    </div>
  );
}
