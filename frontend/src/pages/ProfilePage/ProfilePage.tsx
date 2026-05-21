import { useState, useEffect, useRef } from 'react';
import { Container, Grid, Box } from '@mantine/core';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import ProfileCard from '../../components/ProfileCard/ProfileCard';
import ProfileSettings from '../../components/ProfileSettings/ProfileSettings';
import ProfileHistoryList from '../../components/ProfileHistoryList/ProfileHistoryList';
import classes from './ProfilePage.module.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

interface ChatSession {
  id: number;
  university_id?: number;
  created_at: string;
}

interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  university_id?: number;
}

export default function ProfilePage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [universities, setUniversities] = useState<{ value: string; label: string }[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [token, setToken] = useState<string | null>(null);

  // Read initial states from localStorage or fallback
  const [historySaved, setHistorySaved] = useState(() => {
    const saved = localStorage.getItem('historySaved');
    return saved !== 'false';
  });
  const [anonymized, setAnonymized] = useState(() => {
    const anon = localStorage.getItem('anonymized');
    return anon === 'true';
  });

  const navigate = useNavigate();

  // Auth check & load initial data
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (!storedToken) {
      navigate('/');
      return;
    }
    setToken(storedToken);

    // Fetch profile
    fetch(`${API_BASE_URL}/users/me`, {
      headers: {
        'Authorization': `Bearer ${storedToken}`
      }
    })
      .then(res => {
        if (res.ok) return res.json();
        throw new Error('Unauthorized');
      })
      .then(data => {
        setUser(data);
        localStorage.setItem('user', JSON.stringify(data));
        window.dispatchEvent(new Event('user-updated'));
      })
      .catch(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/');
      });

    // Fetch universities
    fetch(`${API_BASE_URL}/universities`, {
      headers: {
        'Authorization': `Bearer ${storedToken}`
      }
    })
      .then(res => res.json())
      .then(data => {
        setUniversities(data.map((uni: any) => ({
          value: String(uni.id),
          label: uni.name
        })));
      })
      .catch(err => console.error('Error fetching universities:', err));

    // Fetch sessions
    fetch(`${API_BASE_URL}/chat/sessions`, {
      headers: {
        'Authorization': `Bearer ${storedToken}`
      }
    })
      .then(res => res.json())
      .then(data => setSessions(data))
      .catch(err => console.error('Error fetching sessions:', err));

  }, [navigate]);

  // Persist local settings changes to localStorage
  useEffect(() => {
    localStorage.setItem('historySaved', String(historySaved));
  }, [historySaved]);

  useEffect(() => {
    localStorage.setItem('anonymized', String(anonymized));
  }, [anonymized]);

  // Get user role based on email
  const getRole = (email: string) => {
    if (email.startsWith('admin')) return { label: 'Yönetici', color: 'red' };
    if (email.includes('ogrmail') || email.includes('student') || /\d/.test(email)) return { label: 'Öğrenci', color: 'cyan' };
    return { label: 'Akademisyen', color: 'grape' };
  };

  // Handle active university update
  const handleUniversityChange = async (val: string | null) => {
    if (!val || !token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ university_id: Number(val) })
      });
      if (res.ok) {
        const updatedUser = await res.json();
        setUser(updatedUser);
        localStorage.setItem('user', JSON.stringify(updatedUser));
        window.dispatchEvent(new Event('user-updated'));
      }
    } catch (err) {
      console.error('Error updating university:', err);
    }
  };

  // Handle account deletion
  const handleDeleteAccount = async () => {
    if (!token) return;
    if (!window.confirm('Hesabınızı silmek istediğinizden emin misiniz? Bu işlem geri alınamaz ve tüm geçmiş sohbetleriniz kalıcı olarak temizlenir.')) {
      return;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/');
      }
    } catch (err) {
      console.error('Error deleting account:', err);
    }
  };

  // Click on a chat history item to open it in chat page
  const handleOpenChat = (sessionId: number) => {
    navigate(`/chat?session_id=${sessionId}`);
  };

  // GSAP Entry Animations
  useGSAP(() => {
    if (user) {
      gsap.from('.glass-card-col', {
        y: 30,
        opacity: 0,
        stagger: 0.2,
        duration: 0.8,
        ease: 'power2.out'
      });
    }
  }, { scope: containerRef, dependencies: [user !== null] });

  if (!user) {
    return null;
  }

  const roleInfo = getRole(user.email);
  const usedQueries = Math.min(sessions.length * 4, 50);
  const capacityPercent = Math.round((usedQueries / 50) * 100);

  return (
    <div ref={containerRef} className={classes.profilePage}>
      <Container size="xl">
        <Grid style={{ gap: 'var(--mantine-spacing-xl)' }}>
          {/* LEFT PANEL - Profile Info & Settings */}
          <Grid.Col span={{ base: 12, md: 4 }} className="glass-card-col">
            <Box className={classes.leftColumnContainer}>
              <ProfileCard
                user={user}
                roleInfo={roleInfo}
                sessionsCount={sessions.length}
                usedQueries={usedQueries}
              />
              <ProfileSettings
                user={user}
                token={token || ''}
                universities={universities}
                onUserUpdate={setUser}
                onDeleteAccount={handleDeleteAccount}
                historySaved={historySaved}
                setHistorySaved={setHistorySaved}
                anonymized={anonymized}
                setAnonymized={setAnonymized}
                onUniversityChange={handleUniversityChange}
              />
            </Box>
          </Grid.Col>

          {/* RIGHT PANEL - Chat History & Capacity */}
          <Grid.Col span={{ base: 12, md: 8 }} className="glass-card-col">
            <ProfileHistoryList
              sessions={sessions}
              universities={universities}
              onOpenChat={handleOpenChat}
              usedQueries={usedQueries}
              capacityPercent={capacityPercent}
            />
          </Grid.Col>
        </Grid>
      </Container>
    </div>
  );
}
