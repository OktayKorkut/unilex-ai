import { useState } from 'react';
import { Card, Box, Group, Title, TextInput, Text, Badge } from '@mantine/core';
import { IconHistory, IconSearch } from '@tabler/icons-react';
import classes from '../../pages/ProfilePage/ProfilePage.module.css';

interface ChatSession {
  id: number;
  university_id?: number;
  title?: string | null;
  created_at: string;
}

interface ProfileHistoryListProps {
  sessions: ChatSession[];
  universities: { value: string; label: string }[];
  onOpenChat: (id: number) => void;
}

const parseUtcDate = (dateStr: string | null | undefined): Date => {
  if (!dateStr) return new Date();
  return new Date(dateStr.endsWith('Z') ? dateStr : dateStr + 'Z');
};

export default function ProfileHistoryList({
  sessions,
  universities,
  onOpenChat,
}: ProfileHistoryListProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // Map real sessions to display format
  const formattedChats = sessions.map((session) => {
    const uniName = universities.find((u) => u.value === String(session.university_id))?.label || 'Işık Üniversitesi';
    return {
      id: session.id,
      date: parseUtcDate(session.created_at).toLocaleString('tr-TR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }),
      title: session.title || `Sohbet #${session.id}`,
      description: `${uniName} mevzuatı hakkında RAG tabanlı soru-cevap oturumu.`,
      tags: ['Mevzuat', 'Akademik', uniName.split(' ')[0]],
    };
  });

  const filteredChats = formattedChats.filter((chat) =>
    chat.title.toLocaleLowerCase('tr-TR').includes(searchQuery.toLocaleLowerCase('tr-TR'))
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

    </Card>
  );
}
