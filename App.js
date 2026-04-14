import React, { useState, useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import { WebView } from 'react-native-webview';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

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

  // Reusable function to reliably send the push token to the WebView
  const sendTokenToWeb = (tokenToUse) => {
    const tokenObj = tokenToUse || expoPushToken;
    if (tokenObj && webViewRef.current) {
        const js = `
          window.dispatchEvent(new MessageEvent('message', {
            data: { type: 'expo-token', token: '${tokenObj}' }
          }));
          true;
        `;
        webViewRef.current.injectJavaScript(js);
        console.log("Token injected into WebView:", tokenObj);
    }
  };

  // Reusable function to forward notification events to the WebView
  const sendNotificationEventToWeb = (eventType, payload) => {
    if (webViewRef.current) {
        const js = `
          window.dispatchEvent(new MessageEvent('message', {
            data: { type: '${eventType}', payload: ${JSON.stringify(payload)} }
          }));
          true;
        `;
        webViewRef.current.injectJavaScript(js);
    }
  };

  useEffect(() => {
    registerForPushNotificationsAsync().then((token) => {
        if (token) {
            setExpoPushToken(token);
        }
    });

    // Handle foreground notifications
    const notificationListener = Notifications.addNotificationReceivedListener(notification => {
      console.log('Notification Received in foreground:', notification);
      sendNotificationEventToWeb('notification-foreground', notification);
    });

    // Handle notification clicks (foreground and background)
    const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
      console.log('Notification Tapped:', response);
      sendNotificationEventToWeb('notification-tapped', response);
    });

    return () => {
      Notifications.removeNotificationSubscription(notificationListener);
      Notifications.removeNotificationSubscription(responseListener);
    };
  }, []);

  // Run when token changes (race condition safeguard)
  useEffect(() => {
    if (expoPushToken) {
        sendTokenToWeb(expoPushToken);
    }
  }, [expoPushToken]);

  // Run when WebView is loaded (race condition safeguard)
  const onWebViewLoad = () => {
    if (expoPushToken) {
        sendTokenToWeb(expoPushToken);
    }
  };

  return (
    <WebView
      ref={webViewRef}
      source={{ uri: 'https://lab-booking-app.onrender.com' }}
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
      console.log('Failed to get permissions for push notifications!');
      return undefined;
    }

    try {
        const projectId =
          Constants?.expoConfig?.extra?.eas?.projectId ??
          Constants?.easConfig?.projectId;
          
        token = (await Notifications.getExpoPushTokenAsync({
            projectId: projectId,
        })).data;
        
        console.log('Expo Push Token generated successfully.');
    } catch (e) {
        console.log("Error getting push token:", e);
    }
  } else {
    console.log('Must use physical device for Push Notifications');
  }

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });
  }

  return token;
}