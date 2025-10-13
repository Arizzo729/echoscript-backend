// src/pages/PrivacyPolicy.jsx
import React from "react";

export default function PrivacyPolicy() {
  const effective = new Date().toLocaleDateString();

  return (
    <div className="max-w-3xl mx-auto px-6 py-12 text-white">
      <h1 className="text-3xl font-bold text-teal-400 mb-2">Privacy Policy</h1>
      <p className="text-sm text-zinc-400 mb-8">Effective Date: {effective}</p>

      <p className="text-zinc-200 mb-6">
        EchoScript.AI (“we,” “our,” “us”) respects your privacy. This policy explains
        what we collect, how we use it, how we share it, and your choices—especially
        regarding payments processed by Stripe.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">1) Scope</h2>
      <p className="text-zinc-200 mb-4">
        This policy covers our website, dashboard, and related services (the “Services”).
        By using the Services, you agree to this Privacy Policy.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">2) Information We Collect</h2>
      <ul className="list-disc pl-6 text-zinc-200 space-y-2">
        <li>
          <b>Account & Contact Information</b>: name, email, and any details you provide
          (e.g., support messages or forms).
        </li>
        <li>
          <b>Usage & Device Data</b>: IP address, device/browser type, pages or actions
          within the app, language, time zone, and diagnostics; used to maintain and
          improve performance and security.
        </li>
        <li>
          <b>Content You Upload</b>: audio/video files, transcripts, and derived summaries
          you choose to process with our AI features.
        </li>
        <li>
          <b>Payment Data</b>: processed by <b>Stripe</b>—we do <b>not</b> store full card
          numbers or CVV on our servers. Limited billing info (e.g., last4, brand,
          status) may be accessible via Stripe for receipts, refunds, and fraud prevention.
        </li>
        <li>
          <b>Cookies & Local Storage</b>: to keep you signed in, remember preferences, and
          enable core functionality (see “Cookies” below).
        </li>
      </ul>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">3) How We Use Information</h2>
      <ul className="list-disc pl-6 text-zinc-200 space-y-2">
        <li>Provide, operate, secure, and improve the Services.</li>
        <li>Process orders/subscriptions and deliver purchased features.</li>
        <li>Communicate with you (service updates, account notices, support).</li>
        <li>Comply with legal obligations and enforce our Terms.</li>
        <li>Detect, investigate, and prevent fraud, abuse, or security incidents.</li>
      </ul>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">4) Payments via Stripe</h2>
      <p className="text-zinc-200 mb-4">
        All payments are processed by Stripe, Inc. (“Stripe”). Your payment details are transmitted
        directly to Stripe and handled under PCI-DSS. We do not control Stripe’s practices and are
        not responsible for their services. Please review{" "}
        <a
          href="https://stripe.com/privacy"
          target="_blank"
          rel="noopener noreferrer"
          className="text-teal-300 underline"
        >
          Stripe’s Privacy Policy
        </a>{" "}
        and{" "}
        <a
          href="https://stripe.com/terms"
          target="_blank"
          rel="noopener noreferrer"
          className="text-teal-300 underline"
        >
          Terms
        </a>.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">5) Sharing of Information</h2>
      <p className="text-zinc-200 mb-2">
        We do not sell your personal data. We share information only with:
      </p>
      <ul className="list-disc pl-6 text-zinc-200 space-y-2">
        <li>
          <b>Service Providers</b> (e.g., hosting, analytics, email delivery, payments) bound by
          contracts to process data on our behalf and follow confidentiality and security obligations.
        </li>
        <li>
          <b>Legal/Compliance</b> when required by law, subpoena, or to protect rights, safety, and integrity.
        </li>
        <li>
          <b>Business Transfers</b> in connection with a merger, acquisition, or asset sale (with notice
          where required by law).
        </li>
      </ul>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">6) AI Processing & Your Content</h2>
      <p className="text-zinc-200 mb-4">
        When you upload audio/video or text, we process it to generate transcripts and summaries.
        We may use trusted third-party AI services under strict agreements. You retain ownership of
        your content. You’re responsible for having the necessary rights/permissions to upload it.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">7) Data Retention</h2>
      <p className="text-zinc-200 mb-4">
        We keep personal information only as long as needed to provide the Services, meet legal
        obligations, resolve disputes, and enforce agreements. You can request deletion (see “Your Rights”).
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">8) Security</h2>
      <p className="text-zinc-200 mb-4">
        We use reasonable administrative, technical, and physical safeguards appropriate to our
        Services. However, no method of transmission or storage is 100% secure. To the maximum
        extent permitted by law, we are not liable for unauthorized access beyond our reasonable control.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">9) Your Rights & Choices</h2>
      <ul className="list-disc pl-6 text-zinc-200 space-y-2">
        <li>
          <b>Access/Update/Delete</b>: contact us to access or delete personal information we maintain,
          subject to legal exceptions.
        </li>
        <li>
          <b>Opt-Out</b>: you can unsubscribe from non-essential emails at any time.
        </li>
        <li>
          <b>Cookies</b>: adjust browser settings to block or delete cookies (core features may require them).
        </li>
      </ul>
      <p className="text-xs text-zinc-400 mt-2">
        If you are in the EEA/UK/California or similar jurisdictions, you may have additional rights (e.g.,
        portability, restriction, objection). We will honor applicable rights requests per local law.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">10) International Data Transfers</h2>
      <p className="text-zinc-200 mb-4">
        We may process data in countries outside your own. Where required, we rely on appropriate legal
        mechanisms (e.g., standard contractual clauses) for cross-border transfers.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">11) Children’s Privacy</h2>
      <p className="text-zinc-200 mb-4">
        Our Services are not directed to children under 13 (or the minimum age in your jurisdiction).
        If you believe a child has provided personal information, contact us to request deletion.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">12) Cookies & Similar Technologies</h2>
      <p className="text-zinc-200 mb-4">
        We use cookies/local storage to keep you signed in, remember preferences, enable features, and
        help protect your account. Analytics may use cookies to understand usage patterns and improve
        performance.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">13) Changes to This Policy</h2>
      <p className="text-zinc-200 mb-4">
        We may update this policy to reflect operational, legal, or regulatory changes. We will post the
        updated version with a new “Effective Date.” Material changes may also be communicated by email
        or in-app notice.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">14) Contact</h2>
      <p className="text-zinc-200">
        Questions or requests? Email{" "}
        <a href="mailto:support@echoscript.ai" className="text-teal-300 underline">
          support@echoscript.ai
        </a>
        .
      </p>

      <p className="text-xs text-zinc-500 mt-8">
        <b>Note:</b> This template is provided for general informational purposes and does not constitute legal advice.
        Consider having it reviewed by a qualified attorney for your specific use case and jurisdiction.
      </p>
    </div>
  );
}
