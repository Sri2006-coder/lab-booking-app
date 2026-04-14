importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyAYpXGDlYTg03U-WWRpEvIAqnqUyJFc6QU",
  authDomain: "lab-booking-system-e77ad.firebaseapp.com",
  projectId: "lab-booking-system-e77ad",
  messagingSenderId: "492426985882",
  appId: "1:492426985882:web:648566f44e48acdb497a23"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  console.log("🔥 Background message:", payload);

  self.registration.showNotification(
    payload.notification?.title || payload.data.title,
    {
      body: payload.notification?.body || payload.data.body,
      icon: "/icon-192.png"
    }
  );
});