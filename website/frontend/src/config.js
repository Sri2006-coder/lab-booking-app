import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
import { getMessaging, getToken, onMessage } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging.js";

console.log("Firebase Modular Config Loaded");

// Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyAYpXGDlYTg03U-WWRpEvIAqnqUyJFc6QU",
  authDomain: "lab-booking-system-e77ad.firebaseapp.com",
  projectId: "lab-booking-system-e77ad",
  storageBucket: "lab-booking-system-e77ad.firebasestorage.app",
  messagingSenderId: "492426985882",
  appId: "1:492426985882:web:648566f44e48acdb497a23"
};

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
}

initNotifications();

// 📩 FOREGROUND NOTIFICATIONS
onMessage(messaging, (payload) => {
  console.log("📩 Foreground message:", payload);

  if (payload.notification) {
    new Notification(payload.notification.title, {
      body: payload.notification.body,
      icon: "/favicon.ico"
    });
  }
});