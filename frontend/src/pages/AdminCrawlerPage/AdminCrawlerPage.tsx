import { AppShell, Group, Text, Paper, Badge, ThemeIcon, ActionIcon, Button, Stack, Container, Progress, Select, Box, Loader, Alert } from '@mantine/core';
import { IconSpider, IconSearch, IconBell, IconUpload, IconFileText, IconRefresh, IconAlertCircle, IconServer } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import AdminSidebar from '../../components/AdminSidebar/AdminSidebar';
import classes from './AdminCrawlerPage.module.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

interface UniversityOption {
  value: string;
  label: string;
}

interface CrawlStatusResponse {
  university_id: number;
  name: string;
  crawl_status: 'idle' | 'running' | 'done' | 'error';
  is_crawled: boolean;
  crawled_at: string | null;
  document_count: number;
  crawl_error: string | null;
}

export default function AdminCrawlerPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [universities, setUniversities] = useState<UniversityOption[]>([]);
  const [selectedUni, setSelectedUni] = useState<string | null>(null);
  const [crawlStatus, setCrawlStatus] = useState<CrawlStatusResponse | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [embedLoading, setEmbedLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{ type: 'success' | 'error' | null; message: string }>({ type: null, message: '' });

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

      // Fetch universities for select dropdown
      fetch(`${API_BASE_URL}/universities`)
        .then(res => res.json())
        .then(data => {
          const list = data.map((uni: any) => ({
            value: String(uni.id),
            label: uni.name
          }));
          setUniversities(list);
          if (list.length > 0) {
            setSelectedUni(list[0].value);
          }
        })
        .catch(err => console.error('Error fetching universities:', err));

    } catch (e) {
      navigate('/');
    }
  }, [navigate]);

  const fetchCrawlStatus = async (uniId: string) => {
    const token = localStorage.getItem('token');
    if (!token) return;
    setStatusLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/universities/${uniId}/crawl-status`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setCrawlStatus(data);
      }
    } catch (err) {
      console.error('Error fetching crawl status:', err);
    } finally {
      setStatusLoading(false);
    }
  };

  useEffect(() => {
    if (selectedUni) {
      fetchCrawlStatus(selectedUni);
    } else {
      setCrawlStatus(null);
    }
  }, [selectedUni]);

  // Polling if crawl is running
  useEffect(() => {
    if (crawlStatus?.crawl_status === 'running' && selectedUni) {
      const timer = setInterval(() => {
        const token = localStorage.getItem('token');
        if (!token) return;
        fetch(`${API_BASE_URL}/universities/${selectedUni}/crawl-status`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
          .then(res => {
            if (res.ok) return res.json();
            throw new Error();
          })
          .then(data => {
            setCrawlStatus(data);
          })
          .catch(() => {});
      }, 3000);
      return () => clearInterval(timer);
    }
  }, [crawlStatus?.crawl_status, selectedUni]);

  const handleStartCrawl = async () => {
    if (!selectedUni) return;
    const token = localStorage.getItem('token');
    if (!token) return;

    setTriggerLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/universities/${selectedUni}/crawl`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        fetchCrawlStatus(selectedUni);
      } else {
        const errData = await res.json();
        alert(errData.detail || 'Crawl başlatılamadı.');
      }
    } catch (err) {
      alert('Sunucu ile bağlantı kurulamadı.');
    } finally {
      setTriggerLoading(false);
    }
  };

  const handleStartEmbed = async () => {
    if (!selectedUni) return;
    const token = localStorage.getItem('token');
    if (!token) return;

    setEmbedLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/universities/${selectedUni}/embed`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        alert('Vektör çıkarma işlemi arka planda başlatıldı.');
      } else {
        const errData = await res.json();
        alert(errData.detail || 'Embed işlemi başlatılamadı.');
      }
    } catch (err) {
      alert('Sunucu ile bağlantı kurulamadı.');
    } finally {
      setEmbedLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setUploadedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setUploadedFile(e.target.files[0]);
    }
  };

  const handleUploadClick = () => {
    setUploadStatus({
      type: 'error',
      message: 'PDF yükleme servisi backend entegrasyonu sonrasında aktif olacaktır. Mevcut backend sürümü doğrudan web tarama (crawler) altyapısını desteklemektedir.'
    });
    // Auto-clear upload notification after 6 seconds
    setTimeout(() => {
      setUploadStatus({ type: null, message: '' });
    }, 6000);
  };

  return (
    <AppShell
      navbar={{ width: 280, breakpoint: 'sm' }}
      padding="xl"
      bg="gray.0"
    >
      {/* SIDEBAR Component */}
      <AdminSidebar activePage="crawler" />

      <AppShell.Main>
        {/* HEADER */}
        <Group justify="space-between" mb="xl">
          <Group>
            <Text size="xl" fw={800}>Doküman Yükleme & Crawler</Text>
            <Badge color="cyan" variant="light" size="lg" radius="sm">RAG Eğitim Modülü</Badge>
          </Group>
          <Group>
            <ActionIcon variant="light" color="gray" size="lg" radius="md"><IconSearch size={20} /></ActionIcon>
            <ActionIcon variant="light" color="gray" size="lg" radius="md"><IconBell size={20} /></ActionIcon>
          </Group>
        </Group>

        <Container className={classes.container}>
          {/* UNIVERSITY SELECTOR */}
          <Paper withBorder p="xl" radius="md" bg="white" shadow="sm" mb="xl">
            <Text fw={700} size="lg" mb="xs">Yönetilecek Kampüs / Üniversite Seçimi</Text>
            <Text c="dimmed" size="sm" mb="md">
              Veri tarama ve indeksleme işlemlerini yürütmek istediğiniz kurumu seçin.
            </Text>
            <Select
              placeholder="Üniversite seçin"
              data={universities}
              value={selectedUni}
              onChange={(val) => setSelectedUni(val)}
              classNames={{ input: classes.uniSelect }}
            />
          </Paper>

          {/* PDF UPLOAD SECTION */}
          <Paper withBorder p="xl" radius="md" bg="white" shadow="sm" mb="xl">
            <Text fw={700} size="lg" mb="sm">Yeni Yönetmelik / PDF Yükle</Text>
            <Text c="dimmed" size="sm" mb="xl">
              Yapay zekanın (Asistan) öğrenmesini istediğiniz PDF formatındaki yönetmelikleri veya iç yazışmaları buraya yükleyin.
            </Text>

            {uploadStatus.type && (
              <Alert icon={<IconAlertCircle size={16} />} title="Entegrasyon Uyarısı" color="red" mb="md">
                {uploadStatus.message}
              </Alert>
            )}

            {/* DRAG AND DROP ZONE */}
            <div
              onClick={handleUploadClick}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`${classes.dragZone} ${isDragging ? classes.dragZoneDragging : ''}`}
            >
              <input 
                ref={fileInputRef}
                type="file" 
                accept=".pdf" 
                onChange={handleFileSelect} 
                className={classes.hiddenInput}
              />
              
              {!uploadedFile ? (
                <Stack align="center" gap="xs">
                  <ThemeIcon size={50} radius="xl" color="gray" variant="light">
                    <IconUpload size={24} />
                  </ThemeIcon>
                  <Text fw={700} size="md">PDF Dosyasını Buraya Sürükleyin</Text>
                  <Text size="xs" c="dimmed">veya bilgisayarınızdan seçmek için tıklayın</Text>
                  <Badge color="gray" variant="outline" mt="xs">Maksimum 50 MB</Badge>
                </Stack>
              ) : (
                <Stack align="center" gap="xs">
                  <ThemeIcon size={50} radius="xl" color="cyan" variant="light">
                    <IconFileText size={24} />
                  </ThemeIcon>
                  <Text fw={700} size="md" c="dark">{uploadedFile.name}</Text>
                  <Text size="xs" c="dimmed">{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</Text>
                  <Button mt="xs" color="cyan" size="sm" onClick={(e) => { e.stopPropagation(); handleUploadClick(); }} leftSection={<IconRefresh size={14} />}>Sisteme Yükle ve Tara</Button>
                </Stack>
              )}
            </div>
          </Paper>

          {/* ACTIVE CRAWLER STATUS */}
          <Paper withBorder p="xl" radius="md" bg="white" shadow="sm">
            <Group justify="space-between" mb="lg">
              <div>
                <Text fw={700} size="lg">Otomatik Web Tarayıcı (Web Crawler)</Text>
                <Text size="xs" c="dimmed">Seçili üniversitenin mevzuat web sayfasını otomatik olarak tarar.</Text>
              </div>
              {statusLoading ? (
                <Loader size="xs" />
              ) : crawlStatus ? (
                <Badge 
                  color={
                    crawlStatus.crawl_status === 'running' ? 'yellow' :
                    crawlStatus.crawl_status === 'done' ? 'teal' :
                    crawlStatus.crawl_status === 'error' ? 'red' : 'gray'
                  } 
                  variant="light"
                >
                  {
                    crawlStatus.crawl_status === 'running' ? 'Tarama Sürüyor' :
                    crawlStatus.crawl_status === 'done' ? 'Tamamlandı' :
                    crawlStatus.crawl_status === 'error' ? 'Hata' : 'Hazır'
                  }
                </Badge>
              ) : (
                <Badge color="gray" variant="light">Durum Bilinmiyor</Badge>
              )}
            </Group>

            {crawlStatus && (
              <Stack gap="md">
                <Box>
                  <Text size="sm" fw={600}>Mevcut İndeks Durumu:</Text>
                  <Text size="xs" c="dimmed">
                    Veritabanında <strong>{crawlStatus.document_count} adet</strong> doküman/yönetmelik kayıtlı.
                  </Text>
                  {crawlStatus.crawled_at && (
                    <Text size="xs" c="dimmed">
                      Son Başarılı Tarama: {new Date(crawlStatus.crawled_at).toLocaleString('tr-TR')}
                    </Text>
                  )}
                  {crawlStatus.crawl_error && (
                    <Alert icon={<IconAlertCircle size={16} />} color="red" title="Tarayıcı Hatası" mt="sm">
                      {crawlStatus.crawl_error}
                    </Alert>
                  )}
                </Box>

                {crawlStatus.crawl_status === 'running' && (
                  <Box>
                    <Group justify="space-between" mb="xs">
                      <Text size="xs" fw={700} c="yellow">Web sayfaları taranıyor ve metinler çıkarılıyor...</Text>
                      <Loader size="xs" color="yellow" variant="dots" />
                    </Group>
                    <Progress value={100} color="yellow" size="sm" striped animated />
                  </Box>
                )}

                <Group gap="md" mt="sm">
                  <Button 
                    color="teal" 
                    onClick={handleStartCrawl} 
                    loading={triggerLoading}
                    disabled={crawlStatus.crawl_status === 'running' || statusLoading}
                    leftSection={<IconSpider size={16} />}
                  >
                    Tarayıcıyı Başlat (Crawl)
                  </Button>
                  <Button 
                    color="blue" 
                    variant="outline"
                    onClick={handleStartEmbed} 
                    loading={embedLoading}
                    disabled={crawlStatus.crawl_status === 'running' || statusLoading}
                    leftSection={<IconServer size={16} />}
                  >
                    Vektörleri Yeniden Çıkar (Embed)
                  </Button>
                </Group>
              </Stack>
            )}
          </Paper>
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}
