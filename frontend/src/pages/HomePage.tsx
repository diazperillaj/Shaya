// src/pages/Dashboard.jsx
import { useState } from "react";
import MainLayout from "../components/layout/MainLayout";
import UsersPage from "../features/users/UsersPage";

export default function Dashboard() {

  const [activeMenuItem, setActiveMenuItem] = useState('Dashboard');

  return (
    <MainLayout setActiveMenuItem={setActiveMenuItem}>
      <div className="min-w-[700px] overflow-x-auto p-4">
        <UsersPage />
      </div>
    </MainLayout>
  );
}
