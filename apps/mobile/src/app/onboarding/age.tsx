import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";

import { OptionChip } from "@/components";
import { askAbout } from "@/lib/onboarding";
import { useDraft } from "@/components/onboarding/DraftProvider";
import { QuestionScreen } from "@/components/onboarding/QuestionScreen";
import { type AgeGroup, ageGroupText } from "@/storage/profile";
import { useTheme } from "@/theme";

const ages = Object.keys(ageGroupText) as AgeGroup[];

/** Question 2: the age group, which sets the persona. A group, not a birthday: less to store. */
export default function Age() {
  const { space } = useTheme();
  const { draft, update } = useDraft();
  const [picked, setPicked] = useState(draft.age);
  const title = `How old ${askAbout(draft.relation).are}?`;

  const next = () => {
    update({ age: picked });
    router.push("/onboarding/pregnancy");
  };
  const skip = () => router.push("/onboarding/pregnancy");

  return (
    <QuestionScreen
      step={2}
      title={title}
      subtitle="Medicines affect children, adults and older adults differently."
      onNext={next}
      onSkip={skip}
    >
      <View
        accessibilityRole="radiogroup"
        accessibilityLabel={title}
        style={[styles.wrap, { gap: space[8] }]}
      >
        {ages.map((age) => (
          <OptionChip
            key={age}
            mode="single"
            label={ageGroupText[age]}
            selected={picked === age}
            onPress={() => setPicked(age)}
          />
        ))}
      </View>
    </QuestionScreen>
  );
}

const styles = StyleSheet.create({
  wrap: { flexDirection: "row", flexWrap: "wrap" },
});
