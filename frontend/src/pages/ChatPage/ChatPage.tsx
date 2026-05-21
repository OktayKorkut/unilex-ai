import { AppShell, Burger, Group, Text, ScrollArea, TextInput, ActionIcon, Avatar, Paper, Badge, Button, Image, Loader, Stack, Box, Title } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconSend, IconPlus, IconMessageCircle, IconPaperclip, IconHome, IconAlertCircle, IconTrash } from '@tabler/icons-react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useGSAP } from '@gsap/react';
import gsap from 'gsap';
import { useRef, useState, useEffect } from 'react';
import ChatMessage, { type Message } from '../../components/ChatMessage/ChatMessage';
import ChatSourcePanel from '../../components/ChatSourcePanel/ChatSourcePanel';
import classes from './ChatPage.module.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

interface ChatSession {
  id: number;
  university_id?: number;
  created_at: string;
}

export default function ChatPage() {
  const [opened, { toggle, close }] = useDisclosure();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [asideOpened, setAsideOpened] = useState(false);
  const [selectedSource, setSelectedSource] = useState<any | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [searchParams, setSearchParams] = useSearchParams();

  // Track individual message feedback states (like/dislike)
  const [feedbacks, setFeedbacks] = useState<Record<string | number, any>>({});

  const viewportRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Scroll to bottom whenever messages change or typing state changes
  const scrollToBottom = () => {
    if (viewportRef.current) {
      viewportRef.current.scrollTo({
        top: viewportRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Auth check & load sessions
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (!storedToken) {
      navigate('/');
      return;
    }
    setToken(storedToken);
    fetchSessions(storedToken);
  }, [navigate]);

  // Sync active session if URL search parameters change
  useEffect(() => {
    const urlSessionId = searchParams.get('session_id');
    if (urlSessionId && Number(urlSessionId) !== activeSessionId) {
      const numId = Number(urlSessionId);
      if (sessions.some(s => s.id === numId)) {
        selectSession(numId);
      }
    }
  }, [searchParams, sessions, activeSessionId]);

  // Fetch chat sessions
  const fetchSessions = async (authToken: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/chat/sessions`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
        if (data.length > 0) {
          const urlSessionId = searchParams.get('session_id');
          if (urlSessionId && data.some((s: any) => s.id === Number(urlSessionId))) {
            selectSession(Number(urlSessionId), authToken);
          } else {
            selectSession(data[0].id, authToken);
          }
        } else {
          // If no session exists, create a new one automatically
          createNewSession(authToken);
        }
      } else {
        setErrorMsg('Sohbet geçmişi yüklenirken bir sorun oluştu.');
      }
    } catch (err) {
      setErrorMsg('Backend sunucusu ile bağlantı kurulamadı.');
    }
  };

  // Select and load chat session messages
  const selectSession = async (sessionId: number, authToken = token) => {
    if (!authToken) return;
    close();
    setActiveSessionId(sessionId);
    setSearchParams({ session_id: String(sessionId) }, { replace: true });
    setMessages([]);
    setErrorMsg('');

    try {
      const res = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      if (res.ok) {
        const data = await res.json();
        // Backend returns SessionDetailResponse: { id, university_id, created_at, messages }
        // Each message in DB has role: 'user' or 'assistant' (mapped here)
        const formattedMessages = data.messages.map((m: any) => ({
          id: m.id,
          role: m.role === 'assistant' ? 'assistant' : 'user',
          content: m.content,
          created_at: m.created_at,
          sources: m.sources || []
        }));
        setMessages(formattedMessages);
      }
    } catch (err) {
      setErrorMsg('Sohbet içeriği yüklenemedi.');
    }
  };

  // Create a new chat session
  const createNewSession = async (authToken = token) => {
    if (!authToken) return;
    close();
    setErrorMsg('');

    let universityId = null;
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const parsed = JSON.parse(storedUser);
        universityId = parsed.university_id || null;
      } catch (e) {
        console.error('Error parsing user storage:', e);
      }
    }

    try {
      const res = await fetch(`${API_BASE_URL}/chat/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ university_id: universityId })
      });
      if (res.ok) {
        const data = await res.json();
        const newSession: ChatSession = {
          id: data.session_id,
          university_id: data.university_id,
          created_at: data.created_at
        };
        setSessions(prev => [newSession, ...prev]);
        setActiveSessionId(data.session_id);
        setSearchParams({ session_id: String(data.session_id) }, { replace: true });
        setMessages([]);
      }
    } catch (err) {
      setErrorMsg('Yeni sohbet odası oluşturulamadı.');
    }
  };

  // Send message
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || !activeSessionId || !token) return;

    const userQuestion = inputValue.trim();
    setInputValue('');
    setErrorMsg('');

    // 1. Add user message locally
    const userMsgId = Date.now();
    const newUserMsg: Message = {
      id: userMsgId,
      role: 'user',
      content: userQuestion,
      created_at: new Date().toISOString()
    };
    setMessages(prev => [...prev, newUserMsg]);
    setIsTyping(true);

    try {
      // 2. POST to send message
      const res = await fetch(`${API_BASE_URL}/chat/sessions/${activeSessionId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ content: userQuestion })
      });

      if (res.ok) {
        const data = await res.json();
        // Backend returns MessageResponse: { question, answer, university_id, sources }
        const newAiMsg: Message = {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.answer,
          created_at: new Date().toISOString(),
          sources: data.sources // RAG source list
        };
        setMessages(prev => [...prev, newAiMsg]);

        // If the session didn't have a university, it might be dynamically resolved now
        if (data.university_id) {
          setSessions(prev => prev.map(s =>
            s.id === activeSessionId ? { ...s, university_id: data.university_id } : s
          ));
        }
      } else {
        const data = await res.json().catch(() => ({}));
        setErrorMsg(data.detail || 'Cevap üretilirken bir sorun oluştu.');
      }
    } catch (err) {
      setErrorMsg('Bağlantı hatası: Mesaj gönderilemedi.');
    } finally {
      setIsTyping(false);
    }
  };

  const handleThumbUp = (msgId: string | number, e: React.MouseEvent<HTMLButtonElement>) => {
    setFeedbacks(prev => ({
      ...prev,
      [msgId]: prev[msgId] === 'like' ? null : 'like'
    }));
    gsap.to(e.currentTarget, {
      rotationY: '+=360',
      duration: 0.6,
      ease: 'power2.out'
    });
  };

  const handleThumbDown = (msgId: string | number, e: React.MouseEvent<HTMLButtonElement>) => {
    setFeedbacks(prev => ({
      ...prev,
      [msgId]: prev[msgId] === 'dislike' ? null : 'dislike'
    }));
    gsap.to(e.currentTarget, {
      rotationY: '+=360',
      duration: 0.6,
      ease: 'power2.out'
    });
  };

  const handleOpenSource = (source: any) => {
    setSelectedSource(source);
    setAsideOpened(true);
  };

  const handleDeleteSession = async (sessionId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!token) return;

    if (!window.confirm('Bu sohbeti silmek istediğinizden emin misiniz?')) return;

    try {
      const res = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.ok) {
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        if (activeSessionId === sessionId) {
          setMessages([]);
          setActiveSessionId(null);
          setSearchParams({}, { replace: true });
        }
      } else {
        setErrorMsg('Sohbet silinirken bir hata oluştu.');
      }
    } catch (err) {
      setErrorMsg('Sohbet silinemedi.');
    }
  };

  useGSAP(() => {
    if (messages.length > 0) {
      gsap.from('.message-bubble-latest', {
        y: 20,
        opacity: 0,
        duration: 0.4,
        ease: 'power2.out'
      });
    }
  }, [messages.length]);

  return (
    <AppShell
      layout="alt"
      navbar={{
        width: 300,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      aside={{
        width: 350,
        breakpoint: 'lg',
        collapsed: { desktop: !asideOpened, mobile: !asideOpened },
      }}
      padding="0"
      transitionDuration={300}
      transitionTimingFunction="ease"
    >
      {/* LEFT SIDEBAR */}
      <AppShell.Navbar p="md" className={classes.navbar}>
        <Group justify="space-between" mb="xl">
          <Link to="/" style={{ textDecoration: 'none' }}>
            <Group gap="sm">
              <Image src="/logo_gold.png" h={32} w="auto" fit="contain" />
              <Text fw={900} size="lg" c="white">UniLex AI</Text>
            </Group>
          </Link>
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" color="white" />
        </Group>

        <Button
          variant="outline"
          color="cyan"
          fullWidth
          leftSection={<IconPlus size={16} />}
          radius="md"
          className={classes.newChatBtn}
          onClick={() => createNewSession()}
        >
          Yeni Sohbet Başlat
        </Button>

        <Text size="xs" fw={700} c="dimmed" mt="xl" mb="sm" tt="uppercase">
          Sohbet Geçmişi
        </Text>

        <ScrollArea h="calc(100vh - 200px)">
          <Stack gap="xs">
            {sessions.map((s) => (
              <Group
                key={s.id}
                className={`${classes.historyItem} ${s.id === activeSessionId ? classes.historyItemActive : ''}`}
                onClick={() => selectSession(s.id)}
                justify="space-between"
                wrap="nowrap"
                gap="xs"
                p="xs"
              >
                <Group gap="xs" style={{ flex: 1, minWidth: 0 }} wrap="nowrap">
                  <IconMessageCircle size={18} style={{ flexShrink: 0 }} />
                  <Text size="sm" truncate>
                    {`Sohbet #${s.id} (${new Date(s.created_at).toLocaleDateString('tr-TR')})`}
                  </Text>
                </Group>
                <ActionIcon
                  variant="subtle"
                  color="red"
                  size="sm"
                  onClick={(e) => handleDeleteSession(s.id, e)}
                  className="delete-session-btn"
                >
                  <IconTrash size={14} />
                </ActionIcon>
              </Group>
            ))}
          </Stack>
        </ScrollArea>

        {/* Bottom Navigation */}
        <div className={classes.sidebarFooter}>
          <Button
            component={Link}
            to="/"
            variant="subtle"
            color="gray"
            fullWidth
            leftSection={<IconHome size={18} />}
            className={classes.backBtn}
          >
            Ana Sayfaya Dön
          </Button>
        </div>
      </AppShell.Navbar>

      {/* MAIN CHAT AREA */}
      <AppShell.Main className={classes.mainContent}>
        {/* Mobile Header */}
        <Group h={60} px="md" hiddenFrom="sm" className={classes.mobileHeader}>
          <Burger opened={opened} onClick={toggle} size="sm" color="dark" />
          <Text fw={700}>UniLex</Text>
        </Group>

        <ScrollArea className={classes.chatArea} p="xl" viewportRef={viewportRef}>
          {errorMsg && (
            <Paper p="sm" bg="red.0" className={classes.errorAlert} mb="md">
              <Group gap="xs" c="red.7">
                <IconAlertCircle size={18} />
                <Text size="sm" fw={600}>{errorMsg}</Text>
              </Group>
            </Paper>
          )}

          {messages.length === 0 && !isTyping && (
            <Box className={classes.welcomeContainer}>
              <Avatar size={80} color="cyan" radius="xl" mx="auto" mb="xl">
                <IconMessageCircle size={40} />
              </Avatar>
              <Title order={2} c="dark.8" mb="sm">Mevzuat Arama Portalı</Title>
              <Text c="dimmed" maw={500} mx="auto">
                Üniversitelerin akademik yönetmelikleri, yönergeleri ve ÇAP/yatay geçiş kuralları hakkında merak ettiğiniz her şeyi sorabilirsiniz.
              </Text>
            </Box>
          )}

          {messages.map((msg, index) => {
            const isLast = index === messages.length - 1;
            const feedbackVal = feedbacks[msg.id] || null;

            return (
              <ChatMessage
                key={msg.id}
                msg={msg}
                isLatest={isLast}
                feedbackVal={feedbackVal}
                onThumbUp={handleThumbUp}
                onThumbDown={handleThumbDown}
                onOpenSource={handleOpenSource}
              />
            );
          })}

          {/* Typing Indicator */}
          {isTyping && (
            <Group align="flex-start" justify="flex-start" mb="xl" wrap="nowrap">
              <Avatar bg="#0b132b" p={4} radius="xl">
                <Image src="/logo_gold.png" fit="contain" />
              </Avatar>
              <div className={classes.typingWrapper}>
                <Badge color="cyan" variant="light" mb="sm">AI YAZIYOR</Badge>
                <Paper className={classes.aiMessage} radius="lg" p="md" withBorder>
                  <Group gap="xs">
                    <Loader size="xs" color="cyan" type="dots" />
                    <Text size="xs" c="dimmed" fs="italic">Analiz yapılıyor ve cevap oluşturuluyor...</Text>
                  </Group>
                </Paper>
              </div>
            </Group>
          )}
        </ScrollArea>

        {/* Chat Input */}
        <div className={classes.inputWrapper}>
          <Paper withBorder radius="xl" p="xs" shadow="sm" className={classes.inputContainer} component="form" onSubmit={handleSendMessage}>
            <Group wrap="nowrap" gap="xs">
              <ActionIcon variant="subtle" color="gray" size="lg" radius="xl">
                <IconPaperclip size={20} />
              </ActionIcon>
              <TextInput
                placeholder="Mevzuat kuralları, yönetmelikler veya burs şartları hakkında sorun..."
                variant="unstyled"
                style={{ flex: 1 }}
                size="md"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isTyping}
                styles={{
                  input: {
                    color: '#1a1b1e',
                    fontWeight: 500,
                  }
                }}
              />
              <ActionIcon color="cyan" size="lg" radius="xl" variant="filled" type="submit" disabled={!inputValue.trim() || isTyping}>
                <IconSend size={18} />
              </ActionIcon>
            </Group>
          </Paper>
        </div>
      </AppShell.Main>

      {/* RIGHT SIDEBAR - SOURCE DETAILS */}
      <ChatSourcePanel
        selectedSource={selectedSource}
        onClose={() => setAsideOpened(false)}
      />
    </AppShell>
  );
}
