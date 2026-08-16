import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider } from "./components/Toast";
import { ChallengeProvider } from "./context/ChallengeContext";
import LoginScreen from "./components/LoginScreen";
import RegisterScreen from "./components/RegisterScreen";
import ResetPasswordScreen from "./components/ResetPasswordScreen";
import OnboardingScreen from "./components/OnboardingScreen";
import TutorialOverlay from "./components/TutorialOverlay";
import QueueScreen from "./components/QueueScreen";
import DuelScreen from "./components/DuelScreen";
import ResultsScreen from "./components/ResultsScreen";
import LeaderboardScreen from "./components/LeaderboardScreen";
import ProfileScreen from "./components/ProfileScreen";
import LobbyScreen from "./components/LobbyScreen";
import SpectatorView from "./components/SpectatorView";
import FriendsScreen from "./components/FriendsScreen";
import CustomLobbyScreen from "./components/CustomLobbyScreen";
import Navbar from "./components/Navbar";
import { DuelProvider } from "./context/DuelContext";
import "./styles/app.css";

function ProtectedRoute({ children }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

function BootstrappingGate({ children }) {
  const { bootstrapping } = useAuth();
  if (bootstrapping) return null;
  return children;
}

function PublicRoute({ children }) {
  const { token } = useAuth();
  if (token) return <Navigate to="/" replace />;
  return children;
}

function Layout({ children }) {
  return (
    <div className="app-layout page-enter">
      <Navbar />
      <main className="app-main">{children}</main>
    </div>
  );
}

function HomeRoute() {
  const { token, user } = useAuth();
  if (!token) return <OnboardingScreen />;
  if (user && !user.tutorial_completed) return <TutorialOverlay />;
  return (
    <Layout>
      <QueueScreen />
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <BootstrappingGate>
          <ToastProvider>
            <ChallengeProvider>
            <Routes>
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <LoginScreen />
                </PublicRoute>
              }
            />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <RegisterScreen />
              </PublicRoute>
            }
          />
          <Route
            path="/reset-password"
            element={
              <PublicRoute>
                <ResetPasswordScreen />
              </PublicRoute>
            }
          />
            <Route path="/" element={<HomeRoute />} />
            <Route
              path="/leaderboard"
              element={
                <ProtectedRoute>
                  <Layout>
                    <LeaderboardScreen />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile/:userId"
              element={
                <ProtectedRoute>
                  <Layout>
                    <ProfileScreen />
                  </Layout>
                </ProtectedRoute>
              }
            />
            <Route
              path="/duel/:matchId"
              element={
                <ProtectedRoute>
                  <DuelProvider>
                    <DuelScreen />
                  </DuelProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/results/:matchId"
              element={
                <ProtectedRoute>
                  <DuelProvider>
                    <ResultsScreen />
                  </DuelProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/lobby"
              element={
                <ProtectedRoute>
                  <Layout>
                    <LobbyScreen />
                  </Layout>
                </ProtectedRoute>
              }
            />
          <Route
            path="/spectate/:matchId"
            element={
              <ProtectedRoute>
                <Layout>
                  <SpectatorView />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/friends"
            element={
              <ProtectedRoute>
                <Layout>
                  <FriendsScreen />
                </Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/custom-game"
            element={
              <ProtectedRoute>
                <Layout>
                  <CustomLobbyScreen />
                </Layout>
              </ProtectedRoute>
            }
          />
          </Routes>
          </ChallengeProvider>
          </ToastProvider>
        </BootstrappingGate>
      </AuthProvider>
    </BrowserRouter>
  );
}
