import React, { useState } from 'react';
import { Clipboard, Home, ShoppingBag, Users, UserCog, PersonStanding, ChevronLeft, ChevronRight, Wheat } from 'lucide-react';
import { logout } from '../../features/auth/service';
import { useNavigate } from 'react-router-dom';

type setActiveMenuItemProps = (item: string) => void;

function Sidebar({ children, setActiveMenuItem }: { children: React.ReactNode, setActiveMenuItem: setActiveMenuItemProps }) {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    const menuItems = [
        { name: 'Inicio', icon: Home, label: 'home' },
        { name: 'Inventario', icon: Clipboard, label: 'inventory' },
        { name: 'Ventas', icon: ShoppingBag, label: 'sales' },
        { name: 'Clientes', icon: Users, label: 'clients' },
        { name: 'Caficultores', icon: PersonStanding, label: 'farmers' },
        { name: 'Usuarios', icon: UserCog, label: 'users' },
    ];

    const navigate = useNavigate()

    const handleLogout = async () => {
    
        try {
          await logout()
          navigate("/login")
        } catch (err: any) {
          alert(err.message)
        }
      }

    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);

    return (
        <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100">
            {/* Sidebar */}
            <div className={`relative flex flex-col bg-gradient-to-b from-emerald-900 via-emerald-800 to-emerald-900 text-white transition-all duration-300 ease-in-out shadow-2xl ${isSidebarOpen ? 'w-72' : 'w-20'}`}>

                {/* Logo/Header */}
                <div className="px-6 py-8 border-b border-emerald-700/50">
                    <div className={`flex items-center gap-3 transition-all duration-300 ${isSidebarOpen ? 'justify-start' : 'justify-center'}`}>
                        <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform duration-200">
                            <Wheat className="w-6 h-6 text-white" />
                        </div>
                        {isSidebarOpen && (
                            <div className="overflow-hidden">
                                <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white to-emerald-100 bg-clip-text text-transparent">
                                    Shaya Café
                                </h1>
                                <p className="text-xs text-emerald-300 mt-0.5">Sistema de gestión</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Menu Items */}
                <nav className="flex-1 px-3 py-6 space-y-1 scrollbar-thin scrollbar-thumb-emerald-700 scrollbar-track-transparent">
                    {menuItems.map((item, index) => {
                        const Icon = item.icon;
                        return (
                            <div
                                key={item.name}
                                className={`group relative flex items-center gap-4 px-4 py-3.5 rounded-xl cursor-pointer transition-all duration-200 hover:bg-emerald-800/60 hover:shadow-lg hover:translate-x-1 ${isSidebarOpen ? '' : 'justify-center'}`}
                                style={{ animationDelay: `${index * 50}ms` }}
                                onClick={() => setActiveMenuItem(item.label)}
                            >
                                <div className="flex items-center justify-center w-5 h-5 text-emerald-200 group-hover:text-white group-hover:scale-110 transition-all duration-200">
                                    {<Icon className="w-5 h-5" />}
                                </div>

                                {isSidebarOpen && (
                                    <span className="text-sm font-medium text-emerald-50 group-hover:text-white transition-colors duration-200">
                                        {item.name}
                                    </span>
                                )}
                            </div>
                        )
                    })}
                        
                </nav>

                {/* Toggle Button */}
                <div className="px-4 py-4 border-t border-emerald-700/50">
                    <button
                        onClick={toggleSidebar}
                        className="w-full flex items-center justify-center p-3 rounded-xl bg-emerald-800/50 hover:bg-emerald-700/60 transition-all duration-200 group shadow-lg hover:shadow-xl"
                        aria-label={isSidebarOpen ? 'Cerrar sidebar' : 'Abrir sidebar'}
                    >
                        {isSidebarOpen ? (
                            <ChevronLeft className="w-5 h-5 text-emerald-200 group-hover:text-white transition-colors duration-200" />
                        ) : (
                            <ChevronRight className="w-5 h-5 text-emerald-200 group-hover:text-white transition-colors duration-200" />
                        )}
                    </button>
                    <p className="cursor-pointer text-xs text-emerald-300 mt-2"><a onClick={handleLogout}>Cerrar sesión</a></p>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
                <main className="flex-1 p-8 overflow-auto">
                    {children}
                </main>
            </div>
        </div>
    );
};

export default Sidebar;