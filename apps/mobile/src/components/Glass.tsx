import { GlassView, isLiquidGlassAvailable } from "expo-glass-effect";
import type { ReactNode } from "react";
import { type StyleProp, StyleSheet, Text, View, type ViewStyle } from "react-native";

import { useIconScale, useTheme } from "@/theme";

import { Icon, type IconName } from "./Icon";
import { Tappable } from "./Tappable";

/** Liquid Glass needs iOS 26. Older systems get a plain translucent fill instead. */
const GLASS = isLiquidGlassAvailable();

/**
 * A glass surface for controls that float over content or the camera. Glass is only for this
 * layer: never put it on cards or lists.
 */
export function GlassSurface({
  dark = false,
  style,
  children,
}: {
  /** Over the camera picture. */
  dark?: boolean;
  style?: StyleProp<ViewStyle>;
  children?: ReactNode;
}) {
  const { scheme } = useTheme();
  if (GLASS) {
    return (
      <GlassView isInteractive colorScheme={dark ? "dark" : "auto"} style={style}>
        {children}
      </GlassView>
    );
  }
  return (
    <View
      style={[
        style,
        {
          backgroundColor:
            dark || scheme === "dark" ? "rgba(255,255,255,0.18)" : "rgba(255,255,255,0.85)",
          borderWidth: StyleSheet.hairlineWidth,
          borderColor: dark ? "rgba(255,255,255,0.35)" : "rgba(23,19,31,0.08)",
        },
      ]}
    >
      {children}
    </View>
  );
}

/** Where controls sit. 44 points is the smallest comfortable tap. */
const SIZE = 44;

/**
 * A glass button: a 44 pt circle with an icon, or a capsule with an icon and a label.
 *
 * @example
 * ```tsx
 * <GlassButton icon="home" label="Home" iconOnly onPress={openHome} />
 * <GlassButton icon="keyboard" label="Type a barcode" onPress={openEnter} dark />
 * ```
 */
export function GlassButton({
  icon,
  label,
  iconOnly = false,
  dark = false,
  tall = false,
  selected,
  hint,
  onPress,
  style,
}: {
  icon?: IconName;
  /** Shown, or only spoken when `iconOnly`. */
  label: string;
  iconOnly?: boolean;
  /** Over the camera picture: white text and icon. */
  dark?: boolean;
  /** 52 pt tall, to sit next to a primary button. */
  tall?: boolean;
  /** For a toggle: whether it is on. Screen readers say so. */
  selected?: boolean;
  hint?: string;
  onPress: () => void;
  style?: StyleProp<ViewStyle>;
}) {
  const { colors, space, text } = useTheme();
  const iconScale = useIconScale();
  const foreground = dark ? "#FFFFFF" : colors.brand.text;
  const height = tall ? 52 : SIZE;
  return (
    <Tappable
      onPress={onPress}
      accessibilityLabel={label}
      accessibilityHint={hint}
      selected={selected}
      style={[{ minWidth: SIZE, minHeight: height, borderRadius: height / 2 }, style]}
    >
      <GlassSurface
        dark={dark}
        style={[
          styles.inner,
          {
            minHeight: height,
            borderRadius: height / 2,
            gap: space[8],
            paddingHorizontal: iconOnly ? 0 : space[20],
            width: iconOnly ? SIZE : undefined,
          },
        ]}
      >
        {icon && <Icon name={icon} size="nav" scale={iconScale} color={foreground} />}
        {!iconOnly && <Text style={[text("headline"), { color: foreground }]}>{label}</Text>}
      </GlassSurface>
    </Tappable>
  );
}

const styles = StyleSheet.create({
  inner: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    overflow: "hidden",
  },
});
