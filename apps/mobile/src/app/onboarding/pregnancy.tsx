import { router } from "expo-router";
import { useState } from "react";
import { View } from "react-native";

import { OptionCard } from "@/components";
import { askAbout, capitalize, type Pregnancy } from "@/lib/onboarding";
import { useDraft } from "@/components/onboarding/DraftProvider";
import { QuestionScreen } from "@/components/onboarding/QuestionScreen";
import { useTheme } from "@/theme";

const options: { value: Pregnancy; label: string }[] = [
  { value: "no", label: "No" },
  { value: "pregnant", label: "Pregnant" },
  { value: "breastfeeding", label: "Breastfeeding" },
  { value: "undisclosed", label: "Prefer not to say" },
];

/** Question 3: pregnant or breastfeeding replaces the age persona. */
export default function PregnancyQuestion() {
  const { space } = useTheme();
  const { draft, update } = useDraft();
  const [picked, setPicked] = useState(draft.pregnancy);
  const title = `${capitalize(askAbout(draft.relation).are)} pregnant or breastfeeding?`;

  const next = () => {
    update({ pregnancy: picked });
    router.push("/onboarding/conditions");
  };
  const skip = () => router.push("/onboarding/conditions");

  return (
    <QuestionScreen
      step={3}
      title={title}
      subtitle="If you pick one, scores use pregnancy or breastfeeding guidance instead of your age group."
      onNext={next}
      onSkip={skip}
    >
      <View accessibilityRole="radiogroup" accessibilityLabel={title} style={{ gap: space[12] }}>
        {options.map((o) => (
          <OptionCard
            key={o.value}
            label={o.label}
            selected={picked === o.value}
            onPress={() => setPicked(o.value)}
          />
        ))}
      </View>
    </QuestionScreen>
  );
}
