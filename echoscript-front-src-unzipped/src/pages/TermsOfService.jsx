// src/pages/TermsOfService.jsx
import React from "react";

export default function TermsOfService() {
  const effective = new Date().toLocaleDateString();

  return (
    <div className="max-w-3xl mx-auto px-6 py-12 text-white">
      <h1 className="text-3xl font-bold text-teal-400 mb-2">Terms of Service</h1>
      <p className="text-sm text-zinc-400 mb-8">Effective Date: {effective}</p>

      <p className="text-zinc-200 mb-6">
        These Terms of Service (“Terms”) govern your use of EchoScript.AI (“EchoScript,” “we,” “our,” “us”)
        websites, dashboards, and services (collectively, the “Services”). By accessing or using the Services,
        you agree to these Terms.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">1) Accounts & Eligibility</h2>
      <ul className="list-disc pl-6 text-zinc-200 space-y-2">
        <li>You must be at least 13 years old (or the minimum age in your jurisdiction).</li>
        <li>You are responsible for all activity that occurs under your account and for keeping credentials secure.</li>
        <li>Provide accurate information and promptly update changes.</li>
      </ul>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">2) Acceptable Use</h2>
      <ul className="list-disc pl-6 text-zinc-200 space-y-2">
        <li>No illegal, infringing, or harmful content; no harassment, spam, or malware.</li>
        <li>Do not reverse engineer, scrape, overload, or circumvent security or usage limits.</li>
        <li>You must have the rights/permissions to upload any content you submit to the Services.</li>
      </ul>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">3) Your Content & AI Outputs</h2>
      <p className="text-zinc-200 mb-4">
        You retain ownership of content you upload (audio/video/text) and grant us a limited license to
        process it solely to provide the Services (e.g., transcription, summaries). AI-generated outputs
        may contain inaccuracies. You are responsible for reviewing outputs and any decisions made based on them.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">4) Payments & Subscriptions</h2>
      <p className="text-zinc-200 mb-4">
        Paid plans, add-ons, and usage are billed according to the pricing shown at checkout. Payments are
        processed by third-party providers such as Stripe. We do not store full card numbers on our servers.
        By purchasing, you authorize charges for the selected plan and any applicable taxes. Unless stated
        otherwise, subscriptions renew automatically until canceled in your account settings (or by contacting support).
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">5) Refunds</h2>
      <p className="text-zinc-200 mb-4">
        Except where required by law or explicitly stated, fees are non-refundable. If you believe you were
        charged in error, contact support promptly so we can investigate.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">6) Privacy</h2>
      <p className="text-zinc-200 mb-4">
        Your use of the Services is also governed by our Privacy Policy. Please review it to understand how
        we collect, use, and safeguard information, including payments handled by Stripe.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">7) Availability & Modifications</h2>
      <p className="text-zinc-200 mb-4">
        We may modify, suspend, or discontinue features or the Services at any time, with or without notice.
        We are not liable for any unavailability, delay, or failure caused by circumstances beyond our reasonable control.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">8) Disclaimers</h2>
      <p className="text-zinc-200 mb-4">
        THE SERVICES (INCLUDING AI-GENERATED OUTPUTS) ARE PROVIDED “AS IS” AND “AS AVAILABLE” WITHOUT WARRANTIES
        OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING ACCURACY, RELIABILITY, NON-INFRINGEMENT, OR FITNESS FOR A
        PARTICULAR PURPOSE. YOU ASSUME ALL RISK FOR YOUR USE OF THE SERVICES AND OUTPUTS.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">9) Limitation of Liability</h2>
      <p className="text-zinc-200 mb-4">
        TO THE MAXIMUM EXTENT PERMITTED BY LAW, ECHOSCRIPT AND ITS AFFILIATES, OFFICERS, EMPLOYEES, AND
        LICENSORS SHALL NOT BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR
        PUNITIVE DAMAGES; LOSS OF PROFITS, DATA, OR GOODWILL; OR SERVICE INTERRUPTION, EVEN IF ADVISED
        OF THE POSSIBILITY. OUR TOTAL LIABILITY FOR ANY CLAIMS ARISING OUT OF OR RELATING TO THE SERVICES
        SHALL NOT EXCEED THE AMOUNT YOU PAID TO US FOR THE SERVICES IN THE 3 MONTHS PRECEDING THE EVENT
        GIVING RISE TO THE CLAIM.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">10) Indemnification</h2>
      <p className="text-zinc-200 mb-4">
        You agree to defend, indemnify, and hold harmless EchoScript from any claims, damages, liabilities,
        costs, and expenses (including reasonable attorneys’ fees) arising from your use of the Services,
        your content, or your violation of these Terms or applicable law.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">11) Termination</h2>
      <p className="text-zinc-200 mb-4">
        We may suspend or terminate access to the Services at any time for violation of these Terms, risk,
        or misuse. You may stop using the Services at any time. Sections that by their nature should survive
        termination will survive (e.g., intellectual property, disclaimers, limitations of liability, indemnity).
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">12) Governing Law; Disputes</h2>
      <p className="text-zinc-200 mb-4">
        These Terms are governed by the laws of your principal place of business for EchoScript (without regard
        to conflicts rules). Any disputes will be brought in the courts of that venue, unless otherwise required
        by applicable law. You and EchoScript consent to personal jurisdiction and venue there.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">13) Changes to Terms</h2>
      <p className="text-zinc-200 mb-4">
        We may update these Terms from time to time. The updated version will be posted with a new “Effective Date.”
        Your continued use after changes constitutes acceptance.
      </p>

      <h2 className="text-xl font-semibold text-teal-300 mt-8 mb-2">14) Contact</h2>
      <p className="text-zinc-200">
        Questions about these Terms? Email{" "}
        <a href="mailto:support@echoscript.ai" className="text-teal-300 underline">
          support@echoscript.ai
        </a>.
      </p>

      <p className="text-xs text-zinc-500 mt-8">
        <b>Note:</b> These Terms are general information, not legal advice. Consider having counsel review
        for your specific business and jurisdiction.
      </p>
    </div>
  );
}
