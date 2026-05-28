
import React, { useState, useEffect, useRef } from 'react';
import { Platform, Text, View, StyleSheet, Alert, ActivityIndicator, TouchableOpacity, SafeAreaView } from 'react-native';
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
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
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

  const handleReload = () => {
    setHasError(false);
    setIsLoading(true);
    if (webViewRef.current) {
      webViewRef.current.reload();
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {hasError ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorEmoji}>📶</Text>
          <Text style={styles.errorTitle}>Connection Timeout</Text>
          <Text style={styles.errorText}>
            Could not connect to the Lab Booking server. Please make sure you are connected to the internet.
          </Text>
          <TouchableOpacity style={styles.retryButton} onPress={handleReload}>
            <Text style={styles.retryButtonText}>Tap to Retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={{ flex: 1 }}>
          <WebView
            ref={webViewRef}
            source={{ uri: 'https://lab-booking-system-e77ad.web.app' }}
            style={{ flex: 1 }}
            onLoadStart={() => setIsLoading(true)}
            onLoad={() => {
              console.log("WebView Loaded successfully");
              setIsLoading(false);
              setHasError(false);
              if (expoPushToken) injectToken(expoPushToken);
            }}
            onError={(syntheticEvent) => {
              const { nativeEvent } = syntheticEvent;
              console.warn('WebView error: ', nativeEvent);
              setHasError(true);
              setIsLoading(false);
            }}
            onHttpError={(syntheticEvent) => {
              const { nativeEvent } = syntheticEvent;
              console.warn('WebView HTTP error: ', nativeEvent);
              // Only fail on critical server crashes (5xx errors)
              if (nativeEvent.statusCode >= 500) {
                setHasError(true);
              }
              setIsLoading(false);
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
          
          {isLoading && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#2563EB" />
              <Text style={styles.loadingText}>Connecting to Lab Panel...</Text>
            </View>
          )}
        </View>
      )}
    </SafeAreaView>
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
    backgroundColor: '#F3F4F6',
  },
  loadingContainer: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(243, 244, 246, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 15,
    color: '#1E293B',
    fontSize: 16,
    fontWeight: '600',
    fontFamily: Platform.OS === 'ios' ? 'System' : 'sans-serif-medium',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 30,
    backgroundColor: '#FFFFFF',
  },
  errorEmoji: {
    fontSize: 70,
    marginBottom: 20,
  },
  errorTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 10,
    textAlign: 'center',
  },
  errorText: {
    fontSize: 15,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 30,
  },
  retryButton: {
    backgroundColor: '#2563EB',
    paddingVertical: 14,
    paddingHorizontal: 30,
    borderRadius: 12,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
});