// src/pages/Dashboard.jsx
import { useState } from "react";
import MainLayout from "../../../components/layout/MainLayout";


export default function Dashboard() {

  const [activeMenuItem, setActiveMenuItem] = useState('Dashboard');

  console.log(activeMenuItem);

  return (
    <MainLayout setActiveMenuItem={setActiveMenuItem}>
      <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
      <p>Este es el contenido principal entre el header y el sidebar.</p>
    </MainLayout>
  );
}
