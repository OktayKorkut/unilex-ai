import { AppShell, ScrollArea, Group, Text, ActionIcon, Paper, Divider, Badge, Button, Box } from '@mantine/core';
import { IconPaperclip, IconDownload } from '@tabler/icons-react';
import classes from './ChatSourcePanel.module.css';

interface Source {
  id?: string;
  title?: string;
  score: number;
  text: string;
  source_url?: string;
}

interface ChatSourcePanelProps {
  selectedSource: Source | null;
  onClose: () => void;
}

export default function ChatSourcePanel({ selectedSource, onClose }: ChatSourcePanelProps) {
  return (
    <AppShell.Aside className={classes.aside}>
      {selectedSource ? (
        <ScrollArea h="100vh" p="xl">
          <Group justify="space-between" mb="xl">
            <Text fw={800} tt="uppercase" size="xs" c="dark.8">
              ATIF METNİ & DETAYLAR
            </Text>
            <ActionIcon variant="light" color="cyan" size="sm" onClick={onClose}>
              <Text size="xs" fw={900}>✕</Text>
            </ActionIcon>
          </Group>

          <Text size="xs" c="dimmed" mb="xs">
            Güven Skoru
          </Text>
          <Group justify="space-between" align="flex-end" mb="xs">
            <Text size="xl" fw={900} c="cyan">
              {Math.round(selectedSource.score * 100)}%
            </Text>
          </Group>
          <div className={classes.progressBar}>
            <div
              className={classes.progressFill}
              style={{ width: `${selectedSource.score * 100}%` }}
            ></div>
          </div>

          <Group grow mt="xl" mb="xl">
            <Paper withBorder p="sm" radius="md" bg="white">
              <Text size="10px" c="dimmed">
                Alaka Derecesi
              </Text>
              <Text fw={700} size="xs" c={selectedSource.score > 0.7 ? 'green.7' : 'orange.7'}>
                {selectedSource.score > 0.7 ? 'Çok Yüksek' : 'Orta'}
              </Text>
            </Paper>
            <Paper withBorder p="sm" radius="md" bg="white">
              <Text size="10px" c="dimmed">
                Kaynak Türü
              </Text>
              <Text fw={700} size="xs">
                Mevzuat Dökümanı
              </Text>
            </Paper>
          </Group>

          <Divider my="xl" />

          <Group gap="xs" mb="md">
            <IconPaperclip size={16} color="gray" />
            <Text fw={700} size="sm">
              DÖKÜMAN KESİTİ
            </Text>
          </Group>
          <Paper bg="gray.0" p="md" radius="md">
            <Text size="sm" fs="italic" c="dark.7" className={classes.citationText}>
              "{selectedSource.text}"
            </Text>
          </Paper>

          <Divider my="xl" />

          <Text fw={700} size="xs" mb="md">
            META VERİLER
          </Text>
          <Group justify="space-between" mb="xs">
            <Text size="xs" c="dimmed">Döküman Adı:</Text>
            <Text size="xs" fw={700} className={classes.metaValue}>
              {selectedSource.title}
            </Text>
          </Group>
          <Group justify="space-between" mb="xs">
            <Text size="xs" c="dimmed">Vektör ID:</Text>
            <Text size="xs" fw={500}>
              {selectedSource.id ? selectedSource.id.substring(0, 8) + '...' : 'Otomatik'}
            </Text>
          </Group>
          <Group justify="space-between" mb="xl">
            <Text size="xs" c="dimmed">Erişim Durumu:</Text>
            <Badge size="xs" color="cyan" variant="light">
              PUBLIC
            </Badge>
          </Group>

          {selectedSource.source_url && (
            <Button
              fullWidth
              variant="outline"
              color="cyan"
              leftSection={<IconDownload size={16} />}
              mt="xl"
              component="a"
              href={selectedSource.source_url}
              target="_blank"
            >
              Orjinal Dökümana Git
            </Button>
          )}
        </ScrollArea>
      ) : (
        <ScrollArea h="100vh" p="xl">
          <Box className={classes.emptyText}>
            <Text c="dimmed">Detayları görmek için atıf kartına tıklayın.</Text>
          </Box>
        </ScrollArea>
      )}
    </AppShell.Aside>
  );
}
