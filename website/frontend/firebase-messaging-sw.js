importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyXXXX",
  authDomain: "lab-booking-system-xxxx.firebaseapp.com",
  projectId: "lab-booking-system-xxxx",
  storageBucket: "lab-booking-system-xxxx.appspot.com",
  messagingSenderId: "492426985882",
  appId: "1:492426985882:web:abcd1234"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  self.registration.showNotification(payload.notification.title, {
    body: payload.notification.body,
    icon: "/icon-192.png"
  });
});