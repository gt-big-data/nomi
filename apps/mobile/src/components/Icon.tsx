import Ban from "lucide-react-native/icons/ban";
import ChevronRight from "lucide-react-native/icons/chevron-right";
import CircleCheck from "lucide-react-native/icons/circle-check";
import CircleMinus from "lucide-react-native/icons/circle-minus";
import FileText from "lucide-react-native/icons/file-text";
import Gem from "lucide-react-native/icons/gem";
import Info from "lucide-react-native/icons/info";
import OctagonAlert from "lucide-react-native/icons/octagon-alert";
import TriangleAlert from "lucide-react-native/icons/triangle-alert";

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
  doc: FileText, // Citation chip
  chevron: ChevronRight, // Rows and banners you can tap
  gem: Gem, // Premium
} as const;

export type IconName = keyof typeof icons;

type IconProps = {
  /** Which icon, by what it means in Nomi, e.g. "chevron" or "info". The list is `icons` above. */
  name: IconName;
  /** Width and height in points. */
  size: number;
  /** A theme color, e.g. `colors.brand.text`. */
  color: string;
  /** Line thickness in points at this size (Figma's stroke weight). Converted to Lucide's units for you. */
  strokeWidth: number;
};

/**
 * Decorative icon. It has no screen-reader label of its own: the text or component around it
 * gives the meaning, so the meaning never depends on the icon alone.
 *
 * Mostly used inside the core components. Use it directly only when building a new component,
 * and give that component the screen-reader label.
 *
 * Every prop is required: there are no defaults. Don't pick new numbers; use a pair from this
 * list, which is every size the Nomi Library uses (size / strokeWidth, in points):
 * - 14 / 1.17: citation chip document icon
 * - 14 / 1.4: tier label icon
 * - 18 / 1.5: chevron on tappable rows and banners
 * - 18 / 2: Premium gem on buttons
 * - 22 / 1.83: alert banner icon
 * - 22 / 2: "Do not use" icon in the small score dot
 * - 72 / 6: "Do not use" icon in the large score ring
 * If a design needs a size that isn't here, add it to the Figma library first, then to this list.
 *
 * When the icon sits next to text, multiply both numbers by `useIconScale()` so it grows with
 * large text settings.
 *
 * @example
 * ```tsx
 * const { colors } = useTheme();
 * const k = useIconScale(); // grows with large text
 * <Icon name="chevron" size={18 * k} color={colors.text.secondary} strokeWidth={1.5 * k} />
 * ```
 */
export function Icon({ name, size, color, strokeWidth }: IconProps) {
  const LucideIcon = icons[name];
  // Lucide draws on a 24×24 grid, so turn the line width in points into grid units.
  return <LucideIcon size={size} color={color} strokeWidth={(strokeWidth * 24) / size} />;
}
