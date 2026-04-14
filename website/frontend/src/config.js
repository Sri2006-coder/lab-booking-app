import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getMessaging, getToken, onMessage } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging.js";

console.log("Firebase Modular Config Loaded");

<<<<<<< HEAD
// 1. Firebase Web SDK Configuration
=======
// Firebase config
>>>>>>> ba06191b32c5c4fd347c100bd2c9e64b23df85ee
const firebaseConfig = {
  apiKey: "AIzaSyAYpXGDlYTg03U-WWRpEvIAqnqUyJFc6QU",
  authDomain: "lab-booking-system-e77ad.firebaseapp.com",
  projectId: "lab-booking-system-e77ad",
  storageBucket: "lab-booking-system-e77ad.firebasestorage.app",
  messagingSenderId: "492426985882",
  appId: "1:492426985882:web:648566f44e48acdb497a23"
};

<<<<<<< HEAD
// 2. Initialize Firebase
const app = initializeApp(firebaseConfig);

// 3. Initialize messaging using getMessaging
const messaging = getMessaging(app);

// Helper function to handle Notifications initialization
function initNotifications() {
  // We specify the path to our service worker generated for Firebase
  navigator.serviceWorker.register("/firebase-messaging-sw.js")
    .then((registration) => {
      console.log("Service Worker Registered for Firebase");

      // 4. Ask user for notification permission
      Notification.requestPermission().then((permission) => {
        if (permission === "granted") {
          console.log("Notification permission explicitly granted.");

          // 5. Generate FCM token using VAPID key
          getToken(messaging, {
            vapidKey: "BPffVCwY5C4FPtAZ99CNYXiNCE4WJkHaHh8R7Gb_zdkigHa2xs96ZGAJqKkdWGWahZQWSa9SNHrZn7S3-5VKTqc",
            serviceWorkerRegistration: registration
          })
          .then((currentToken) => {
            if (currentToken) {
              // 6. Log the token in console
              console.log("✅ FCM Token generated:", currentToken);

              // 7. Send token to backend endpoint /save-token using fetch POST
              fetch("/save-token", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json"
                },
                body: JSON.stringify({ token: currentToken })
              })
              .then(response => response.json())
              .then(data => console.log("Backend response saved token:", data))
              .catch(err => console.error("Failed to send token to backend:", err));

            } else {
              console.warn("No registration token available. Ensure proper permission/setup.");
            }
          })
          .catch((err) => {
            console.error("An error occurred while generating FCM token:", err);
          });
        } else {
          console.warn("Notification permission was denied.");
        }
      });
    })
    .catch((err) => {
      console.error("Service Worker registration failed:", err);
    });
=======
// Initialize Firebase
const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// 🔔 INIT NOTIFICATIONS
async function initNotifications() {
  try {
    const registration = await navigator.serviceWorker.register("/firebase-messaging-sw.js");
    console.log("Service Worker Registered");

    const permission = await Notification.requestPermission();

    if (permission !== "granted") {
      console.warn("Notification permission denied");
      return;
    }

    console.log("Notification permission granted");

    // ✅ Get token properly
    const currentToken = await getToken(messaging, {
      vapidKey: "BPffVCwY5C4FPtAZ99CNYXiNCE4WJkHaHh8R7Gb_zdkigHa2xs96ZGAJqKkdWGWahZQWSa9SNHrZn7S3-5VKTqc",
      serviceWorkerRegistration: registration
    });

    if (currentToken) {
      console.log("✅ Token:", currentToken);

      // Store locally
      localStorage.setItem("fcm_token", currentToken);

      // Send to backend
      await fetch("/save-token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ token: currentToken })
      });

      console.log("✅ Token sent to backend");
    } else {
      console.warn("No token received");
    }

  } catch (err) {
    console.error("FCM error:", err);
  }
>>>>>>> ba06191b32c5c4fd347c100bd2c9e64b23df85ee
}

initNotifications();

<<<<<<< HEAD
// 8. Handle foreground notifications using onMessage
onMessage(messaging, (payload) => {
  console.log("📩 Foreground Message received:", payload);

  // Read message content
  if (payload.notification) {
    const title = payload.notification.title || "New Notification";
    const body = payload.notification.body || "You have a new message.";

    // Provide a neat browser built-in notification pop-up
    new Notification(title, {
      body: body,
      icon: "/favicon.ico" // You can provide a custom icon URL here
    });

    // We can also trigger a visual UI update like alert if we want it to be very visible
    // alert(`📢 ${title}\n${body}`);
=======
// 📩 FOREGROUND NOTIFICATIONS
onMessage(messaging, (payload) => {
  console.log("📩 Foreground message:", payload);

  if (payload.notification) {
    new Notification(payload.notification.title, {
      body: payload.notification.body,
      icon: "/icon-192.png"
    });
>>>>>>> ba06191b32c5c4fd347c100bd2c9e64b23df85ee
  }
});