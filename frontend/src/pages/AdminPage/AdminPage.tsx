import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell, Group, Text, Paper, SimpleGrid, Badge, ThemeIcon, Divider, ActionIcon, Box, Loader, Alert, Avatar, Burger } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconActivity, IconCheck, IconAlertCircle, IconInfoCircle, IconUsers, IconSchool, IconFileText, IconMessage } from '@tabler/icons-react';
import AdminSidebar from '../../components/AdminSidebar/AdminSidebar';
import classes from './AdminPage.module.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

interface StatsData {
  users: number;
  universities: number;
  documents: number;
  chat_sessions: number;
}

interface FeedbackData {
  id: number;
  full_name: string;
  email: string;
  message: string;
  created_at: string;
}

export default function AdminPage() {
  const [opened, { toggle, close }] = useDisclosure(false);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [feedbacks, setFeedbacks] = useState<FeedbackData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');

    if (!token || !storedUser) {
      navigate('/');
      return;
    }

    try {
      const parsedUser = JSON.parse(storedUser);
      const isAdminUser = parsedUser.is_admin || parsedUser.email?.startsWith('admin');
      if (!isAdminUser) {
        navigate('/');
        return;
      }
      
      // Fetch stats and feedbacks
      Promise.all([
        fetch(`${API_BASE_URL}/admin/stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).then(res => {
          if (res.ok) return res.json();
          if (res.status === 403) throw new Error('Yönetici yetkiniz bulunmamaktadır.');
          throw new Error('İstatistikler yüklenirken bir hata oluştu.');
        }),
        fetch(`${API_BASE_URL}/admin/feedbacks`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).then(res => {
          if (res.ok) return res.json();
          throw new Error('Geri bildirimler yüklenirken bir hata oluştu.');
        })
      ])
        .then(([statsData, feedbacksData]) => {
          setStats(statsData);
          setFeedbacks(feedbacksData);
          setLoading(false);
        })
        .catch(err => {
          setError(err.message);
          setLoading(false);
        });

    } catch (e) {
      navigate('/');
    }
  }, [navigate]);

  return (
    <AppShell
      navbar={{
        width: 280,
        breakpoint: 'sm',
        collapsed: { mobile: !opened }
      }}
      padding={{ base: 'md', sm: 'xl' }}
      bg="gray.0"
    >
      {/* SIDEBAR Component */}
      <AdminSidebar activePage="dashboard" onClose={close} />
      <AppShell.Main>
        {/* HEADER */}
        <Group justify="space-between" mb="xl">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" color="dark" />
            <Text size="xl" fw={800}>Sistem İzleme</Text>
            <Badge color="teal" variant="light" size="lg" radius="sm" visibleFrom="xs">Canlı Veri Akışı Aktif</Badge>
          </Group>
        </Group>

        {loading ? (
          <Box style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
            <Loader size="xl" color="cyan" />
          </Box>
        ) : error ? (
          <Alert icon={<IconAlertCircle size={16} />} title="Hata" color="red" mb="xl">
            {error}
          </Alert>
        ) : (
          <>
            {/* METRICS ROW */}
            <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="lg" mb="xl">
              <Paper withBorder p="xl" radius="md" bg="white" className={classes.metricCardTeal}>
                <Group justify="space-between" mb="xs">
                  <Text size="xs" c="dimmed" fw={700}>TOPLAM KULLANICI</Text>
                  <ThemeIcon color="teal" variant="light" radius="md">
                    <IconUsers size={16} />
                  </ThemeIcon>
                </Group>
                <Text size="xl" fw={900}>{stats?.users}</Text>
              </Paper>

              <Paper withBorder p="xl" radius="md" bg="white" className={classes.metricCardBlue}>
                <Group justify="space-between" mb="xs">
                  <Text size="xs" c="dimmed" fw={700}>ÜNİVERSİTELER</Text>
                  <ThemeIcon color="blue" variant="light" radius="md">
                    <IconSchool size={16} />
                  </ThemeIcon>
                </Group>
                <Text size="xl" fw={900}>{stats?.universities}</Text>
              </Paper>

              <Paper withBorder p="xl" radius="md" bg="white" className={classes.metricCardYellow}>
                <Group justify="space-between" mb="xs">
                  <Text size="xs" c="dimmed" fw={700}>İNDEKSLENEN BELGELER</Text>
                  <ThemeIcon color="yellow" variant="light" radius="md">
                    <IconFileText size={16} />
                  </ThemeIcon>
                </Group>
                <Text size="xl" fw={900}>{stats?.documents}</Text>
              </Paper>

              <Paper withBorder p="xl" radius="md" bg="white" className={classes.metricCardRed}>
                <Group justify="space-between" mb="xs">
                  <Text size="xs" c="dimmed" fw={700}>TOPLAM SOHBET</Text>
                  <ThemeIcon color="red" variant="light" radius="md">
                    <IconMessage size={16} />
                  </ThemeIcon>
                </Group>
                <Text size="xl" fw={900}>{stats?.chat_sessions}</Text>
              </Paper>
            </SimpleGrid>


            {/* BOTTOM ROW */}
            <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="lg">
              {/* Feedback */}
              <Paper withBorder p="xl" radius="md" bg="white" className={classes.feedbackContainer}>
                <Group justify="space-between" mb="xl">
                  <Text fw={700}>Kullanıcı Geri Bildirimleri</Text>
                  <Badge color="cyan" variant="light">{feedbacks.length} Mesaj</Badge>
                </Group>

                <div className={classes.feedbackScrollArea}>
                  {feedbacks.length === 0 ? (
                    <Text size="sm" c="dimmed" ta="center" py="xl">Henüz bir geri bildirim gönderilmedi.</Text>
                  ) : (
                    feedbacks.map((fb, idx) => (
                      <div key={fb.id} style={{ marginBottom: idx === feedbacks.length - 1 ? 0 : '1.5rem' }}>
                        <Group justify="space-between" align="flex-start" mb="xs">
                          <Group>
                            <Avatar color="cyan" radius="xl" size="md">
                              {fb.full_name.split(' ').filter(Boolean).map(n => n[0]).join('').toUpperCase()}
                            </Avatar>
                            <div>
                              <Text size="sm" fw={700}>{fb.full_name}</Text>
                              <Text size="xs" c="dimmed">
                                {new Date(fb.created_at).toLocaleString('tr-TR')}
                              </Text>
                            </div>
                          </Group>
                          <Badge color="blue" variant="light">{fb.email}</Badge>
                        </Group>
                        <Text size="sm" c="dark.6" bg="gray.0" p="sm" className={classes.feedbackMessage}>
                          {fb.message}
                        </Text>
                        {idx !== feedbacks.length - 1 && <Divider mt="md" />}
                      </div>
                    ))
                  )}
                </div>
              </Paper>

              {/* Logs */}
              <Paper withBorder p="xl" radius="md" bg="white">
                <Group justify="space-between" mb="xl">
                  <Text fw={700}>Sistem Logları <Badge size="xs" color="gray" variant="light">Simüle Edildi</Badge></Text>
                  <ActionIcon variant="subtle" color="gray"><IconActivity size={18} /></ActionIcon>
                </Group>

                <Group wrap="nowrap" mb="xl">
                  <ThemeIcon color="gray" variant="outline" radius="xl" size="md" className={classes.logIcon}><IconCheck size={14} color="#343a40" /></ThemeIcon>
                  <div style={{ flex: 1 }}>
                    <Group justify="space-between">
                      <Text size="sm" fw={700}>Crawler Senkronizasyonu</Text>
                      <Text size="xs" c="dimmed">14:22:01</Text>
                    </Group>
                    <Text size="xs" c="dimmed">Kütüphane veritabanı başarıyla güncellendi.</Text>
                  </div>
                </Group>

                <Group wrap="nowrap" mb="xl">
                  <ThemeIcon color="gray" variant="outline" radius="xl" size="md" className={classes.logIcon}><IconAlertCircle size={14} color="#343a40" /></ThemeIcon>
                  <div style={{ flex: 1 }}>
                    <Group justify="space-between">
                      <Text size="sm" fw={700}>Vektör DB Hatası</Text>
                      <Text size="xs" c="dimmed">13:58:45</Text>
                    </Group>
                    <Text size="xs" c="dimmed">Bağlantı zaman aşımına uğradı (Retry #3).</Text>
                  </div>
                </Group>

                <Group wrap="nowrap">
                  <ThemeIcon color="gray" variant="outline" radius="xl" size="md" className={classes.logIcon}><IconInfoCircle size={14} color="#343a40" /></ThemeIcon>
                  <div style={{ flex: 1 }}>
                    <Group justify="space-between">
                      <Text size="sm" fw={700}>Model Embedding Güncellendi</Text>
                      <Text size="xs" c="dimmed">12:10:30</Text>
                    </Group>
                    <Text size="xs" c="dimmed">BERT-base-turkish ağırlıkları yenilendi.</Text>
                  </div>
                </Group>
              </Paper>
            </SimpleGrid>
          </>
        )}
      </AppShell.Main>
    </AppShell>
  );
}
