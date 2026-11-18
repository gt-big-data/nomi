import * as Haptics from "expo-haptics";
import { Redirect, router, Stack, useFocusEffect } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { AppState, Linking, StyleSheet, Text, useWindowDimensions, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useCameraPermission } from "react-native-vision-camera";
import { CodeScanner } from "react-native-vision-camera-barcode-scanner";

import { Button, Icon, type IconName } from "@/components";
import { Tappable } from "@/components/Tappable";
import { ndcCandidates } from "@/lib/barcode";
import { openDataset } from "@/lib/dataset";
import { useSavedProfile } from "@/storage/activeProfile";
import { borderWidth, minHeight, opacity, useIconScale, useTheme } from "@/theme";

/** The scan frame's width over its height, about a UPC-A barcode with its digits. */
const FRAME_ASPECT = 1.6;
/** The widest the scan frame gets, in points, so it stays barcode-sized on a tablet. */
const FRAME_MAX_WIDTH = 320;

export default function Scanner() {
  const { hasPermission, canRequestPermission, requestPermission } = useCameraPermission();
  const { colors, space, text } = useTheme();
  const insets = useSafeAreaInsets();
  const profile = useSavedProfile();
  // A ref, not state: the camera fires many times per second, and a ref changes instantly,
  // so a second frame can't open a second result screen.
  const scanned = useRef(false);
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
    <View style={styles.container}>
      <Stack.Screen options={SCREEN} />
      <CodeScanner
        style={StyleSheet.absoluteFill}
        isActive={appActive && focused}
        barcodeFormats={["upc-a", "ean-13"]}
        onBarcodeScanned={(barcodes) => {
          const value = barcodes[0]?.rawValue;
          if (scanned.current || !value) {
            return;
          }
          scanned.current = true;
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
      <View style={[styles.topBar, { top: insets.top + space[8], right: space[16] }]}>
        <CameraButton
          icon="person"
          label="Profile"
          hint="Shows who scores are for"
          onPress={openProfile}
        />
      </View>
      <View style={[styles.bottomBar, { bottom: insets.bottom + space[24] }]}>
        <CameraButton label="Type a barcode" onPress={() => router.push("/enter")} />
      </View>
    </View>
  );
}

function openProfile() {
  router.push("/profile");
}

/**
 * A barcode-sized frame with the picture around it dimmed, and a hint under it. Only a guide:
 * the scanner reads barcodes anywhere in the picture.
 */
function ScanFrame() {
  const { colors, radius, space, text } = useTheme();
  const { width } = useWindowDimensions();
  const frameWidth = Math.min(width - 2 * space[48], FRAME_MAX_WIDTH);
  const dim = [styles.fill, { backgroundColor: colors.bg.camera, opacity: opacity.scrim }];
  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      <View style={dim} />
      <View style={styles.row}>
        <View style={dim} />
        <View
          style={{
            width: frameWidth,
            height: frameWidth / FRAME_ASPECT,
            borderRadius: radius.md,
            borderWidth: borderWidth.scanFrame,
            // White in both modes, like the camera background it sits on.
            borderColor: colors.brand.onPrimary,
          }}
        />
        <View style={dim} />
      </View>
      <View style={[styles.fill, styles.hint]}>
        <View style={[StyleSheet.absoluteFill, dim]} />
        <Text style={[text("bodyStrong"), { color: colors.brand.onPrimary, marginTop: space[16] }]}>
          Point at the barcode
        </Text>
      </View>
    </View>
  );
}

/** A pill on the camera picture, in the surface color so it reads on any picture. */
function CameraButton({
  icon,
  label,
  hint,
  onPress,
}: {
  icon?: IconName;
  label: string;
  hint?: string;
  onPress: () => void;
}) {
  const { colors, radius, space, text } = useTheme();
  const iconScale = useIconScale();
  return (
    <Tappable
      onPress={onPress}
      accessibilityLabel={label}
      accessibilityHint={hint}
      style={[
        styles.pill,
        {
          gap: space[8],
          paddingHorizontal: space[16],
          borderRadius: radius.pill,
          backgroundColor: colors.bg.surface,
        },
      ]}
    >
      {icon && <Icon name={icon} size="button" scale={iconScale} color={colors.text.primary} />}
      <Text style={[text("button"), { color: colors.text.primary }]}>{label}</Text>
    </Tappable>
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
  topBar: { position: "absolute", flexDirection: "row" },
  bottomBar: { position: "absolute", alignSelf: "center" },
  pill: { minHeight: minHeight.chip, flexDirection: "row", alignItems: "center" },
});
