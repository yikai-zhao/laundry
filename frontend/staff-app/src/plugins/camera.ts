/**
 * Camera abstraction layer.
 *
 * On native iOS / Android (Capacitor) the @capacitor/camera plugin is used
 * so the app gets native permission prompts and a full-screen camera viewfinder.
 *
 * On web / PWA the functions return null and the caller falls back to
 * <input type="file" capture="environment">.
 */

function isNativePlatform(): boolean {
  if (typeof window === "undefined") return false;
  const origin = window.location.origin;
  return (
    origin === "capacitor://localhost" ||
    origin.startsWith("ionic://") ||
    origin.startsWith("file://") ||
    origin === "null"
  );
}

export { isNativePlatform };

/**
 * Open the native camera and return the captured image as a File.
 * Returns null on web (caller should trigger <input capture="environment">).
 */
export async function capturePhotoNative(): Promise<File | null> {
  if (!isNativePlatform()) return null;
  try {
    const { Camera, CameraResultType, CameraSource } = await import("@capacitor/camera");
    const photo = await Camera.getPhoto({
      quality: 90,
      allowEditing: false,
      resultType: CameraResultType.DataUrl,
      source: CameraSource.Camera,
      correctOrientation: true,
      width: 2048,
      height: 2048,
    });
    if (!photo.dataUrl) return null;
    const res = await fetch(photo.dataUrl);
    const blob = await res.blob();
    return new File([blob], `photo_${Date.now()}.jpg`, { type: "image/jpeg" });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    if (msg.includes("cancelled") || msg.includes("canceled") || msg.includes("User cancelled")) {
      return null;
    }
    console.error("[Camera] Native capture failed:", e);
    return null;
  }
}

/**
 * Open native photo library and return selected images as File[].
 * Returns null on web (caller should trigger <input type="file" multiple>).
 */
export async function pickPhotosNative(): Promise<File[] | null> {
  if (!isNativePlatform()) return null;
  try {
    const { Camera } = await import("@capacitor/camera");
    const images = await Camera.pickImages({ quality: 90, limit: 10 });
    const files: File[] = [];
    for (const photo of images.photos) {
      const src = (photo as { dataUrl?: string; webPath?: string }).dataUrl || photo.webPath;
      if (!src) continue;
      const res = await fetch(src);
      const blob = await res.blob();
      files.push(new File([blob], `photo_${Date.now()}.jpg`, { type: "image/jpeg" }));
    }
    return files.length > 0 ? files : null;
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    if (msg.includes("cancelled") || msg.includes("canceled") || msg.includes("User cancelled")) {
      return null;
    }
    console.error("[Camera] Native gallery failed:", e);
    return null;
  }
}
