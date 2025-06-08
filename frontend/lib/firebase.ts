// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth, GoogleAuthProvider, signInWithPopup, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut, onAuthStateChanged, User } from "firebase/auth";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyAV-8GAjwn1t-Fr-WV7DtTUhrOvE0L4WhY",
  authDomain: "lexify-3c202.firebaseapp.com",
  projectId: "lexify-3c202",
  storageBucket: "lexify-3c202.firebasestorage.app",
  messagingSenderId: "318177375708",
  appId: "1:318177375708:web:6b7fbc63b24b6ba2054b19",
  measurementId: "G-3SMDF8MWFC"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

// Initialize Google Auth Provider
export const googleProvider = new GoogleAuthProvider();

// Auth functions
export const signInWithGoogle = () => signInWithPopup(auth, googleProvider);

export const signInWithEmail = (email: string, password: string) => 
  signInWithEmailAndPassword(auth, email, password);

export const signUpWithEmail = (email: string, password: string) => 
  createUserWithEmailAndPassword(auth, email, password);

export const logOut = () => signOut(auth);

export const onAuthStateChange = (callback: (user: User | null) => void) => 
  onAuthStateChanged(auth, callback);

// Initialize Analytics (only in browser)
let analytics;
if (typeof window !== 'undefined') {
  analytics = getAnalytics(app);
}

export { analytics }; 