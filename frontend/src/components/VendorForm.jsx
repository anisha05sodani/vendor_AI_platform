import { useEffect, useState } from "react";
import { getRequiredDocuments } from "../api.js";

const BUSINESS_TYPES = [
  "IT Services",
  "Manufacturing",
  "Logistics",
  "Finance",
  "Retail",
];

const COUNTRIES = ["India", "USA", "UK", "Germany", "Nigeria", "Russia", "China"];

// Fallback used only if the backend checklist endpoint is unreachable. The
// authoritative list comes from agents/config/required_documents.py via the API.
const FALLBACK_DOCUMENT_OPTIONS = [
  "Business Registration Certificate",
  "Tax Identification Document",
  "Proof of Address / Bank Statement",
  "ID Proof (Authorized Signatory)",
];

const labelCls = "block text-sm font-medium text-slate-700 mb-1";
const inputCls =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";

export default function VendorForm({ form, setForm, files, setFiles, onSubmit, loading }) {
  const [docOptions, setDocOptions] = useState(FALLBACK_DOCUMENT_OPTIONS);

  // Load the canonical checklist (tailored by business type / country) from the
  // backend whenever those change, so all layers share one source of truth.
  useEffect(() => {
    let active = true;
    getRequiredDocuments(form.business_type, form.country)
      .then((labels) => {
        if (active && labels.length) setDocOptions(labels);
      })
      .catch(() => {
        if (active) setDocOptions(FALLBACK_DOCUMENT_OPTIONS);
      });
    return () => {
      active = false;
    };
  }, [form.business_type, form.country]);

  const update = (key) => (e) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const toggleDoc = (doc) =>
    setForm((prev) => {
      const has = prev.documents_submitted.includes(doc);
      return {
        ...prev,
        documents_submitted: has
          ? prev.documents_submitted.filter((d) => d !== doc)
          : [...prev.documents_submitted, doc],
      };
    });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex h-full flex-col gap-4 overflow-y-auto p-5"
    >
      <div>
        <h2 className="text-lg font-semibold text-slate-800">📋 Vendor Details</h2>
        <p className="text-xs text-slate-500">
          Fill in the profile and run the multi-agent pipeline.
        </p>
      </div>

      <div>
        <label className={labelCls}>Vendor Name</label>
        <input
          className={inputCls}
          value={form.vendor_name}
          onChange={update("vendor_name")}
          required
        />
      </div>

      <div>
        <label className={labelCls}>Email</label>
        <input
          className={inputCls}
          type="email"
          value={form.vendor_email}
          onChange={update("vendor_email")}
          required
        />
      </div>

      <div>
        <label className={labelCls}>Business Type</label>
        <select
          className={inputCls}
          value={form.business_type}
          onChange={update("business_type")}
        >
          {BUSINESS_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className={labelCls}>Annual Revenue (USD)</label>
        <input
          className={inputCls}
          type="number"
          min="0"
          step="100000"
          value={form.annual_revenue}
          onChange={(e) =>
            setForm((prev) => ({
              ...prev,
              annual_revenue: Number(e.target.value),
            }))
          }
          required
        />
      </div>

      <div>
        <label className={labelCls}>Country</label>
        <select
          className={inputCls}
          value={form.country}
          onChange={update("country")}
        >
          {COUNTRIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className={labelCls}>Documents Submitted (checklist)</label>
        <div className="space-y-1.5 rounded-lg border border-slate-200 p-3">
          {docOptions.map((doc) => (
            <label
              key={doc}
              className="flex cursor-pointer items-center gap-2 text-sm text-slate-700"
            >
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                checked={form.documents_submitted.includes(doc)}
                onChange={() => toggleDoc(doc)}
              />
              {doc}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className={labelCls}>Upload Document Files</label>
        <input
          className="w-full text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-indigo-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-indigo-700 hover:file:bg-indigo-100"
          type="file"
          multiple
          accept=".pdf,.docx,.png,.jpg,.jpeg"
          onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
        />
        {files.length > 0 && (
          <p className="mt-1 text-xs text-slate-500">
            {files.length} file{files.length > 1 ? "s" : ""} selected
          </p>
        )}
        <p className="mt-1 text-xs text-slate-400">
          PDF / DOCX / scanned images verified by the Document Verification agent.
        </p>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="mt-auto inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "🔄 Running pipeline…" : "🚀 Run AI Pipeline"}
      </button>
    </form>
  );
}
