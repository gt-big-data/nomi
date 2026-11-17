import { router } from "expo-router";
import { useState } from "react";
import { View } from "react-native";

import { OptionCard } from "@/components";
import { useDraft } from "@/components/onboarding/DraftProvider";
import { QuestionScreen } from "@/components/onboarding/QuestionScreen";
import { withRelation } from "@/lib/onboarding";
import { defaultProfile, type Relation, relationText } from "@/storage/profile";
import { useTheme } from "@/theme";

const descriptions: Record<Relation, string> = {
  self: "Scores for your age, health and medicines",
  someone_else: "Check medicines for someone you look after",
  child: "Adds child and under-2 warnings",
};
const relations = Object.keys(relationText) as Relation[];

const TITLE = "Who are you scanning for?";

/** Question 1: who the profile is for. */
export default function Who() {
  const { space } = useTheme();
  const { draft, update } = useDraft();
  const [picked, setPicked] = useState(draft.relation);

  const answer = (relation: Relation) => {
    update(withRelation(draft, relation));
    router.push("/onboarding/age");
  };

  return (
    <QuestionScreen
      question="who"
      title={TITLE}
      subtitle="Medicines are scored for the person who will take them."
      onNext={() => answer(picked)}
      onSkip={() => answer(defaultProfile.relation)}
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
