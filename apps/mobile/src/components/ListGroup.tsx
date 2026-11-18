import { Children, Fragment, type ReactNode } from "react";
import { type StyleProp, StyleSheet, Text, View, type ViewStyle } from "react-native";

import { useIconScale, useTheme } from "@/theme";

import { Icon } from "./Icon";
import { Tappable } from "./Tappable";

/**
 * An inset grouped list, as in iOS Settings: white, rounded, no border, with hairlines between
 * rows inset from the leading edge.
 *
 * @example
 * ```tsx
 * <ListGroup title="Why this score">
 *   <ListRow title="Stomach bleeding" subtitle="Moderate · OTC monograph" onPress={open} />
 * </ListGroup>
 * ```
 */
export function ListGroup({
  title,
  footer,
  inset = 16,
  children,
}: {
  /** Section header above the group. */
  title?: string;
  /** A note under the group. */
  footer?: string;
  /** Where the hairlines start, in points from the leading edge. */
  inset?: number;
  children: ReactNode;
}) {
  const { colors, space, text } = useTheme();
  const rows = Children.toArray(children).filter(Boolean);
  return (
    <View style={{ gap: space[8] }}>
      {title ? (
        <Text
          accessibilityRole="header"
          style={[text("titleSmall"), { color: colors.text.primary }]}
        >
          {title}
        </Text>
      ) : null}
      <View style={[styles.group, { backgroundColor: colors.bg.surface }]}>
        {rows.map((row, index) => (
          <Fragment key={index}>
            {index > 0 && (
              <View
                style={[
                  styles.separator,
                  { marginLeft: inset, backgroundColor: colors.border.separator },
                ]}
              />
            )}
            {row}
          </Fragment>
        ))}
      </View>
      {footer ? (
        <Text
          style={[text("footnote"), { color: colors.text.tertiary, paddingHorizontal: space[16] }]}
        >
          {footer}
        </Text>
      ) : null}
    </View>
  );
}

/**
 * One row in a ListGroup: an optional leading view, a title and subtitle, an optional trailing
 * view, and a chevron when it can be tapped.
 */
export function ListRow({
  title,
  subtitle,
  leading,
  trailing,
  onPress,
  accessibilityLabel,
  accessibilityHint,
  style,
}: {
  title: string;
  subtitle?: ReactNode;
  leading?: ReactNode;
  trailing?: ReactNode;
  onPress?: () => void;
  accessibilityLabel: string;
  accessibilityHint?: string;
  style?: StyleProp<ViewStyle>;
}) {
  const { colors, space, text } = useTheme();
  const iconScale = useIconScale();
  return (
    <Tappable
      onPress={onPress}
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      style={[styles.row, { gap: space[12], paddingHorizontal: space[16] }, style]}
    >
      {leading}
      <View style={[styles.words, { gap: space[2] }]}>
        <Text style={[text("headline"), { color: colors.text.primary }]}>{title}</Text>
        {typeof subtitle === "string" ? (
          <Text style={[text("footnote"), { color: colors.text.secondary }]}>{subtitle}</Text>
        ) : (
          subtitle
        )}
      </View>
      {trailing}
      {onPress && (
        <Icon name="chevron" size="chevron" scale={iconScale} color={colors.text.glyph} />
      )}
    </Tappable>
  );
}

const styles = StyleSheet.create({
  group: { borderRadius: 16, overflow: "hidden" },
  separator: { height: StyleSheet.hairlineWidth },
  row: { flexDirection: "row", alignItems: "center", minHeight: 52, paddingVertical: 12 },
  words: { flex: 1, minWidth: 0 },
});
