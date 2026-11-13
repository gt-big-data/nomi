import { Stack } from "expo-router";

import { DraftProvider } from "@/components/onboarding/DraftProvider";

/** First run: the welcome screen, five skippable questions, then done. Nothing leaves the phone. */
export default function OnboardingLayout() {
  return (
    <DraftProvider>
      {/* Hides the app's header for the whole flow; each screen draws its own top bar. */}
      <Stack.Screen options={{ headerShown: false }} />
      <Stack screenOptions={{ headerShown: false }} />
    </DraftProvider>
  );
}
