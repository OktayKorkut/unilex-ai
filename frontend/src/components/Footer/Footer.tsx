import { Container, Group, ActionIcon, Text, Box, Image } from '@mantine/core';
import { IconBrandTwitter, IconBrandYoutube, IconBrandInstagram } from '@tabler/icons-react';
import classes from './Footer.module.css';

export default function Footer() {
  return (
    <Box className={classes.footer}>
      <Container className={classes.inner} size="xl">
        <div className={classes.logoSection}>
          <Group gap="sm">
            <Image src="/logo_gold.png" h={40} w="auto" fit="contain" />
            <Text fw={900} size="xl" color="white">
              UniLex AI
            </Text>
          </Group>
          <Text size="sm" c="dimmed" mt="md" maw={300}>
            Akademik araştırmaların geleceği için geliştirilen ileri düzey yapay zeka asistanı. Işık Üniversitesi yönetmelikleri ile tam uyumlu.
          </Text>
        </div>

        <Group className={classes.links} gap="xl">
          <Box>
            <Text fw={700} color="white" mb="sm">Ürün</Text>
            <a href="/" className={classes.link}>Özellikler</a>
            <a href="/" className={classes.link}>Nasıl Çalışır?</a>
            <a href="/" className={classes.link}>Fiyatlandırma</a>
          </Box>
          <Box>
            <Text fw={700} color="white" mb="sm">Kurumsal</Text>
            <a href="/about" className={classes.link}>Hakkımızda</a>
            <a href="/about" className={classes.link}>Gizlilik Politikası</a>
            <a href="/contact" className={classes.link}>İletişim</a>
          </Box>
        </Group>
      </Container>

      <Container className={classes.afterFooter} size="xl">
        <Text c="dimmed" size="sm">
          © 2026 Işık Üniversitesi AI Lab. Tüm hakları saklıdır.
        </Text>

        <Group gap={10} className={classes.social} justify="flex-end" wrap="nowrap">
          <ActionIcon size="lg" color="gray" variant="subtle">
            <IconBrandTwitter size={18} stroke={1.5} />
          </ActionIcon>
          <ActionIcon size="lg" color="gray" variant="subtle">
            <IconBrandYoutube size={18} stroke={1.5} />
          </ActionIcon>
          <ActionIcon size="lg" color="gray" variant="subtle">
            <IconBrandInstagram size={18} stroke={1.5} />
          </ActionIcon>
        </Group>
      </Container>
    </Box>
  );
}
