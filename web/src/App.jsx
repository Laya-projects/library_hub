import { useState } from "react";
import Layout from "./components/Layout";
import Navbar from "./components/Navbar";
import CataloguePage from "./pages/CataloguePage";
import AddItemForm from "./components/AddItemForm";
import { sampleMembers } from "./data/sampleMembers";

export default function App() {
  // Temporary: B6 moves this into MemberContext.
  const [memberId, setMemberId] = useState(sampleMembers[0].member_id);
  // Temporary: B5 replaces this with routing.
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <Layout
      navbar={
        <Navbar
          basketCount={0}
          members={sampleMembers}
          currentMemberId={memberId}
          onMemberChange={setMemberId}
        />
      }
    >
      <CataloguePage refreshKey={refreshKey} />
      <h2>Add item (librarian)</h2>
      <AddItemForm onCreated={() => setRefreshKey((k) => k + 1)} />
    </Layout>
  );
}