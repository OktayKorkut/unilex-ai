import React from 'react';
import { Group, Text, Avatar, Paper, Badge, ThemeIcon, Image, Stack, ActionIcon } from '@mantine/core';
import { IconPaperclip, IconChevronRight, IconThumbUp, IconThumbDown, IconUser } from '@tabler/icons-react';
import classes from './ChatMessage.module.css';

export interface Message {
  id: string | number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  sources?: any[];
}

interface ChatMessageProps {
  msg: Message;
  isLatest: boolean;
  feedbackVal: 'like' | 'dislike' | null;
  onThumbUp: (msgId: string | number, e: React.MouseEvent<HTMLButtonElement>) => void;
  onThumbDown: (msgId: string | number, e: React.MouseEvent<HTMLButtonElement>) => void;
  onOpenSource: (source: any) => void;
}

export default function ChatMessage({
  msg,
  isLatest,
  feedbackVal,
  onThumbUp,
  onThumbDown,
  onOpenSource,
}: ChatMessageProps) {
  const isAssistant = msg.role === 'assistant';

  return (
    <Group
      align="flex-start"
      justify={isAssistant ? 'flex-start' : 'flex-end'}
      className={`${classes.messageBubble} ${isLatest ? 'message-bubble-latest' : ''}`}
      wrap="nowrap"
    >
      {isAssistant && (
        <Avatar bg="#0b132b" p={4} radius="xl">
          <Image src="/logo_gold.png" fit="contain" />
        </Avatar>
      )}

      <div
        className={`${classes.messageBody} ${
          isAssistant ? classes.messageBodyAi : classes.messageBodyUser
        }`}
      >
        {isAssistant && (
          <Badge color="cyan" variant="light" mb="sm">
            AI ASİSTAN
          </Badge>
        )}

        <Paper
          className={isAssistant ? classes.aiMessage : classes.userMessage}
          radius="lg"
          p="md"
          withBorder={isAssistant}
        >
          <Text className={classes.messageText}>{msg.content}</Text>

          {/* Source References */}
          {isAssistant && msg.sources && msg.sources.length > 0 && (
            <Stack gap="xs" mt="xl">
              <Text size="xs" fw={700} c="dimmed">
                ATIFTA BULUNULAN DÖKÜMANLAR:
              </Text>
              {msg.sources.map((src, i) => (
                <Paper
                  key={i}
                  withBorder
                  p="sm"
                  radius="md"
                  className={classes.sourceCard}
                  onClick={() => onOpenSource(src)}
                >
                  <Group justify="space-between" wrap="nowrap">
                    <Group gap="xs" wrap="nowrap">
                      <ThemeIcon color="cyan" variant="light" size="sm">
                        <IconPaperclip size={14} />
                      </ThemeIcon>
                      <div>
                        <Text size="xs" fw={700} truncate>
                          {src.title || 'Mevzuat Dökümanı'}
                        </Text>
                        <Text size="10px" c="dimmed">
                          Güven Skoru: {Math.round(src.score * 100)}%
                        </Text>
                      </div>
                    </Group>
                    <IconChevronRight size={14} color="gray" />
                  </Group>
                </Paper>
              ))}
            </Stack>
          )}

          {/* Feedback Section */}
          {isAssistant && (
            <Group justify="space-between" className={classes.feedbackSection}>
              <Text size="xs" c="dark.4" fw={600}>
                Bu yanıt yardımcı oldu mu?
              </Text>
              <Group gap="xs">
                <ActionIcon
                  variant={feedbackVal === 'like' ? 'filled' : 'light'}
                  color={feedbackVal === 'like' ? '#20c997' : '#d4af37'}
                  size="md"
                  radius="md"
                  onClick={(e) => onThumbUp(msg.id, e)}
                  className={classes.feedbackBtn}
                >
                  <IconThumbUp size={16} />
                </ActionIcon>
                <ActionIcon
                  variant={feedbackVal === 'dislike' ? 'filled' : 'light'}
                  color={feedbackVal === 'dislike' ? '#c92a2a' : '#d4af37'}
                  size="md"
                  radius="md"
                  onClick={(e) => onThumbDown(msg.id, e)}
                  className={classes.feedbackBtn}
                >
                  <IconThumbDown size={16} />
                </ActionIcon>
              </Group>
            </Group>
          )}
        </Paper>
      </div>

      {!isAssistant && (
        <Avatar color="cyan" radius="xl">
          <IconUser size={20} />
        </Avatar>
      )}
    </Group>
  );
}
