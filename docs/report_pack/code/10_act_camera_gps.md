# React Act screen: live camera + GPS + submit

Source: `frontend/src/pages/Act.tsx` (29 lines in total), copied unchanged.

Lines 20–24:

```tsx
/** Open the camera (camera only, no gallery) and return the photo as a Blob. */
async function takePhoto(): Promise<Blob> {
  const photo = await Camera.getPhoto({ source: CameraSource.Camera, resultType: CameraResultType.Uri, quality: 80 });
  return (await fetch(photo.webPath!)).blob();
}
```

Lines 57–80:

```tsx
  /** Take the (after) photo, read GPS, and POST everything to /actions. */
  const captureAndSubmit = async () => {
    if (!type) return;
    setError("");
    try {
      const photo = await takePhoto();
      setBusy(hi ? "स्थान लिया जा रहा है…" : "Getting location…");
      const pos = await Geolocation.getCurrentPosition({ enableHighAccuracy: true });
      const form = new FormData();
      form.append("user_id", String(user.id));
      form.append("action_type", type);
      form.append("lat", String(pos.coords.latitude));
      form.append("lon", String(pos.coords.longitude));
      form.append("client_time", new Date().toISOString());
      form.append("photo", photo, "photo.jpg");
      if (type === "cleanup" && before) form.append("before_photo", before, "before.jpg");
      setBusy(hi ? "जाँच हो रही है…" : "Checking photo…");
      setResult(await api.submitAction(form));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  };
```
