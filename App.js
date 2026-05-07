
import React, { useState, useEffect, useRef } from 'react';
import { Platform, Alert, Text, View, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';

// 1. Configure the notification handler for foreground alerts
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export default function App() {
  const [expoPushToken, setExpoPushToken] = useState('');
  const [debugInfo, setDebugInfo] = useState('Initializing...');
  const webViewRef = useRef(null);

  // STEP 1 & 2: Component Mounting & useEffect Log
  useEffect(() => {
    console.log("DEBUG: App Component Mounted");
    setDebugInfo('App started, setting up notifications...');
    
    // Immediate feedback for the user
    alert("DEBUG 1: App Started");

    async function setup() {
        try {
            console.log("DEBUG: Calling registerForPushNotificationsAsync");
            alert("DEBUG 2: Registration function called");
            
            const token = await registerForPushNotificationsAsync();
            
            if (token) {
                console.log("DEBUG: Token received:", token);
                setExpoPushToken(token);
                setDebugInfo('Token Generated Successfully');
                alert("DEBUG 5: Token received in App.js: " + token.substring(0, 10) + "...");
            } else {
                console.log("DEBUG: No token returned");
                setDebugInfo('Failed to generate token');
                alert("DEBUG 5: Failed to generate token");
            }
        } catch (error) {
            console.error("DEBUG: Setup error:", error);
            setDebugInfo('Error: ' + error.message);
            alert("DEBUG ERROR: " + error.message);
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
      console.log("DEBUG: Token injected into WebView");
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
            console.log("DEBUG: WebView Loaded");
            if (expoPushToken) injectToken(expoPushToken);
        }}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        onMessage={(event) => {
            console.log("WebView Log:", event.nativeEvent.data);
        }}
      />
      {/* Debug overlay to see status on screen */}
      <View style={styles.debugOverlay}>
        <Text style={styles.debugText}>{debugInfo}</Text>
      </View>
    </View>
  );
}

async function registerForPushNotificationsAsync() {
  let token;

  // STEP 3: Initial Check
  console.log("DEBUG: STEP 3: Checking device status");
  alert("DEBUG 3: Checking device and permissions");

  if (!Device.isDevice) {
    console.warn("DEBUG: Not a physical device");
    alert("WARNING: Running on Emulator. Push may not work.");
  }

  // STEP 4: Permissions
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;
  
  if (existingStatus !== 'granted') {
    console.log("DEBUG: Requesting new permissions");
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }
  
  if (finalStatus !== 'granted') {
    alert("CRITICAL: Permission for notifications not granted!");
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

  // STEP 5: Token Generation
  try {
    console.log("DEBUG: STEP 4: Fetching FCM Device Token");
    alert("DEBUG 4: Fetching FCM Token...");

    // Important: projectId is often required in newer Expo versions even for native tokens
    const projectId = Constants?.expoConfig?.extra?.eas?.projectId || Constants?.easConfig?.projectId;
    
    // We try to get the device push token (native FCM token)
    // Note: getDevicePushTokenAsync() is specifically for direct Firebase integration
    const deviceToken = await Notifications.getDevicePushTokenAsync();
    token = deviceToken.data;

    console.log("DEBUG: FCM Token Success:", token);
    alert("SUCCESS: Token Generated!");
    
  } catch (error) {
    console.error("DEBUG: Token Generation Error:", error);
    alert("ERROR at STEP 4: " + error.message);
    
    // Fallback: Try Expo Push Token if Device Token fails
    try {
        console.log("DEBUG: Attempting Fallback to Expo Push Token");
        const expoToken = await Notifications.getExpoPushTokenAsync({
            projectId: Constants?.expoConfig?.extra?.eas?.projectId
        });
        token = expoToken.data;
        console.log("DEBUG: Expo Token Generated (Fallback):", token);
    } catch (fallbackError) {
        console.error("DEBUG: Fallback Error:", fallbackError);
    }
  }

  return token;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  debugOverlay: {
    position: 'absolute',
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    padding: 10,
    width: '100%',
  },
  debugText: {
    color: 'white',
    fontSize: 10,
  }
});