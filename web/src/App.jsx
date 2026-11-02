import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Navbar from "./components/Navbar";
import CataloguePage from "./pages/CataloguePage";
import BookDetailsPage from "./pages/BookDetailsPage";
import MyLoansPage from "./pages/MyLoansPage";
import BasketPage from "./pages/BasketPage";
import AddItemPage from "./pages/AddItemPage";
import NotFoundPage from "./pages/NotFoundPage";
import { MemberProvider, useMember } from "./context/MemberContext";
import { BasketProvider, useBasket } from "./context/BasketContext";

function AppShell() {
  const { members, currentMember, setCurrentMemberId, loading } = useMember();
  const basket = useBasket();

  return (
    <Layout
      navbar={
        <Navbar
          basketCount={basket.items.length}
          members={members}
          membersLoading={loading}
          currentMemberId={currentMember?.member_id ?? ""}
          onMemberChange={setCurrentMemberId}
        />
      }
    >
      {basket.message && (
        <p role="status" className="mb-4 rounded-md border-purple-300 bg-purple-100 px-3 py-2 text-purple-900">
          {basket.message}
        </p>
      )}
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

export default function App() {
  return (
    <MemberProvider>
      <BasketProvider>
        <AppShell />
      </BasketProvider>
    </MemberProvider>
  );
}