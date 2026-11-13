import { router } from "expo-router";
import { useState } from "react";
import { View } from "react-native";

import { OptionCard } from "@/components";
import { useDraft } from "@/components/onboarding/DraftProvider";
import { QuestionScreen } from "@/components/onboarding/QuestionScreen";
import { type Relation, relationText } from "@/storage/profile";
import { useTheme } from "@/theme";

const descriptions: Record<Relation, string> = {
  self: "Scores for your age, health and medicines",
  someone_else: "Check medicines for someone you look after",
  child: "Adds child dosing and under-2 warnings",
};
const relations = Object.keys(relationText) as Relation[];

const TITLE = "Who are you scanning for?";

/** Question 1: who the profile is for. */
export default function Who() {
  const { space } = useTheme();
  const { draft, update } = useDraft();
  const [picked, setPicked] = useState(draft.relation);

  const next = () => {
    update({ relation: picked });
    router.push("/onboarding/age");
  };
  const skip = () => router.push("/onboarding/age");

  return (
    <QuestionScreen
      step={1}
      title={TITLE}
      subtitle="You can add more people later."
      onNext={next}
      onSkip={skip}
    >
      <View accessibilityRole="radiogroup" accessibilityLabel={TITLE} style={{ gap: space[12] }}>
        {relations.map((r) => (
          <OptionCard
            key={r}
            label={relationText[r]}
            description={descriptions[r]}
            selected={picked === r}
            onPress={() => setPicked(r)}
          />
        ))}
      </View>
    </QuestionScreen>
  );
}
