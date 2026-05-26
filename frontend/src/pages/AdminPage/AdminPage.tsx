import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell, Group, Text, Paper, SimpleGrid, Badge, ThemeIcon, Divider, ActionIcon, Box, Loader, Alert, Avatar, Burger, Table } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconActivity, IconCheck, IconAlertCircle, IconInfoCircle, IconUsers, IconSchool, IconFileText, IconMessage } from '@tabler/icons-react';
import AdminSidebar from '../../components/AdminSidebar/AdminSidebar';
import classes from './AdminPage.module.css';

import { API_BASE_URL } from '../../config';

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

interface SystemLog {
  id: number;
  level: string;
  title: string;
  message: string;
  created_at: string;
}

interface BadFeedback {
  id: number;
  user_question: string;
  ai_response: string;
  comment: string | null;
  created_at: string;
}

const parseUtcDate = (dateStr: string | null | undefined): Date => {
  if (!dateStr) return new Date();
  return new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z');
};

export default function AdminPage() {
  const [opened, { toggle, close }] = useDisclosure(false);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [feedbacks, setFeedbacks] = useState<FeedbackData[]>([]);
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [badFeedbacks, setBadFeedbacks] = useState<BadFeedback[]>([]);
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
      
      // Fetch stats, feedbacks, logs and bad feedbacks
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
        }),
        fetch(`${API_BASE_URL}/admin/logs`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).then(res => {
          if (res.ok) return res.json();
          throw new Error('Sistem logları yüklenirken bir hata oluştu.');
        }),
        fetch(`${API_BASE_URL}/admin/bad-feedbacks`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }).then(res => {
          if (res.ok) return res.json();
          throw new Error('Hatalı yanıt geri bildirimleri yüklenirken bir hata oluştu.');
        })
      ])
        .then(([statsData, feedbacksData, logsData, badFeedbacksData]) => {
          setStats(statsData);
          setFeedbacks(feedbacksData);
          setLogs(logsData);
          setBadFeedbacks(badFeedbacksData);
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
                              {(fb.full_name || 'K').split(' ').filter(Boolean).map(n => n[0]).join('').toUpperCase()}
                            </Avatar>
                            <div>
                              <Text size="sm" fw={700}>{fb.full_name || 'Kullanıcı'}</Text>
                              <Text size="xs" c="dimmed">
                              {parseUtcDate(fb.created_at).toLocaleString('tr-TR')}
                              </Text>
                            </div>
                          </Group>
                          {fb.email && <Badge color="blue" variant="light">{fb.email}</Badge>}
                        </Group>
                        {fb.message && (
                          <Text size="sm" c="dark.6" bg="gray.0" p="sm" className={classes.feedbackMessage}>
                            {fb.message}
                          </Text>
                        )}
                        {idx !== feedbacks.length - 1 && <Divider mt="md" />}
                      </div>
                    ))
                  )}
                </div>
              </Paper>

              {/* Logs */}
              <Paper withBorder p="xl" radius="md" bg="white">
                <Group justify="space-between" mb="xl">
                  <Text fw={700}>Sistem Logları <Badge size="xs" color="teal" variant="light">Canlı</Badge></Text>
                  <ActionIcon variant="subtle" color="gray"><IconActivity size={18} /></ActionIcon>
                </Group>

                {logs.length === 0 ? (
                  <Text size="sm" c="dimmed" ta="center" py="xl">Henüz bir sistem logu bulunmuyor.</Text>
                ) : (
                  logs.map((log, index) => {
                    let Icon = IconInfoCircle;
                    let color = "blue";
                    
                    if (log.level === "error") {
                      Icon = IconAlertCircle;
                      color = "red";
                    } else if (log.level === "warning") {
                      Icon = IconAlertCircle;
                      color = "orange";
                    } else if (log.title === "Crawler Senkronizasyonu" && log.level === "info") {
                      Icon = IconCheck;
                      color = "green";
                    }
                    
                    const logTime = parseUtcDate(log.created_at).toLocaleTimeString('tr-TR', {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit'
                    });

                    return (
                      <Group wrap="nowrap" key={log.id} mb={index !== logs.length - 1 ? "xl" : undefined}>
                        <ThemeIcon color={color} variant="light" radius="xl" size="md">
                          <Icon size={14} />
                        </ThemeIcon>
                        <div style={{ flex: 1 }}>
                          <Group justify="space-between">
                            <Text size="sm" fw={700}>{log.title}</Text>
                            <Text size="xs" c="dimmed">{logTime}</Text>
                          </Group>
                          <Text size="xs" c="dimmed">{log.message}</Text>
                        </div>
                      </Group>
                    );
                  })
                )}
              </Paper>
            </SimpleGrid>

            {/* NEW SECTION: BAD FEEDBACKS TABLE */}
            <Paper withBorder p="xl" radius="md" bg="white" mt="lg">
              <Group justify="space-between" mb="lg">
                <Text fw={700} size="lg">Hatalı Yanıt Geri Bildirimleri (Thumbs Down)</Text>
                <Badge color="red" variant="light">{badFeedbacks.length} Adet</Badge>
              </Group>
              
              {badFeedbacks.length === 0 ? (
                <Text size="sm" c="dimmed" ta="center" py="xl">Henüz olumsuz değerlendirilmiş bir asistan yanıtı yok.</Text>
              ) : (
                <Box style={{ overflowX: 'auto' }}>
                  <Table striped highlightOnHover>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th style={{ minWidth: '220px' }}>Öğrencinin Sorusu</Table.Th>
                        <Table.Th style={{ minWidth: '350px' }}>Yapay Zekanın Cevabı</Table.Th>
                        <Table.Th style={{ minWidth: '220px' }}>Öğrenci Yorumu / Notu</Table.Th>
                        <Table.Th style={{ width: '140px' }}>Tarih</Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {badFeedbacks.map((fb) => (
                        <Table.Tr key={fb.id}>
                          <Table.Td>
                            <Text size="xs" style={{ whiteSpace: 'pre-wrap' }}>{fb.user_question}</Text>
                          </Table.Td>
                          <Table.Td>
                            <Text size="xs" style={{ whiteSpace: 'pre-wrap' }} c="dimmed">{fb.ai_response}</Text>
                          </Table.Td>
                          <Table.Td>
                            {fb.comment ? (
                              <Text size="xs" fw={500} c="red.6">{fb.comment}</Text>
                            ) : (
                              <Text size="xs" c="dimmed" fs="italic">Not eklenmemiş</Text>
                            )}
                          </Table.Td>
                          <Table.Td>
                            <Text size="xs" c="dimmed">
                              {parseUtcDate(fb.created_at).toLocaleDateString('tr-TR')} {parseUtcDate(fb.created_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                            </Text>
                          </Table.Td>
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </Box>
              )}
            </Paper>
          </>
        )}
      </AppShell.Main>
    </AppShell>
  );
}
