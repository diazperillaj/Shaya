// src/pages/Dashboard.jsx
import { useState } from "react";
import MainLayout from "../components/layout/MainLayout";
import UsersPage from "../features/users/UsersPage";

export default function Dashboard() {

  const [activeMenuItem, setActiveMenuItem] = useState('Dashboard');

  console.log(activeMenuItem);

  return (
    <MainLayout setActiveMenuItem={setActiveMenuItem}>
      <UsersPage />
    </MainLayout>
  );
}
