import { useState } from "react";
import VendorForm from "./components/VendorForm.jsx";
import Results from "./components/Results.jsx";
import { onboardVendor } from "./api.js";

const INITIAL_FORM = {
  vendor_name: "TechNova Solutions Ltd",
  vendor_email: "contact@technova.com",
  business_type: "IT Services",
  annual_revenue: 2500000,
  country: "India",
  documents_submitted: ["Business Registration", "Tax Certificate", "ID Proof"],
};

export default function App() {
  const [form, setForm] = useState(INITIAL_FORM);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await onboardVendor(form, files);
      setResult(data);
    } catch (err) {
      setError(err.message || "Pipeline request failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <h1 className="text-2xl font-bold text-slate-900">
          🤖 Vendor AI Onboarding Platform
        </h1>
        <p className="text-sm text-slate-500">
          Multi-agent pipeline: Document Verification → Qualification → Fraud
          Detection → Compliance → KPI Summary
        </p>
      </header>

      <div className="flex flex-1 flex-col lg:flex-row">
        {/* Sidebar form */}
        <aside className="w-full border-b border-slate-200 bg-white lg:w-96 lg:border-b-0 lg:border-r">
          <VendorForm
            form={form}
            setForm={setForm}
            files={files}
            setFiles={setFiles}
            onSubmit={handleSubmit}
            loading={loading}
          />
        </aside>

        {/* Main results */}
        <main className="flex-1 p-6">
          {loading && (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600" />
                <p className="text-sm text-slate-600">
                  Running multi-agent pipeline… this can take ~20–30 seconds.
                </p>
              </div>
            </div>
          )}

          {!loading && error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <span className="font-semibold">Pipeline error:</span> {error}
            </div>
          )}

          {!loading && !error && result && <Results data={result} />}

          {!loading && !error && !result && <Welcome />}
        </main>
      </div>
    </div>
  );
}

function Welcome() {
  const rows = [
    ["0️⃣", "Document Verification Agent", "Reads uploaded files, checks them against the required-document checklist"],
    ["1️⃣", "Qualification Agent", "Checks eligibility, documents, risk level"],
    ["2️⃣", "Fraud Detection Agent", "Scores vendor for suspicious patterns"],
    ["3️⃣", "Compliance Agent", "Checks GDPR, AML/KYC, SOX regulations"],
    ["4️⃣", "KPI Summary Agent", "Produces executive-level decision report"],
  ];
  return (
    <div className="mx-auto max-w-3xl">
      <div className="rounded-lg border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-indigo-800">
        👈 Fill in the vendor details and click <strong>Run AI Pipeline</strong>{" "}
        to start.
      </div>
      <h2 className="mt-6 mb-3 text-lg font-semibold text-slate-800">
        How it works
      </h2>
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-2">Step</th>
              <th className="px-4 py-2">Agent</th>
              <th className="px-4 py-2">What it does</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map(([step, agent, desc]) => (
              <tr key={agent} className="text-slate-700">
                <td className="px-4 py-2">{step}</td>
                <td className="px-4 py-2 font-medium">{agent}</td>
                <td className="px-4 py-2">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
