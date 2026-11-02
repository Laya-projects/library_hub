import { useState } from "react";
import Layout from "./components/Layout";
import Navbar from "./components/Navbar";
import BookList from "./components/BookList";
import { sampleBooks } from "./data/sampleBooks";
import { sampleMembers } from "./data/sampleMembers";

export default function App() {
  // Temporary: B6 moves this into MemberContext.
  const [memberId, setMemberId] = useState(sampleMembers[0].member_id);

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
      <h1>Catalogue</h1>
      <BookList books={sampleBooks} />
    </Layout>
  );
}