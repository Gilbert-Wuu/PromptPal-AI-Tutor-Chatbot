'use client';

import { useAuth } from '../contexts/AuthContext';
import Header from './Header';
import ProtectedRoute from './ProtectedRoute';

interface ClientLayoutProps {
    children: React.ReactNode;
}

const ClientLayout: React.FC<ClientLayoutProps> = ({ children }) => {
    const { isAuthenticated } = useAuth();

    return (
        <>
            {isAuthenticated && <Header />}
            <ProtectedRoute>{children}</ProtectedRoute>
        </>
    );
};

export default ClientLayout;

