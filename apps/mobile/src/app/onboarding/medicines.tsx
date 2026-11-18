import { router } from "expo-router";
import { useState } from "react";

import { askAbout, capitalize, toProfile } from "@/lib/onboarding";
import { useDraft } from "@/components/onboarding/DraftProvider";
import { MultiSelectChips } from "@/components/onboarding/MultiSelectChips";
import { QuestionScreen } from "@/components/onboarding/QuestionScreen";
import { saveProfile } from "@/storage/activeProfile";
import { type MedicationType, medicationTypeText } from "@/storage/profile";

/**
 * Question 5: the 8 types of medicine that change scores. Only the type, since that's all the
 * model needs; exact medicines can go in the Cabinet later.
 */
export default function Medicines() {
  const { draft, update } = useDraft();
  const [picked, setPicked] = useState(draft.medicationTypes);

  const finish = (medicationTypes: MedicationType[]) => {
    update({ medicationTypes });
    saveProfile(toProfile({ ...draft, medicationTypes }));
    // Clears the questions off the stack, so Back from the done screen leaves onboarding.
    router.dismissAll();
    router.replace("/onboarding/done");
  };

  return (
    <QuestionScreen
      question="medicines"
      title={`${capitalize(askAbout(draft.relation).do)} take any of these?`}
      subtitle="Only the type matters, not the exact medicine. Nothing leaves your phone."
      nextLabel={picked.length ? "Finish" : "None of these"}
      onNext={() => finish(picked)}
      onSkip={() => finish([])}
    >
      <MultiSelectChips options={medicationTypeText} picked={picked} onChange={setPicked} />
    </QuestionScreen>
  );
}
