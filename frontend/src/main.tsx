import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { AdminPage } from './pages/AdminPage';
import { UserPage } from './pages/UserPage';
import './styles.css';

const userPageEnabled = import.meta.env.VITE_USER_PAGE_ENABLED === 'true';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={userPageEnabled ? <UserPage /> : <Navigate to="/admin" replace />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="*" element={<Navigate to={userPageEnabled ? '/' : '/admin'} replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
