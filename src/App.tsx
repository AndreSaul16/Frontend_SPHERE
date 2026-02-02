import { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { MainLayout } from "@/components/layout/MainLayout";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { ArtifactPanel } from "@/components/artifacts/ArtifactPanel";
import { AgentSelectorModal } from "@/components/modals/AgentSelectorModal";
import { ProfilePage } from "@/pages/ProfilePage";
import { ChatSettingsPage } from "@/pages/ChatSettingsPage";
import { AuroraBackground } from "@/components/AuroraBackground";
import { ErrorOverlay } from "@/components/common/ErrorOverlay";
import { useChatStore } from "@/store/useChatStore";

function App() {
  const { fetchSessions, fetchCustomAgents } = useChatStore();

  useEffect(() => {
    // Sincronización inicial con Backend v2.0
    fetchSessions();
    fetchCustomAgents();
  }, [fetchSessions, fetchCustomAgents]);

  return (
    <div className="relative min-h-screen">
      <AuroraBackground />
      <ErrorOverlay />
      <AgentSelectorModal />
      <Routes>
        <Route
          path="/"
          element={
            <MainLayout
              sidebar={<Sidebar />}
              chat={<ChatPanel />}
              artifactPanel={<ArtifactPanel />}
            />
          }
        />
        <Route
          path="/chat/:sessionId"
          element={
            <MainLayout
              sidebar={<Sidebar />}
              chat={<ChatPanel />}
              artifactPanel={<ArtifactPanel />}
            />
          }
        />
        <Route
          path="/profile"
          element={
            <MainLayout
              sidebar={<Sidebar />}
              chat={<ProfilePage />}
            />
          }
        />
        <Route
          path="/chat/settings"
          element={
            <MainLayout
              sidebar={<Sidebar />}
              chat={<ChatSettingsPage />}
            />
          }
        />
      </Routes>
    </div>
  );
}

export default App;
