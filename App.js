<<<<<<< HEAD
import React, { useState, useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import { WebView } from 'react-native-webview';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export default function App() {
  const [expoPushToken, setExpoPushToken] = useState('');
  const webViewRef = useRef(null);

  useEffect(() => {
    registerForPushNotificationsAsync().then(token => setExpoPushToken(token));

    const subscription = Notifications.addNotificationReceivedListener(notification => {
      console.log('Notification Received:', notification);
    });

    return () => subscription.remove();
  }, []);

  const onWebViewLoad = () => {
    if (expoPushToken && webViewRef.current) {
      const js = `
        window.dispatchEvent(new MessageEvent('message', {
          data: { type: 'expo-token', token: '${expoPushToken}' }
        }));
      `;
      webViewRef.current.injectJavaScript(js);
    }
  };

  return (
    <WebView
      ref={webViewRef}
      source={{ uri: 'http://10.250.79.39:5000' }}
      style={{ flex: 1 }}
      onLoad={onWebViewLoad}
    />
  );
}

async function registerForPushNotificationsAsync() {
  let token;
  if (Device.isDevice) {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    if (finalStatus !== 'granted') {
      console.log('Failed to get push token for push notification!');
      return;
    }
    token = (await Notifications.getExpoPushTokenAsync()).data;
    console.log('Expo Push Token:', token);
  } else {
    console.log('Must use physical device for Push Notifications');
  }

  if (Platform.OS === 'android') {
    Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });
  }

  return token;
}
=======
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
>>>>>>> ba06191b32c5c4fd347c100bd2c9e64b23df85ee
