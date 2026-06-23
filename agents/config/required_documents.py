"""
Required-document checklist configuration.

Edit this file to change which documents are required for vendor onboarding,
without touching any agent logic. Requirements can be tailored by
``business_type`` and/or ``country``.

Each checklist entry is a dict:
    {
        "key":      canonical machine-readable id (used in agent output),
        "label":    human-readable name (shown in UI / prompts),
        "keywords": lowercase substrings used to match an uploaded document
                    to this requirement (filename + extracted text),
    }
"""
from typing import Optional


# --- Documents every vendor must submit -------------------------------------
BASE_REQUIRED_DOCUMENTS: list[dict] = [
    {
        "key": "business_registration_certificate",
        "label": "Business Registration Certificate",
        "keywords": [
            "registration", "incorporation", "certificate of incorporation",
            "business license", "company registration", "registered office",
        ],
    },
    {
        "key": "tax_identification_document",
        "label": "Tax Identification Document",
        "keywords": [
            "tax", "vat", "gst", "ein", "tin", "pan", "tax identification",
            "tax certificate",
        ],
    },
    {
        "key": "proof_of_address_or_bank_statement",
        "label": "Proof of Address / Bank Statement",
        "keywords": [
            "bank statement", "proof of address", "utility bill", "address",
            "account statement", "iban", "sort code",
        ],
    },
    {
        "key": "identity_proof_document",
        "label": "ID Proof (Authorized Signatory)",
        "keywords": [
            "id proof", "identity", "identity proof", "aadhaar", "passport",
            "national id", "photo identity", "din", "director identification",
            "driving license", "drivers license",
        ],
    },
]


# --- Conditional documents ---------------------------------------------------
INSURANCE_CERTIFICATE = {
    "key": "insurance_certificate",
    "label": "Insurance Certificate",
    "keywords": ["insurance", "liability cover", "policy", "coverage", "insurer"],
}

AUDITED_FINANCIALS = {
    "key": "audited_financials",
    "label": "Audited Financial Statements",
    "keywords": ["audited", "financial statement", "balance sheet", "profit and loss", "auditor"],
}

GDPR_DPA = {
    "key": "gdpr_data_processing_agreement",
    "label": "GDPR Data Processing Agreement",
    "keywords": ["gdpr", "data processing", "dpa", "data protection"],
}


# --- Business-type-specific requirements -------------------------------------
BUSINESS_TYPE_REQUIREMENTS: dict[str, list[dict]] = {
    "Manufacturing": [INSURANCE_CERTIFICATE],
    "Logistics": [INSURANCE_CERTIFICATE],
    "Finance": [AUDITED_FINANCIALS],
}


# --- Country-specific requirements -------------------------------------------
# EU / EEA countries trigger a GDPR Data Processing Agreement requirement.
_EU_COUNTRIES = {
    "Germany", "France", "Italy", "Spain", "Netherlands", "Belgium",
    "Ireland", "Poland", "Sweden", "Austria", "Denmark", "Finland",
}

COUNTRY_REQUIREMENTS: dict[str, list[dict]] = {
    country: [GDPR_DPA] for country in _EU_COUNTRIES
}


def get_required_documents(
    business_type: Optional[str] = None,
    country: Optional[str] = None,
) -> list[dict]:
    """Return the list of required-document checklist entries for a vendor.

    Combines the base requirements with any business-type- and country-specific
    requirements, de-duplicated by ``key`` (first occurrence wins).
    """
    combined: list[dict] = list(BASE_REQUIRED_DOCUMENTS)

    if business_type and business_type in BUSINESS_TYPE_REQUIREMENTS:
        combined.extend(BUSINESS_TYPE_REQUIREMENTS[business_type])

    if country and country in COUNTRY_REQUIREMENTS:
        combined.extend(COUNTRY_REQUIREMENTS[country])

    seen: set[str] = set()
    deduped: list[dict] = []
    for entry in combined:
        if entry["key"] not in seen:
            seen.add(entry["key"])
            deduped.append(entry)
    return deduped
