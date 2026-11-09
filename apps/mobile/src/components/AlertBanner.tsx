import { StyleSheet, Text, View } from "react-native";

import { type Colors, useIconScale, useTheme } from "@/theme";

import { Icon, type IconName } from "./Icon";
import { spokenLabel, Tappable } from "./Tappable";

/**
 * How serious it is, not just that something happened:
 * - danger: Don't combine, or a High clash (e.g. two acetaminophen products)
 * - warning: a Moderate clash, or a Preliminary score
 * - info: a Low clash or a neutral note ("Ask your pharmacist")
 * - success: no interactions found
 */
export type AlertType = "danger" | "warning" | "info" | "success";

type AlertBannerProps = {
  type: AlertType;
  /** Always name what it's about, e.g. "Same ingredient as ZzzQuil". */
  title: string;
  /** One or two short lines under the title. */
  body?: string;
  /** Open the details. The chevron only shows when the banner can be tapped. */
  onPress?: () => void;
};

/** Screen readers hear this word first, so the type doesn't depend on color. */
const spoken: Record<AlertType, string> = {
  danger: "Important",
  warning: "Caution",
  info: "Note",
  success: "All clear",
};

/** Danger uses the octagon (like High risk), so it differs from warning by shape, not just color. */
const icons: Record<AlertType, IconName> = {
  danger: "octagonAlert",
  warning: "triangleAlert",
  info: "info",
  success: "checkCircle",
};

function typeColors(c: Colors, type: AlertType) {
  switch (type) {
    case "danger":
      return { background: c.tier.high.tint, accent: c.tier.high.text };
    case "warning":
      return { background: c.tier.moderate.tint, accent: c.tier.moderate.text };
    case "info":
      return { background: c.brand.tint, accent: c.brand.text };
    case "success":
      return { background: c.tier.low.tint, accent: c.tier.low.text };
  }
}

/**
 * A message whose color and icon say how serious it is. Screen readers hear the
 * severity translated from colors first ("Important", "Caution"...).
 *
 * @example
 * ```tsx
 * <AlertBanner
 *   type="danger"
 *   title="Same ingredient as ZzzQuil"
 *   body="In Mom’s cabinet · tap to see why"
 *   onPress={openInteraction}
 * />
 * <AlertBanner type="success" title="No interactions in Mom’s cabinet" body="Checked 4 medicines." />
 * ```
 */
export function AlertBanner({ type, title, body, onPress }: AlertBannerProps) {
  const { colors, radius, space, text } = useTheme();
  const c = typeColors(colors, type);
  const iconScale = useIconScale();
  const label = spokenLabel([`${spoken[type]}: ${title}`, body]);

  const box = [
    styles.box,
    { backgroundColor: c.background, borderRadius: radius.md, gap: space[12], padding: space[16] },
  ];
  const content = (
    <>
      <Icon
        name={icons[type]}
        size={22 * iconScale}
        color={c.accent}
        strokeWidth={1.83 * iconScale}
      />
      <View style={[styles.stack, { gap: space[2] }]}>
        <Text style={[text("bodyStrong"), { color: c.accent }]}>{title}</Text>
        {body ? (
          <Text style={[text("footnote"), { color: colors.text.primary }]}>{body}</Text>
        ) : null}
      </View>
      {onPress && (
        <Icon name="chevron" size={18 * iconScale} color={c.accent} strokeWidth={1.5 * iconScale} />
      )}
    </>
  );

  return (
    <Tappable onPress={onPress} accessibilityLabel={label} style={box}>
      {content}
    </Tappable>
  );
}

const styles = StyleSheet.create({
  box: { flexDirection: "row", alignItems: "flex-start", alignSelf: "stretch" },
  stack: { flex: 1 },
});
