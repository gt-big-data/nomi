import { router } from "expo-router";
import { useState } from "react";

import { useDraft } from "@/components/onboarding/DraftProvider";
import { MultiSelectChips } from "@/components/onboarding/MultiSelectChips";
import { QuestionScreen } from "@/components/onboarding/QuestionScreen";
import { conditionText } from "@/storage/profile";

/** Question 4: the 12 health conditions the scoring model uses, in plain words. */
export default function Conditions() {
  const { draft, update } = useDraft();
  const [picked, setPicked] = useState(draft.conditions);

  const next = () => {
    update({ conditions: picked });
    skip();
  };
  const skip = () => router.push("/onboarding/medicines");

  return (
    <QuestionScreen
      step={4}
      title="Any of these health conditions?"
      subtitle="Pick all that apply. They change how some ingredients are scored."
      // With nothing picked, the button is the "none of these" answer.
      nextLabel={picked.length ? "Next" : "None of these"}
      onNext={next}
      onSkip={skip}
    >
      <MultiSelectChips options={conditionText} picked={picked} onChange={setPicked} />
    </QuestionScreen>
  );
}
