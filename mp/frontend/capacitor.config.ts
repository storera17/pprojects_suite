import type { CapacitorConfig } from '@capacitor/cli';

// Native iPhone packaging. `npm run ios:add && npm run ios:sync && npm run ios:open`
// produces a real Xcode project wrapping the offline dist/ bundle.
const config: CapacitorConfig = {
  appId: 'com.momentumprodigy.learn',
  appName: 'MomentumProdigy',
  webDir: 'dist',
  ios: {
    contentInset: 'always',
    backgroundColor: '#04101c',
  },
};

export default config;