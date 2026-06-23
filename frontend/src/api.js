// Thin API client for the Vendor AI FastAPI backend.
//
// In development, requests go to a relative "/api/..." path which the Vite dev
// server proxies to http://localhost:8000 (see vite.config.js). In production
// set VITE_API_URL to the deployed backend origin.
const API_BASE = import.meta.env.VITE_API_URL ?? "";

export async function onboardVendor(form, files) {
  const data = new FormData();
  data.append("vendor_name", form.vendor_name);
  data.append("vendor_email", form.vendor_email);
  data.append("business_type", form.business_type);
  data.append("annual_revenue", String(form.annual_revenue));
  data.append("country", form.country);
  data.append("documents_submitted", JSON.stringify(form.documents_submitted));

  for (const file of files ?? []) {
    data.append("files", file, file.name);
  }

  const resp = await fetch(`${API_BASE}/api/v1/onboard`, {
    method: "POST",
    body: data,
  });

  if (!resp.ok) {
    let detail = `Request failed with status ${resp.status}`;
    try {
      const body = await resp.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // response had no JSON body; keep the generic message
    }
    throw new Error(detail);
  }

  return resp.json();
}
