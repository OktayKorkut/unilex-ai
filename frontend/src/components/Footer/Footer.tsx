import { Container, Group, Text, Box, Image } from "@mantine/core";
import { Link } from "react-router-dom";
import classes from "./Footer.module.css";

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
            Akademik araştırmaların geleceği için geliştirilen ileri düzey yapay
            zeka asistanı. Işık Üniversitesi yönetmelikleri ile tam uyumlu.
          </Text>
        </div>

        <Group className={classes.links} gap="xl">
          <Box>
            <Text fw={700} color="white" mb="sm">
              Ürün
            </Text>
            <a href="/#features" className={classes.link}>
              Özellikler
            </a>
            <a href="/#how-it-works" className={classes.link}>
              Nasıl Çalışır?
            </a>
          </Box>
          <Box>
            <Text fw={700} color="white" mb="sm">
              Kurumsal
            </Text>
            <Link to="/about" className={classes.link}>
              Hakkımızda
            </Link>
            <Link to="/contact" className={classes.link}>
              İletişim
            </Link>
          </Box>
        </Group>
      </Container>

      <Container className={classes.afterFooter} size="xl">
        <Text c="dimmed" size="sm">
          © 2026 UniLex AI. Tüm hakları saklıdır.
        </Text>
      </Container>
    </Box>
  );
}
