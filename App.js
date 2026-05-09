
import React, { useState, useEffect, useRef } from 'react';
import { Platform, Text, View, StyleSheet, Alert } from 'react-native';
import { WebView } from 'react-native-webview';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

// Configure the notification handler for foreground alerts
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
    console.log("App Component Mounted");

    async function setup() {
      try {
        console.log("Calling registerForPushNotificationsAsync");
        const token = await registerForPushNotificationsAsync();

        if (token) {
          console.log("Token received:", token);
          setExpoPushToken(token);
        } else {
          console.warn("No token returned from registration");
        }
      } catch (error) {
        console.error("Setup error:", error);
      }
    }

    setup();

    // Listen for foreground notifications
    const notificationListener = Notifications.addNotificationReceivedListener(notification => {
      console.log('Foreground Notification:', notification);
    });

    // Listen for notification taps
    const responseListener = Notifications.addNotificationResponseReceivedListener(response => {
      console.log('Notification Tapped:', response);
    });

    return () => {
      Notifications.removeNotificationSubscription(notificationListener);
      Notifications.removeNotificationSubscription(responseListener);
    };
  }, []);

  // Inject token into WebView whenever it's ready
  const injectToken = (token) => {
    if (webViewRef.current && token) {
      const js = `
        (function() {
          window.dispatchEvent(new MessageEvent('message', {
            data: { type: 'expo-token', token: ${JSON.stringify(token)} }
          }));
          console.log("JS: Token injected into WebView context");
        })();
      `;
      webViewRef.current.injectJavaScript(js);
      console.log("Token injected into WebView");
    }
  };

  useEffect(() => {
    if (expoPushToken) {
      injectToken(expoPushToken);
    }
  }, [expoPushToken]);

  return (
    <View style={styles.container}>
      <WebView
        ref={webViewRef}
        source={{ uri: 'https://lab-booking-app.onrender.com' }}
        style={{ flex: 1 }}
        onLoad={() => {
          console.log("WebView Loaded");
          if (expoPushToken) injectToken(expoPushToken);
        }}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        onMessage={(event) => {
          try {
            const data = JSON.parse(event.nativeEvent.data);
            if (data.type === 'alert') {
              Alert.alert(data.title, data.message);
              return;
            }
          } catch (e) {
            // Not a JSON message or not an alert
          }
          console.log("WebView Log:", event.nativeEvent.data);
        }}
      />
    </View>
  );
}

async function registerForPushNotificationsAsync() {
  let token;

  if (!Device.isDevice) {
    console.warn("Not a physical device. Push notifications may not work on emulators.");
  }

  // Check and request permissions
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    console.log("Requesting notification permissions");
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.warn("Permission for push notifications not granted");
    return null;
  }

  // Android-specific channel setup
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#FF231F7C',
    });
  }

  // Fetch FCM Device Token
  try {
    console.log("Fetching FCM Device Token");
    const deviceToken = await Notifications.getDevicePushTokenAsync();
    token = deviceToken.data;
    console.log("FCM Token generated successfully");
  } catch (error) {
    console.error("Token generation error:", error);

    // Fallback: Try Expo Push Token if Device Token fails
    try {
      console.log("Attempting fallback to Expo Push Token");
      const expoToken = await Notifications.getExpoPushTokenAsync({
        projectId: Constants?.expoConfig?.extra?.eas?.projectId,
      });
      token = expoToken.data;
      console.log("Expo Push Token generated (fallback)");
    } catch (fallbackError) {
      console.error("Fallback token generation error:", fallbackError);
    }
  }

  return token;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});