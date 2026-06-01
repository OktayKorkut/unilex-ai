import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ChatPage from './pages/ChatPage';
import AdminPage from './pages/AdminPage';
import AdminCrawlerPage from './pages/AdminCrawlerPage';
import AdminHealthPage from './pages/AdminHealthPage';
import AboutPage from './pages/AboutPage';
import ContactPage from './pages/ContactPage';
import ProfilePage from './pages/ProfilePage';
import ResetPasswordPage from './pages/ResetPasswordPage/ResetPasswordPage';
import Header from './components/Header/Header';
import Footer from './components/Footer/Footer';
import { Box } from '@mantine/core';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={
          <Box>
            <Header />
            <HomePage />
          </Box>
        } />
        <Route path="/about" element={
          <Box>
            <Header />
            <AboutPage />
            <Footer />
          </Box>
        } />
        <Route path="/contact" element={
          <Box>
            <Header />
            <ContactPage />
            <Footer />
          </Box>
        } />
        <Route path="/profile" element={
          <Box>
            <Header />
            <ProfilePage />
            <Footer />
          </Box>
        } />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/admin/crawler" element={<AdminCrawlerPage />} />
        <Route path="/admin/health" element={<AdminHealthPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
      </Routes>
    </Router>
  )
}

export default App;
