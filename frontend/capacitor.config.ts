import type { CapacitorConfig } from "@capacitor/cli";

// Dev builds talk to the laptop backend over plain http on the LAN, so cleartext/mixed content is allowed.
// For a release build (https backend), run with CAP_RELEASE=1 so these are switched off.
const dev = process.env.CAP_RELEASE !== "1";

const config: CapacitorConfig = {
  appId: "in.biomantra.app",
  appName: "Bio Mantra",
  webDir: "dist",
  server: dev ? { androidScheme: "http", cleartext: true } : { androidScheme: "https" },
  android: { allowMixedContent: dev },
};

export default config;
