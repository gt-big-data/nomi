import Ban from "lucide-react-native/icons/ban";
import ChevronLeft from "lucide-react-native/icons/chevron-left";
import ChevronRight from "lucide-react-native/icons/chevron-right";
import CircleCheck from "lucide-react-native/icons/circle-check";
import CircleMinus from "lucide-react-native/icons/circle-minus";
import FileText from "lucide-react-native/icons/file-text";
import Gem from "lucide-react-native/icons/gem";
import Info from "lucide-react-native/icons/info";
import OctagonAlert from "lucide-react-native/icons/octagon-alert";
import ShieldCheck from "lucide-react-native/icons/shield-check";
import TriangleAlert from "lucide-react-native/icons/triangle-alert";
import User from "lucide-react-native/icons/user";

import { iconSize, type IconSize } from "@/theme";

/**
 * The Lucide icons the app uses (lucide.dev), named by what they mean in Nomi.
 */
const icons = {
  checkCircle: CircleCheck, // Low risk, "All clear" banner
  triangleAlert: TriangleAlert, // Use with caution, warning banners
  octagonAlert: OctagonAlert, // High risk, danger banners
  stop: Ban, // Do not use
  dash: CircleMinus, // Not scored
  info: Info, // Info banner
  doc: FileText, // Citation chip, welcome: every warning has a source
  chevron: ChevronRight, // Rows and banners you can tap
  back: ChevronLeft, // Back button in onboarding
  gem: Gem, // Premium
  person: User, // Welcome: scores for who it's for
  shield: ShieldCheck, // Welcome: privacy promise
} as const;

export type IconName = keyof typeof icons;

type IconProps = {
  /** Which icon, by what it means in Nomi, e.g. "chevron" or "info". The list is `icons` above. */
  name: IconName;
  /** Where it's used, which sets its size and line thickness (`iconSize` in tokens.ts). */
  size: IconSize;
  /** A theme color, e.g. `colors.brand.text`. */
  color: string;
  /** Grows it with large text: pass `useIconScale()` when it sits next to text. Defaults to 1. */
  scale?: number;
};

/**
 * Decorative icon. It has no screen-reader label of its own: the text or component around it
 * gives the meaning, so the meaning never depends on the icon alone.
 *
 * Mostly used inside the core components. Use it directly only when building a new component,
 * and give that component the screen-reader label.
 *
 * @example
 * ```tsx
 * const { colors } = useTheme();
 * const iconScale = useIconScale(); // grows with large text
 * <Icon name="chevron" size="chevron" scale={iconScale} color={colors.text.secondary} />
 * ```
 */
export function Icon({ name, size, color, scale = 1 }: IconProps) {
  const LucideIcon = icons[name];
  const points = iconSize[size].size * scale;
  // Lucide draws on a 24×24 grid and scales the line with the icon, so convert the Figma line
  // width to grid units once; it stays right at any scale.
  const strokeWidth = (iconSize[size].strokeWidth * 24) / iconSize[size].size;
  return <LucideIcon size={points} color={color} strokeWidth={strokeWidth} />;
}
