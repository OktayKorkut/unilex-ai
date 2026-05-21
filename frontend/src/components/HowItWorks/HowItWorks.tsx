import {
  Box,
  Container,
  Title,
  Text,
  Grid,
  Paper,
  Avatar,
  Group,
  Badge,
  ThemeIcon,
} from "@mantine/core";
import { IconUser, IconRobot, IconCheck } from "@tabler/icons-react";
import classes from "./HowItWorks.module.css";

export default function HowItWorks() {
  return (
    <Box className={classes.wrapper}>
      <Container size="xl">
        <Grid align="center">
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Title order={2} className={classes.title}>
              Saniyeler İçinde Sonuç Alın
            </Title>
            <Text c="dimmed" size="lg" mb="xl">
              Yüzlerce sayfalık yönetmelikleri okumanıza gerek yok. Sorunuzu
              sorun, UniLex sizin için en doğru kaynağı bulup sentezlesin.
            </Text>

            <div className={classes.step}>
              <ThemeIcon size={40} radius="xl" color="cyan" variant="light">
                1
              </ThemeIcon>
              <div>
                <Text fw={700} size="lg">
                  Sorunuzu İletin
                </Text>
                <Text c="dimmed">
                  Akademik veya idari herhangi bir konuda doğal dille sorunuzu
                  sorun.
                </Text>
              </div>
            </div>

            <div className={classes.step}>
              <ThemeIcon size={40} radius="xl" color="grape" variant="light">
                2
              </ThemeIcon>
              <div>
                <Text fw={700} size="lg">
                  Semantik Tarama
                </Text>
                <Text c="dimmed">
                  Yapay zeka, tüm üniversite veritabanında bağlamsal arama
                  yapar.
                </Text>
              </div>
            </div>

            <div className={classes.step}>
              <ThemeIcon size={40} radius="xl" color="teal" variant="light">
                3
              </ThemeIcon>
              <div>
                <Text fw={700} size="lg">
                  Kanıtlı Cevap
                </Text>
                <Text c="dimmed">
                  Yanıt, tamamen resmi yönetmelik maddelerine dayandırılarak
                  sunulur.
                </Text>
              </div>
            </div>
          </Grid.Col>

          <Grid.Col span={{ base: 12, md: 6 }}>
            <Paper shadow="xl" radius="lg" p="xl" className={classes.mockup}>
              {/* User Message */}
              <Group align="flex-start" justify="flex-end" mb="xl">
                <Paper
                  bg="cyan.1"
                  p="sm"
                  radius="md"
                  className={classes.userBubble}
                >
                  <Text size="sm">
                    Çift Anadal (ÇAP) yapmak için not ortalamam en az kaç
                    olmalı?
                  </Text>
                </Paper>
                <Avatar color="cyan" radius="xl">
                  <IconUser size={20} />
                </Avatar>
              </Group>

              {/* Bot Message */}
              <Group align="flex-start" mb="md">
                <Avatar color="grape" radius="xl">
                  <IconRobot size={20} />
                </Avatar>
                <Paper
                  bg="gray.0"
                  p="sm"
                  radius="md"
                  className={classes.botBubble}
                >
                  <Text size="sm" mb="xs">
                    Işık Üniversitesi Çift Anadal Yönergesi{" "}
                    <strong>Madde 5</strong>'e göre başvuru anında anadal
                    diploma programındaki genel not ortalamanızın en az{" "}
                    <strong>2.72 (100 üzerinden 70)</strong> olması
                    gerekmektedir.
                  </Text>
                  <Group gap="xs" mt="sm">
                    <Badge
                      color="grape"
                      variant="light"
                      size="sm"
                      leftSection={<IconCheck size={10} />}
                    >
                      Kaynak: ÇAP Yönergesi
                    </Badge>
                  </Group>
                </Paper>
              </Group>
            </Paper>
          </Grid.Col>
        </Grid>
      </Container>
    </Box>
  );
}
