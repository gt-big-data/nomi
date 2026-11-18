import * as Haptics from "expo-haptics";
import { Redirect, router, Stack, useFocusEffect } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  AppState,
  Linking,
  type StyleProp,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
  type ViewStyle,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Camera, useCameraDevice, useCameraPermission } from "react-native-vision-camera";
import {
  type BarcodeScannerOutputOptions,
  useBarcodeScannerOutput,
} from "react-native-vision-camera-barcode-scanner";

import { Button, GlassButton, GlassSurface } from "@/components";
import { Tappable } from "@/components/Tappable";
import { ndcCandidates } from "@/lib/barcode";
import { openDataset } from "@/lib/dataset";
import { DEMO_PROFILES, useScoredFor } from "@/lib/demoProfiles";
import { useSavedProfile } from "@/storage/activeProfile";
import { personaText } from "@/storage/profile";
import { opacity, useTheme } from "@/theme";

/** The scan frame's width over its height, about a UPC-A barcode with its digits. */
const FRAME_ASPECT = 1.6;
/** The widest the scan frame gets, in points, so it stays barcode-sized on a tablet. */
const FRAME_MAX_WIDTH = 320;

/** How long the same barcode is ignored after coming back to the camera. */
const SAME_BARCODE_MS = 2000;

export default function Scanner() {
  const { hasPermission, canRequestPermission, requestPermission } = useCameraPermission();
  const { colors, space, text } = useTheme();
  const insets = useSafeAreaInsets();
  const profile = useSavedProfile();
  // A ref, not state: the camera fires many times per second, and a ref changes instantly,
  // so a second frame can't open a second result screen.
  const scanned = useRef(false);
  // The barcode just shown and when scanning came back: Back from its result would otherwise
  // reopen it at once, since it is usually still in front of the camera.
  const last = useRef<{ value: string; since: number }>(undefined);
  const [appActive, setAppActive] = useState(AppState.currentState === "active");

  // Turn the camera off while the app is in the background.
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (state) =>
      setAppActive(state === "active"),
    );
    return () => subscription.remove();
  }, []);

  // Open the dataset at launch, so the first scan doesn't wait for it.
  useEffect(() => {
    openDataset().catch((error) => console.error("Dataset error:", error));
  }, []);

  // Runs each time this screen comes back into view, e.g. after Back from a result.
  // Unlocks scanning and turns the camera back on; turns it off when another screen covers it.
  const [focused, setFocused] = useState(true);
  useFocusEffect(
    useCallback(() => {
      scanned.current = false;
      if (last.current) last.current.since = Date.now();
      setFocused(true);
      return () => setFocused(false);
    }, []),
  );

  // First launch: nobody to score for yet.
  if (profile === null) return <Redirect href="/onboarding" />;

  if (!hasPermission) {
    return (
      <View
        style={[
          styles.center,
          { backgroundColor: colors.bg.canvas, padding: space[24], gap: space[16] },
        ]}
      >
        <Stack.Screen options={SCREEN} />
        <Text style={[text("body"), styles.message, { color: colors.text.primary }]}>
          Nomi needs the camera to scan barcodes.
        </Text>
        {canRequestPermission ? (
          <Button label="Allow camera" onPress={requestPermission} />
        ) : (
          // Once the user has said no, the system won't ask again; only Settings can change it.
          <Button label="Open Settings" onPress={() => Linking.openSettings()} />
        )}
        {/* Without the camera (or on the iOS Simulator, which has none) you can still type it. */}
        <Button
          type="secondary"
          label="Type a barcode instead"
          onPress={() => router.push("/enter")}
        />
        <Button type="ghost" label="Profile" onPress={openProfile} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.bg.camera }]}>
      <Stack.Screen options={SCREEN} />
      <BarcodeCamera
        style={StyleSheet.absoluteFill}
        isActive={appActive && focused}
        barcodeFormats={["upc-a", "ean-13"]}
        onBarcodeScanned={(barcodes) => {
          const value = barcodes[0]?.rawValue;
          if (scanned.current || !value) {
            return;
          }
          if (value === last.current?.value && Date.now() - last.current.since < SAME_BARCODE_MS) {
            return;
          }
          scanned.current = true;
          last.current = { value, since: Date.now() };
          Haptics.notificationAsync(
            ndcCandidates(value).status === "ok"
              ? Haptics.NotificationFeedbackType.Success
              : Haptics.NotificationFeedbackType.Warning,
          );
          router.push({ pathname: "/result", params: { barcode: value } });
        }}
        onError={(error) => console.error("Scanner error:", error)}
      />
      <ScanFrame />
      <View
        style={[
          styles.topBar,
          { top: insets.top + space[8], left: space[16], right: space[16], gap: space[8] },
        ]}
      >
        <GlassButton
          dark
          iconOnly
          icon="home"
          label="Home"
          hint="Shows what you’ve scanned"
          onPress={openHome}
        />
        <ScoringFor />
        <GlassButton
          dark
          iconOnly
          icon="person"
          label="Profile"
          hint="Shows who scores are for"
          onPress={openProfile}
        />
      </View>
      <View style={[styles.bottomBar, { bottom: insets.bottom + space[24] }]}>
        <GlassButton
          dark
          icon="keyboard"
          label="Type a barcode"
          onPress={() => router.push("/enter")}
        />
      </View>
    </View>
  );
}

/** Who the next score is for, between the top buttons. Opens the profile. */
function ScoringFor() {
  const saved = useSavedProfile();
  const scoredFor = useScoredFor();
  const { space, text } = useTheme();
  const demo = DEMO_PROFILES.find((profile) => profile.id === scoredFor);
  const who = demo
    ? demo.label
    : saved?.relation === "child"
      ? "your child"
      : saved?.relation === "someone_else"
        ? "them"
        : "you";
  const detail = demo ? demo.description : saved ? personaText[saved.persona] : "";
  return (
    <Tappable
      onPress={openProfile}
      accessibilityLabel={`Scoring for ${who}, ${detail}`}
      accessibilityHint="Shows who scores are for"
      style={styles.scoringFor}
    >
      <GlassSurface dark style={[styles.scoringInner, { paddingHorizontal: space[16] }]}>
        <Text numberOfLines={1} style={[text("caption"), styles.white]}>
          Scoring for {who}
        </Text>
        <Text numberOfLines={1} style={[text("footnote"), styles.whiteSoft]}>
          {detail}
        </Text>
      </GlassSurface>
    </Tappable>
  );
}

function openHome() {
  router.push("/cabinet");
}

function openProfile() {
  router.push("/profile");
}

/** How long each corner bracket's arms are, and how thick. */
const CORNER = 28;
const CORNER_WIDTH = 4;

/**
 * Four corner brackets around a barcode-sized window, the picture around it dimmed, and a hint
 * under it. Only a guide: the scanner reads barcodes anywhere in the picture.
 */
function ScanFrame() {
  const { colors, space, text } = useTheme();
  const { width } = useWindowDimensions();
  const frameWidth = Math.min(width - 2 * space[48], FRAME_MAX_WIDTH);
  const frameHeight = frameWidth / FRAME_ASPECT;
  const dim = [styles.fill, { backgroundColor: colors.bg.camera, opacity: opacity.scrim }];
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      <View style={dim} />
      <View style={styles.row}>
        <View style={dim} />
        <View style={{ width: frameWidth, height: frameHeight }}>
          {(["tl", "tr", "bl", "br"] as const).map((corner) => (
            <View
              key={corner}
              style={[
                styles.corner,
                {
                  width: CORNER,
                  height: CORNER,
                  borderTopWidth: corner[0] === "t" ? CORNER_WIDTH : 0,
                  borderBottomWidth: corner[0] === "b" ? CORNER_WIDTH : 0,
                  borderLeftWidth: corner[1] === "l" ? CORNER_WIDTH : 0,
                  borderRightWidth: corner[1] === "r" ? CORNER_WIDTH : 0,
                  borderTopLeftRadius: corner === "tl" ? 14 : 0,
                  borderTopRightRadius: corner === "tr" ? 14 : 0,
                  borderBottomLeftRadius: corner === "bl" ? 14 : 0,
                  borderBottomRightRadius: corner === "br" ? 14 : 0,
                  top: corner[0] === "t" ? 0 : undefined,
                  bottom: corner[0] === "b" ? 0 : undefined,
                  left: corner[1] === "l" ? 0 : undefined,
                  right: corner[1] === "r" ? 0 : undefined,
                },
              ]}
            />
          ))}
        </View>
        <View style={dim} />
      </View>
      <View style={[styles.fill, styles.hint]}>
        <View style={[StyleSheet.absoluteFill, dim]} />
        <Text style={[text("headline"), styles.white, { marginTop: space[32] }]}>
          Point at the barcode
        </Text>
        <Text style={[text("subhead"), styles.whiteSoft, { marginTop: space[4] }]}>
          On the back or bottom of the box
        </Text>
      </View>
    </View>
  );
}

// No header over the camera; "Scan" is what the back button says on the next screen.
const SCREEN = { title: "Scan", headerShown: false };

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, alignItems: "stretch", justifyContent: "center" },
  message: { textAlign: "center" },
  fill: { flex: 1 },
  row: { flexDirection: "row" },
  hint: { alignItems: "center" },
  topBar: { position: "absolute", flexDirection: "row", alignItems: "center" },
  bottomBar: { position: "absolute", alignSelf: "center" },
  corner: { position: "absolute", borderColor: "#FFFFFF" },
  white: { color: "#FFFFFF" },
  whiteSoft: { color: "rgba(255,255,255,0.75)" },
  scoringFor: { flex: 1, minHeight: 44, borderRadius: 22 },
  scoringInner: {
    minHeight: 44,
    borderRadius: 22,
    justifyContent: "center",
    alignItems: "center",
    overflow: "hidden",
  },
});

/**
 * The back camera with barcode scanning. The library's own CodeScanner throws when the camera
 * list hasn't loaded on the first render, which crashed the app at launch; this waits instead
 * and shows the plain background until the camera is ready.
 */
function BarcodeCamera({
  isActive,
  style,
  ...options
}: BarcodeScannerOutputOptions & { isActive: boolean; style: StyleProp<ViewStyle> }) {
  const device = useCameraDevice("back");
  const output = useBarcodeScannerOutput(options);
  if (device == null) return null;
  return (
    <Camera
      style={style}
      isActive={isActive}
      device={device}
      outputs={[output]}
      onError={options.onError}
    />
  );
}
