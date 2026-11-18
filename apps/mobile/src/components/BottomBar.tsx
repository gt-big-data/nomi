import type { ReactNode } from "react";
import { StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Defs, LinearGradient, Rect, Stop } from "react-native-svg";

import { useTheme } from "@/theme";

/** How tall the fade above the buttons is, so content scrolling under them softens out. */
const FADE = 32;

/** The space a scroll view should leave at its end for a BottomBar with one row of buttons. */
export function useBottomBarSpace(): number {
  const insets = useSafeAreaInsets();
  return insets.bottom + 12 + 52 + 32;
}

/**
 * Actions pinned to the bottom of a screen, above the home indicator, with the page color fading
 * in behind them.
 *
 * @example
 * ```tsx
 * <BottomBar>
 *   <Button label="Scan again" onPress={scanAgain} />
 * </BottomBar>
 * ```
 */
export function BottomBar({ children, row = false }: { children: ReactNode; row?: boolean }) {
  const { colors, space } = useTheme();
  const insets = useSafeAreaInsets();
  return (
    <View pointerEvents="box-none" style={styles.wrap}>
      <Svg width="100%" height={FADE} pointerEvents="none">
        <Defs>
          <LinearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor={colors.bg.canvas} stopOpacity="0" />
            <Stop offset="1" stopColor={colors.bg.canvas} stopOpacity="1" />
          </LinearGradient>
        </Defs>
        <Rect width="100%" height={FADE} fill="url(#fade)" />
      </Svg>
      <View
        style={[
          row ? styles.row : styles.column,
          {
            backgroundColor: colors.bg.canvas,
            paddingHorizontal: space[20],
            paddingBottom: insets.bottom + space[12],
            gap: row ? 10 : space[8],
          },
        ]}
      >
        {children}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { position: "absolute", left: 0, right: 0, bottom: 0 },
  row: { flexDirection: "row", alignItems: "stretch" },
  column: { alignItems: "stretch" },
});
