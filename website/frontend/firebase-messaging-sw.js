importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// 🔥 Your Firebase config (REAL VALUES — NOT placeholders)
firebase.initializeApp({
  apiKey: "AIzaSyAYpXGDlYTg03U-WWRpEvIAqnqUyJFc6QU",
  authDomain: "lab-booking-system-e77ad.firebaseapp.com",
  projectId: "lab-booking-system-e77ad",
  storageBucket: "lab-booking-system-e77ad.firebasestorage.app",
  messagingSenderId: "492426985882",
  appId: "1:492426985882:web:648566f44e48acdb497a23"
});

// Initialize messaging
const messaging = firebase.messaging();

// ✅ Background Notification
messaging.onBackgroundMessage(function(payload) {
  console.log("🔥 Background message:", payload);

  self.registration.showNotification(
    payload.notification?.title || payload.data?.title || "New Notification",
    {
      body: payload.notification?.body || payload.data?.body || "You have a new update",
      icon: "/icon-192.png"
    }
  );
});