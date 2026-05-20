import { AppShell, Group, Text, Paper, Badge, ThemeIcon, Button, Stack, Container, SimpleGrid, RingProgress, Alert, Loader } from '@mantine/core';
import { IconDatabase, IconActivity, IconRefresh, IconAlertCircle, IconCheck, IconServer } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import AdminSidebar from '../../components/AdminSidebar/AdminSidebar';
import classes from './AdminHealthPage.module.css';

const HEALTH_URL = 'http://localhost:8000/health';

interface HealthStatus {
  status: string;
  postgres: string;
  qdrant: string;
  app: string;
  latencyMs?: number;
}

export default function AdminHealthPage() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealthStatus = async () => {
    setLoading(true);
    setError(null);
    const startTime = performance.now();
    try {
      const res = await fetch(HEALTH_URL);
      const endTime = performance.now();
      if (!res.ok) {
        throw new Error('Sistem sağlığı verisi alınamadı.');
      }
      const data = await res.json();
      setHealth({
        ...data,
        latencyMs: Math.round(endTime - startTime)
      });
    } catch (err: any) {
      setError(err.message || 'Sunucuya bağlanılamadı.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (!userData) {
      navigate('/');
      return;
    }
    try {
      const parsed = JSON.parse(userData);
      const isAdminUser = parsed.is_admin || parsed.email?.startsWith('admin');
      if (!isAdminUser) {
        navigate('/');
        return;
      }
    } catch (e) {
      navigate('/');
      return;
    }

    fetchHealthStatus();
  }, [navigate]);

  return (
    <AppShell
      navbar={{ width: 280, breakpoint: 'sm' }}
      padding="xl"
      bg="gray.0"
    >
      {/* SIDEBAR Component */}
      <AdminSidebar activePage="health" />

      <AppShell.Main>
        {/* HEADER */}
        <Group justify="space-between" mb="xl">
          <Group>
            <Text size="xl" fw={800}>Sistem Sağlığı & Durumu</Text>
            <Badge color="cyan" variant="light" size="lg" radius="sm">Canlı Sunucu Bağlantısı</Badge>
          </Group>
          <Group>
            <Button 
              variant="light" 
              color="cyan" 
              onClick={fetchHealthStatus} 
              loading={loading}
              leftSection={<IconRefresh size={16} />}
            >
              Yenile
            </Button>
          </Group>
        </Group>

        <Container className={classes.container}>
          {error && (
            <Alert icon={<IconAlertCircle size={16} />} title="Bağlantı Hatası" color="red" mb="xl">
              Sistem sağlığı bilgileri alınırken hata oluştu. Lütfen backend sunucunuzun (Port 8000) çalışır durumda olduğunu kontrol edin. Hata: {error}
            </Alert>
          )}

          {loading && !health ? (
            <Stack align="center" py="xl">
              <Loader size="lg" color="cyan" />
              <Text size="sm" c="dimmed">Sunucu durum bilgisi sorgulanıyor...</Text>
            </Stack>
          ) : (
            health && (
              <Stack gap="xl">
                {/* OVERALL STATUS CARD */}
                <Paper withBorder p="xl" radius="md" bg="white" shadow="sm">
                  <Group justify="space-between" align="center">
                    <div>
                      <Text size="lg" fw={800}>Genel Sistem Durumu</Text>
                      <Text size="sm" c="dimmed">Tüm kritik servislerin anlık çalışma performansı ve bağlantıları.</Text>
                    </div>
                    <RingProgress
                      size={80}
                      roundCaps
                      thickness={8}
                      sections={[{ value: 100, color: health.status === 'ok' ? 'teal' : 'red' }]}
                      label={
                        <Stack align="center" gap={0}>
                          {health.status === 'ok' ? (
                            <IconCheck size={24} color="#0ca678" />
                          ) : (
                            <IconAlertCircle size={24} color="#f03e3e" />
                          )}
                        </Stack>
                      }
                    />
                  </Group>
                </Paper>

                {/* DB & SERVICE METRICS */}
                <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="lg">
                  {/* POSTGRES CARD */}
                  <Paper withBorder p="xl" radius="md" bg="white" shadow="sm" className={classes.dbCard}>
                    <div className={`${classes.statusBar} ${health.postgres === 'connected' ? classes.statusBarConnected : classes.statusBarDisconnected}`} />
                    <Group justify="space-between" mb="lg">
                      <Group gap="sm">
                        <ThemeIcon size="lg" radius="md" color={health.postgres === 'connected' ? 'teal' : 'red'} variant="light">
                          <IconDatabase size={20} />
                        </ThemeIcon>
                        <div>
                          <Text fw={700}>PostgreSQL</Text>
                          <Text size="xs" c="dimmed">İlişkisel Veritabanı</Text>
                        </div>
                      </Group>
                      <Badge color={health.postgres === 'connected' ? 'teal' : 'red'} variant="light">
                        {health.postgres === 'connected' ? 'Bağlı' : 'Bağlantı Yok'}
                      </Badge>
                    </Group>
                    <Text size="sm" c="dimmed">
                      Kullanıcı hesapları, üniversite tanımları ve sohbet geçmişleri bu veritabanında depolanmaktadır.
                    </Text>
                  </Paper>

                  {/* QDRANT VECTOR DB CARD */}
                  <Paper withBorder p="xl" radius="md" bg="white" shadow="sm" className={classes.dbCard}>
                    <div className={`${classes.statusBar} ${health.qdrant === 'connected' ? classes.statusBarConnected : classes.statusBarDisconnected}`} />
                    <Group justify="space-between" mb="lg">
                      <Group gap="sm">
                        <ThemeIcon size="lg" radius="md" color={health.qdrant === 'connected' ? 'teal' : 'red'} variant="light">
                          <IconServer size={20} />
                        </ThemeIcon>
                        <div>
                          <Text fw={700}>Qdrant Vector DB</Text>
                          <Text size="xs" c="dimmed">Vektör Tabanlı Arama Motoru</Text>
                        </div>
                      </Group>
                      <Badge color={health.qdrant === 'connected' ? 'teal' : 'red'} variant="light">
                        {health.qdrant === 'connected' ? 'Bağlı' : 'Bağlantı Yok'}
                      </Badge>
                    </Group>
                    <Text size="sm" c="dimmed">
                      Mevzuat belgelerinin anlamsal (semantic) vektör eşleşmeleri ve RAG aramaları bu motor üzerinde çalışmaktadır.
                    </Text>
                  </Paper>
                </SimpleGrid>

                {/* APP CONFIGURATION & SYSTEM METRICS */}
                <Paper withBorder p="xl" radius="md" bg="white" shadow="sm">
                  <Text fw={700} size="lg" mb="md">Uygulama & Sunucu Bilgileri</Text>
                  <Stack gap="sm">
                    <Group justify="space-between" className={classes.infoRow}>
                      <Text size="sm" fw={600}>Uygulama Adı</Text>
                      <Text size="sm" c="dimmed">{health.app}</Text>
                    </Group>
                    <Group justify="space-between" className={classes.infoRow}>
                      <Text size="sm" fw={600}>API Yanıt Gecikmesi</Text>
                      <Group gap="xs">
                        <ThemeIcon size="xs" color="teal" variant="light"><IconActivity size={10} /></ThemeIcon>
                        <Text size="sm" c="dimmed">{health.latencyMs} ms</Text>
                      </Group>
                    </Group>
                    <Group justify="space-between">
                      <Text size="sm" fw={600}>API Host Ortamı</Text>
                      <Text size="sm" c="dimmed">Localhost (Python FastAPI)</Text>
                    </Group>
                  </Stack>
                </Paper>
              </Stack>
            )
          )}
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}
