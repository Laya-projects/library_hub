import { useState } from "react";
import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Navbar from "./components/Navbar";
import CataloguePage from "./pages/CataloguePage";
import BookDetailsPage from "./pages/BookDetailsPage";
import MyLoansPage from "./pages/MyLoansPage";
import BasketPage from "./pages/BasketPage";
import AddItemPage from "./pages/AddItemPage";
import NotFoundPage from "./pages/NotFoundPage";
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
      <Routes>
        <Route path="/" element={<CataloguePage />} />
        <Route path="/books/:isbn" element={<BookDetailsPage />} />
        <Route path="/me" element={<MyLoansPage />} />
        <Route path="/basket" element={<BasketPage />} />
        <Route path="/admin/add" element={<AddItemPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Layout>
  );
}