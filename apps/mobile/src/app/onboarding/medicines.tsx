import { router } from "expo-router";
import { useState } from "react";

import { askAbout, capitalize, type Draft, toProfile } from "@/lib/onboarding";
import { useDraft } from "@/components/onboarding/DraftProvider";
import { MultiSelectChips } from "@/components/onboarding/MultiSelectChips";
import { QuestionScreen } from "@/components/onboarding/QuestionScreen";
import { medicationTypeText, saveProfile } from "@/storage/profile";

/**
 * Question 5: the 8 types of medicine that change scores. Only the type, since that's all the
 * model needs; exact medicines can go in the Cabinet later.
 */
export default function Medicines() {
  const { draft, update } = useDraft();
  const [picked, setPicked] = useState(draft.medicationTypes);

  const next = () => {
    update({ medicationTypes: picked });
    finish({ ...draft, medicationTypes: picked });
  };
  const finish = (answers: Draft) => {
    saveProfile(toProfile(answers));
    // Replace, so Back from the done screen doesn't reopen the questions.
    router.replace("/onboarding/done");
  };

  return (
    <QuestionScreen
      step={5}
      title={`${capitalize(askAbout(draft.relation).do)} take any of these?`}
      subtitle="Only the type matters, not the exact medicine. Nothing leaves your phone."
      nextLabel={picked.length ? "Finish" : "None of these"}
      onNext={next}
      onSkip={() => finish(draft)}
    >
      <MultiSelectChips options={medicationTypeText} picked={picked} onChange={setPicked} />
    </QuestionScreen>
  );
}
