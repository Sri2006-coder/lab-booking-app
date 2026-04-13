import React from 'react';
import { WebView } from 'react-native-webview';

export default function App() {
  return (
    <WebView
      source={{ uri: 'http://10.250.79.39:5000' }}
      style={{ flex: 1 }}
    />
  );
}
