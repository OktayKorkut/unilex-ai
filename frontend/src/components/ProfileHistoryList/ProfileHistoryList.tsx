import { useState } from 'react';
import { Card, Box, Group, Title, TextInput, Text, Badge, Progress } from '@mantine/core';
import { IconHistory, IconSearch, IconCpu } from '@tabler/icons-react';
import classes from '../../pages/ProfilePage/ProfilePage.module.css';

interface ChatSession {
  id: number;
  university_id?: number;
  created_at: string;
}

interface ProfileHistoryListProps {
  sessions: ChatSession[];
  universities: { value: string; label: string }[];
  onOpenChat: (id: number) => void;
  usedQueries: number;
  capacityPercent: number;
}

export default function ProfileHistoryList({
  sessions,
  universities,
  onOpenChat,
  usedQueries,
  capacityPercent,
}: ProfileHistoryListProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // Map real sessions to display format
  const formattedChats = sessions.map((session) => {
    const uniName = universities.find((u) => u.value === String(session.university_id))?.label || 'Işık Üniversitesi';
    return {
      id: session.id,
      date: new Date(session.created_at).toLocaleString('tr-TR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }),
      title: `Sohbet #${session.id}`,
      description: `${uniName} mevzuatı hakkında RAG tabanlı soru-cevap oturumu.`,
      tags: ['Mevzuat', 'Akademik', uniName.split(' ')[0]],
    };
  });

  const filteredChats = formattedChats.filter(
    (chat) =>
      chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      chat.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      chat.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <Card radius="lg" p="xl" className={`${classes.glassCard} ${classes.historyContainer}`} h="100%">
      <Box>
        <Group justify="space-between" mb="xl">
          <Title order={3} c="white" className={classes.flexCenterGap}>
            <IconHistory size={24} color="#00bcd4" />
            Sohbet Geçmişi
          </Title>
          <Group gap="sm">
            <TextInput
              placeholder="Geçmişte ara..."
              leftSection={<IconSearch size={16} color="gray" />}
              size="sm"
              radius="xl"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              bg="rgba(0,0,0,0.2)"
              classNames={{
                input: classes.formInput
              }}
              styles={{
                input: {
                  backgroundColor: 'transparent !important',
                  border: '1px solid rgba(255,255,255,0.05) !important',
                  color: 'white',
                  '&:focus': {
                    borderColor: '#00bcd4 !important',
                  },
                },
              }}
            />
          </Group>
        </Group>

        {/* List of Chats */}
        <Box mt="xl">
          {filteredChats.length > 0 ? (
            filteredChats.map((chat) => (
              <Box key={chat.id} className={classes.chatItem}>
                <Text size="xs" c="dimmed" mb={5} className={classes.monoFont}>
                  {chat.date}
                </Text>
                <Title
                  order={4}
                  c="white"
                  mb="sm"
                  style={{ cursor: 'pointer', transition: 'color 0.2s' }}
                  className={classes.hoverCyan}
                  onClick={() => onOpenChat(chat.id)}
                >
                  {chat.title}
                </Title>
                <Text c="gray.4" size="sm" mb="md">
                  {chat.description}
                </Text>
                <Group gap="xs">
                  {chat.tags.map((tag) => (
                    <Badge
                      key={tag}
                      variant="light"
                      color="cyan"
                      radius="sm"
                      size="sm"
                      bg="rgba(0, 188, 212, 0.08)"
                    >
                      {tag}
                    </Badge>
                  ))}
                </Group>
              </Box>
            ))
          ) : (
            <Box className={classes.emptyHistory}>
              <Text c="dimmed">Aradığınız kriterlere uygun sohbet geçmişi bulunamadı.</Text>
            </Box>
          )}
        </Box>
      </Box>

      {/* Progress Capacity at the very bottom */}
      <Box className={classes.capacityContainer}>
        <Group justify="space-between" mb="xs">
          <Text size="sm" fw={600} c="white" className={classes.capacityTitle}>
            <IconCpu size={16} color="#00bcd4" />
            Haftalık Analiz Kapasitesi
          </Text>
          <Text size="sm" fw={700} c="cyan" className={classes.monoFont}>
            {usedQueries} / 50 Sorgu Kullanıldı ({capacityPercent}%)
          </Text>
        </Group>
        <Progress
          value={capacityPercent}
          color="cyan"
          size="md"
          radius="xl"
          bg="rgba(255,255,255,0.05)"
          className={classes.glowBar}
        />
      </Box>
    </Card>
  );
}
