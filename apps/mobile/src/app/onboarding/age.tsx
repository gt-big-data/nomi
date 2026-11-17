import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";

import { OptionChip } from "@/components";
import { askAbout, asksPregnancy, startingAge } from "@/lib/onboarding";
import { useDraft } from "@/components/onboarding/DraftProvider";
import { QuestionScreen } from "@/components/onboarding/QuestionScreen";
import { type AgeGroup, ageGroupText } from "@/storage/profile";
import { useTheme } from "@/theme";

const ages = Object.keys(ageGroupText) as AgeGroup[];

/**
 * Question 2: the age group, which sets the persona. A group, not a birthday: less to store.
 * A child's age can't be skipped, since the default is an adult.
 */
export default function Age() {
  const { space } = useTheme();
  const { draft, update } = useDraft();
  const [picked, setPicked] = useState(startingAge(draft));
  const title = `How old ${askAbout(draft.relation).are}?`;

  const answer = (age: AgeGroup | null) => {
    update({ age });
    router.push(
      asksPregnancy({ ...draft, age }) ? "/onboarding/pregnancy" : "/onboarding/conditions",
    );
  };

  return (
    <QuestionScreen
      step={2}
      title={title}
      subtitle="Medicines affect children, adults and older adults differently."
      onNext={picked ? () => answer(picked) : undefined}
      onSkip={draft.relation === "child" ? undefined : () => answer(null)}
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
