import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.laundryai.staff",
  appName: "LaundryAI Staff",
  webDir: "dist",
  // When building for production, remove the `server` block below.
  // Keep it during local dev only (hot-reload from dev server).
  server: {
    url: "https://staff.dryclean.synmodel.com",
    cleartext: false,
    androidScheme: "https",
  },
  ios: {
    // Allows camera and photo library access
    contentInset: "automatic",
  },
  android: {
    // Use hardware back button
    allowMixedContent: false,
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1500,
      launchAutoHide: true,
      backgroundColor: "#6366f1",
      androidSplashResourceName: "splash",
      showSpinner: false,
    },
    StatusBar: {
      style: "LIGHT",
      backgroundColor: "#6366f1",
      overlaysWebView: false,
    },
    Camera: {
      // iOS: prompt text shown when requesting camera permission
      iosCameraUsageDescription: "Capture garment photos for inspection",
      // iOS: prompt text shown when requesting photo library permission
      iosPhotoLibraryUsageDescription: "Select garment photos from your photo library",
      // iOS: prompt text for saving photos (not used, but required by Apple)
      iosPhotoLibraryAddUsageDescription: "Save annotated inspection photos",
    },
  },
};

export default config;
