// Example usage
// import PricingCard from "@/components/PricingCard";

export default function PricingSection() {
  return (
    <div className="mx-auto grid max-w-5xl grid-cols-1 gap-6 p-6 sm:grid-cols-2">
      <PricingCard
        plan="pro"
        price={9.99}
        title="Pro"
        blurb="Great for creators and students"
        highlight
      />
      <PricingCard
        plan="premium"
        price={19.99}
        title="Premium"
        blurb="For teams and power users"
        features={[
          "2,000 minutes / month",
          "Audio + video transcription",
          "Advanced diarization & smart chapters",
          "Export: TXT, DOCX, SRT, VTT, CSV",
          "Higher priority + faster queue",
        ]}
      />
    </div>
  );
}
