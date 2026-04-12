importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js');

firebase.initializeApp({
 apiKey: "AIzaSyAYpXGDlYTg03U-WWRpEvIAqnqUyJFc6QU",
  authDomain: "lab-booking-system-e77ad.firebaseapp.com",
  projectId: "lab-booking-system-e77ad",
  storageBucket: "lab-booking-system-e77ad.firebasestorage.app",
  messagingSenderId: "492426985882",
  appId: "1:492426985882:web:648566f44e48acdb497a23",
  measurementId: "G-Z8H51WZZYP"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  self.registration.showNotification(payload.notification.title, {
    body: payload.notification.body,
    icon: "/icon-192.png"
  });
});