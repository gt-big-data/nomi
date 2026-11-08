import type { ConfigContext, ExpoConfig } from "expo/config";

// Free Apple IDs can't share a bundle identifier, so each developer installing on an iPhone
// with one sets their own in NOMI_IOS_BUNDLE_ID (see README). Everything else is in app.json.
export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: config.name ?? "Nomi",
  slug: config.slug ?? "nomi",
  ios: {
    ...config.ios,
    bundleIdentifier: process.env.NOMI_IOS_BUNDLE_ID ?? config.ios?.bundleIdentifier,
  },
});
