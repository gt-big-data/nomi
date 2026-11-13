import { router } from "expo-router";
import type { ReactNode } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { minHeight, opacity, useIconScale, useTheme } from "@/theme";

import { Button } from "../Button";
import { Icon } from "../Icon";
import { Title } from "./Title";

/** How many questions onboarding has. */
export const QUESTION_COUNT = 5;

/** Thickness of the progress bars, from the design. */
const STEP_HEIGHT = 6;

type QuestionScreenProps = {
  /** Which question this is, from 1 to `QUESTION_COUNT`. */
  step: number;
  title: string;
  /** One line under the title on why it's asked. */
  subtitle: string;
  /** Saves the answer and moves on. */
  onNext: () => void;
  /** Moves on without saving, so the answer stays at its default. */
  onSkip: () => void;
  /** What Back does. Defaults to going to the previous screen. */
  onBack?: () => void;
  /** The main button's label. Defaults to "Next". */
  nextLabel?: string;
  /** The answers: OptionCards or OptionChips. */
  children: ReactNode;
};

/**
 * The frame every onboarding question shares: back, progress and Skip along the top, the
 * question, its answers, and the main button pinned to the bottom.
 *
 * @example
 * ```tsx
 * <QuestionScreen step={2} title="How old are you?" subtitle="…" onNext={next} onSkip={skip}>
 *   {chips}
 * </QuestionScreen>
 * ```
 */
export function QuestionScreen({
  step,
  title,
  subtitle,
  onNext,
  onSkip,
  onBack = () => router.back(),
  nextLabel = "Next",
  children,
}: QuestionScreenProps) {
  const { colors, radius, space, text } = useTheme();
  const insets = useSafeAreaInsets();
  const iconScale = useIconScale();
  const counter = `Question ${step} of ${QUESTION_COUNT}`;

  return (
    <View style={[styles.fill, { backgroundColor: colors.bg.surface }]}>
      <View
        style={[
          styles.topBar,
          { paddingTop: insets.top + space[8], paddingHorizontal: space[16], gap: space[12] },
        ]}
      >
        <Pressable
          onPress={onBack}
          accessibilityRole="button"
          accessibilityLabel="Back"
          hitSlop={space[8]}
          style={({ pressed }) => [styles.topButton, pressed && styles.pressed]}
        >
          <Icon name="back" size="back" scale={iconScale} color={colors.brand.text} />
        </Pressable>
        <View
          accessible
          accessibilityRole="progressbar"
          accessibilityLabel={counter}
          style={[styles.steps, { gap: space[4] }]}
        >
          {Array.from({ length: QUESTION_COUNT }, (_, i) => (
            <View
              key={i}
              style={[
                styles.step,
                {
                  borderRadius: radius.pill,
                  backgroundColor: i < step ? colors.brand.primary : colors.border.subtle,
                },
              ]}
            />
          ))}
        </View>
        <Pressable
          onPress={onSkip}
          accessibilityRole="button"
          accessibilityLabel="Skip this question"
          hitSlop={space[8]}
          style={({ pressed }) => [styles.topButton, pressed && styles.pressed]}
        >
          <Text style={[text("bodyStrong"), { color: colors.brand.text }]}>Skip</Text>
        </Pressable>
      </View>

      <ScrollView
        contentContainerStyle={{
          paddingHorizontal: space[24],
          paddingTop: space[16],
          paddingBottom: space[24],
          gap: space[12],
        }}
      >
        <Text style={[text("label"), { color: colors.brand.text }]}>{counter}</Text>
        <Title>{title}</Title>
        <Text style={[text("body"), { color: colors.text.secondary }]}>{subtitle}</Text>
        <View style={{ marginTop: space[4] }}>{children}</View>
      </ScrollView>

      <View
        style={{
          paddingHorizontal: space[16],
          paddingTop: space[12],
          paddingBottom: insets.bottom + space[16],
        }}
      >
        <Button label={nextLabel} onPress={onNext} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  topBar: { flexDirection: "row", alignItems: "center" },
  // Big enough to tap, even though the arrow and the word are small.
  topButton: { minHeight: minHeight.chip, minWidth: minHeight.chip, justifyContent: "center" },
  steps: { flex: 1, flexDirection: "row" },
  step: { flex: 1, height: STEP_HEIGHT },
  pressed: { opacity: opacity.pressed },
});
