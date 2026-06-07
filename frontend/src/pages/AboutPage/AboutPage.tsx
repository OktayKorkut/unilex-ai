import {
  Container,
  Title,
  Text,
  SimpleGrid,
  Grid,
  Card,
  Group,
  Badge,
  Button,
  ThemeIcon,
  Box,
  List,
  Avatar,
  Flex,
} from "@mantine/core";
import {
  IconShieldCheck,
  IconBulb,
  IconEye,
  IconCheck,
  IconSchool,
  IconMicroscope,
  IconUsersGroup,
  IconArrowRight,
  IconDatabase,
} from "@tabler/icons-react";
import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import classes from "./AboutPage.module.css";

gsap.registerPlugin(ScrollTrigger);

const rootsData = [
  {
    icon: IconSchool,
    title: "Akademik Rehberlik",
    description:
      "Üniversitemizin köklü akademik birikimi, her algoritmanın doğruluğunu denetler.",
    color: "#00bcd4",
  },
  {
    icon: IconMicroscope,
    title: "İleri Laboratuvarlar",
    description:
      "En son GPU teknolojileri ve büyük veri setleri ile modellerimizi eğitiyoruz.",
    color: "#20c997",
  },
  {
    icon: IconUsersGroup,
    title: "Öğrenci Odaklı",
    description:
      "Platformumuzu, gerçek kampüs ihtiyaçlarını analiz ederek öğrencilerimizle birlikte tasarlıyoruz.",
    color: "#9c27b0",
  },
];

export default function AboutPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const handleStart = () => {
    if (localStorage.getItem("token")) {
      navigate("/chat");
    } else {
      window.dispatchEvent(new Event("open-auth-modal"));
    }
  };

  const handleContact = () => {
    navigate("/contact");
  };

  useGSAP(
    () => {
      // Hero Animasyonu
      gsap.from(".hero-element", {
        y: 40,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: "power3.out",
      });

      // Bento Grid Kartları
      gsap.from(".bento-card", {
        scrollTrigger: {
          trigger: ".bento-section",
          start: "top 80%",
        },
        y: 50,
        opacity: 0,
        duration: 0.8,
        stagger: 0.2,
        ease: "back.out(1.2)",
      });

      // RAG Section
      gsap.from(".rag-content", {
        scrollTrigger: {
          trigger: ".rag-section",
          start: "top 75%",
        },
        x: -50,
        opacity: 0,
        duration: 0.8,
        ease: "power2.out",
      });

      gsap.from(".rag-image", {
        scrollTrigger: {
          trigger: ".rag-section",
          start: "top 75%",
        },
        x: 50,
        opacity: 0,
        duration: 0.8,
        ease: "power2.out",
      });

      // Akademik Kökler
      gsap.from(".root-card", {
        scrollTrigger: {
          trigger: ".roots-section",
          start: "top 80%",
        },
        y: 40,
        opacity: 0,
        duration: 0.6,
        stagger: 0.15,
        ease: "power2.out",
      });
    },
    { scope: containerRef },
  );

  return (
    <div ref={containerRef} className={classes.container}>
      {/* 1. HERO SECTION - Tam Ekran Yüksekliği */}
      <Container
        size="md"
        style={{
          textAlign: "center",
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
        }}
      >
        <Box pt={100}>
          <Badge
            className="hero-element"
            size="xl"
            variant="light"
            color="cyan"
            mb="xl"
            radius="sm"
          >
            <IconBulb size={14} style={{ marginRight: 8 }} />
            AKADEMİK GELECEK
          </Badge>

          <Title
            className="hero-element"
            order={1}
            c="white"
            mb="lg"
            fz={{ base: "2.2rem", sm: "3.5rem" }}
            fw={900}
            lh={1.2}
          >
            Akademik Aydınlanma İçin{" "}
            <span style={{ color: "#d4af37" }}>Tasarlandı</span>
          </Title>

          <Text
            className="hero-element"
            c="gray.4"
            size="xl"
            maw={700}
            mx="auto"
            mb={40}
          >
            UniLex AI, araştırmacıların ve öğrencilerin bilgiye erişimini yapay
            zeka ile dönüştürerek, karmaşık verileri berrak akademik çıktılara
            dönüştürmeyi misyon edinmiştir.
          </Text>

          <Group justify="center" className="hero-element">
            <Button
              size="lg"
              radius="xl"
              color="cyan"
              rightSection={<IconArrowRight size={18} />}
              onClick={handleStart}
            >
              Asistanı Dene
            </Button>
            <Button
              size="lg"
              radius="xl"
              variant="default"
              bg="rgba(255,255,255,0.05)"
              c="white"
              style={{ border: "1px solid rgba(255,255,255,0.1)" }}
              onClick={handleContact}
            >
              İletişime Geç
            </Button>
          </Group>
        </Box>
      </Container>

      {/* 2. BENTO GRID (TEMEL DEĞERLERİMİZ) */}
      <Container
        size="xl"
        pt={{ base: 40, md: 80 }}
        pb={{ base: 40, md: 80 }}
        className="bento-section"
      >
        <Title order={2} c="white" mb="xs">
          Temel Değerlerimiz
        </Title>
        <Text c="gray.4" mb={40}>
          Yapay zekayı akademik dürüstlük çatısı altında yeniden tanımlıyoruz.
        </Text>

        <Grid align="stretch" style={{ gap: "var(--mantine-spacing-xl)" }}>
          {/* Şeffaflık Kartı */}
          <Grid.Col span={{ base: 12, md: 8 }}>
            <Card
              radius="lg"
              p={{ base: "md", sm: "xl" }}
              className={`bento-card ${classes.gradientCard}`}
              h="100%"
            >
              <Flex
                direction={{ base: "column", sm: "row" }}
                gap="xl"
                align="center"
                h="100%"
                className={classes.cardContent}
              >
                <Box style={{ flex: 1 }}>
                  <ThemeIcon
                    size={50}
                    radius="md"
                    color="cyan"
                    variant="light"
                    mb="xl"
                  >
                    <IconEye size={24} />
                  </ThemeIcon>
                  <Title order={3} c="white" mb="sm">
                    Şeffaflık
                  </Title>
                  <Text c="gray.4" size="md">
                    AI'nın akıl yürütme süreçlerini "camdan bir kutu" haline
                    getiriyoruz. Her yanıt, takip edilebilir kaynaklar ve
                    mantıksal bir akışla sunulur.
                  </Text>
                </Box>
                {/* Dekoratif Görsel Alanı */}
                <Box
                  style={{
                    flex: 1,
                    width: "100%",
                    height: "200px",
                    borderRadius: "12px",
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    overflow: "hidden",
                    position: "relative",
                  }}
                >
                  <div className={classes.spinningBg} />
                  <div
                    style={{
                      position: "absolute",
                      inset: "2px",
                      background: "#0b132b",
                      borderRadius: "10px",
                    }}
                  />
                  <IconBulb
                    size={60}
                    color="#20c997"
                    style={{ zIndex: 1, opacity: 0.5 }}
                  />
                </Box>
              </Flex>
            </Card>
          </Grid.Col>

          {/* Akademik Dürüstlük Kartı */}
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Card
              radius="lg"
              p={{ base: "md", sm: "xl" }}
              className={`bento-card ${classes.gradientCard}`}
              h="100%"
            >
              <div className={classes.cardContent}>
                <ThemeIcon
                  size={50}
                  radius="md"
                  color="grape"
                  variant="light"
                  mb="xl"
                >
                  <IconShieldCheck size={24} />
                </ThemeIcon>
                <Title order={3} c="white" mb="sm">
                  Akademik Dürüstlük
                </Title>
                <Text c="gray.4" size="md" mb="xl">
                  Bilginin doğruluğu ve kaynakların orijinalliği sistemimizin
                  kalbinde yer alır.
                </Text>
                <Badge color="grape" variant="outline">
                  SIFIR HALÜSİNASYON HEDEFİ
                </Badge>
              </div>
            </Card>
          </Grid.Col>

          {/* İnovasyon Kartı */}
          <Grid.Col span={12}>
            <Card
              radius="lg"
              p={{ base: "md", sm: "xl" }}
              className={`bento-card ${classes.gradientCard}`}
            >
              <Flex
                direction={{ base: "column", md: "row" }}
                gap="xl"
                align={{ base: "stretch", md: "center" }}
                className={classes.cardContent}
              >
                <Box style={{ flex: "1 1 300px" }}>
                  <Title order={3} c="white" mb="sm">
                    İnovasyon
                  </Title>
                  <Text c="gray.4" size="md" mb="xl">
                    UniLex AI bünyesinde geliştirilen algoritmalarımız, sadece
                    yanıt vermekle kalmaz, akademik merakı teşvik eden yeni
                    perspektifler sunar.
                  </Text>
                  <Group>
                    <Avatar.Group>
                      <Avatar color="cyan" radius="xl">
                        AI
                      </Avatar>
                      <Avatar color="grape" radius="xl">
                        ML
                      </Avatar>
                      <Avatar color="teal" radius="xl">
                        NLP
                      </Avatar>
                    </Avatar.Group>
                    <Text size="sm" c="dimmed">
                      50+ Akademik İşbirliği
                    </Text>
                  </Group>
                </Box>

                <Box
                  style={{
                    flex: "1 1 200px",
                    display: "flex",
                    gap: "1rem",
                    width: "100%",
                  }}
                >
                  <Card
                    bg="rgba(0,0,0,0.3)"
                    p="lg"
                    radius="md"
                    style={{
                      flex: 1,
                      border: "1px solid rgba(255,255,255,0.05)",
                      textAlign: "center",
                    }}
                  >
                    <Text
                      size="xl"
                      fw={900}
                      className={classes.glowText}
                      style={{ fontSize: "2rem" }}
                    >
                      99%
                    </Text>
                    <Text size="sm" c="gray.5">
                      Doğruluk Payı
                    </Text>
                  </Card>
                  <Card
                    bg="rgba(0,0,0,0.3)"
                    p="lg"
                    radius="md"
                    style={{
                      flex: 1,
                      border: "1px solid rgba(255,255,255,0.05)",
                      textAlign: "center",
                    }}
                  >
                    <Text
                      size="xl"
                      fw={900}
                      className={classes.glowText}
                      style={{ fontSize: "2rem" }}
                    >
                      24/7
                    </Text>
                    <Text size="sm" c="gray.5">
                      Kesintisiz Destek
                    </Text>
                  </Card>
                </Box>
              </Flex>
            </Card>
          </Grid.Col>
        </Grid>
      </Container>

      {/* 3. TEKNOLOJİK TEMELİMİZ: RAG */}
      <Container
        size="xl"
        pt={{ base: 40, md: 80 }}
        pb={{ base: 40, md: 80 }}
        className="rag-section"
      >
        <SimpleGrid
          cols={{ base: 1, md: 2 }}
          spacing={60}
          style={{ alignItems: "center" }}
        >
          <Box className="rag-content">
            <Badge color="cyan" variant="light" mb="md">
              RETRIEVAL-AUGMENTED GENERATION
            </Badge>
            <Title
              order={2}
              c="white"
              mb="lg"
              fz={{ base: "1.8rem", sm: "2.5rem" }}
              lh={1.1}
            >
              Teknolojik Temelimiz: <br />
              <span className={classes.glowText}>RAG</span>
            </Title>
            <Text c="gray.4" size="lg" mb="xl">
              UniLex AI, standart dil modellerinin ötesine geçerek RAG
              teknolojisini kullanır. Bu sistem AI'nın sadece bildiklerini
              söylemesini değil, Işık Üniversitesi'nin güvenilir veri
              tabanlarından anlık bilgi çekerek yanıt oluşturmasını sağlar.
            </Text>

            <List
              spacing="lg"
              size="md"
              center
              icon={
                <ThemeIcon color="teal" size={24} radius="xl">
                  <IconCheck size={16} />
                </ThemeIcon>
              }
            >
              <List.Item>
                <Text fw={700} c="white">
                  Gerçek Zamanlı Veri Erişimi
                </Text>
                <Text c="gray.5" size="sm">
                  En güncel yönetmelikler ve kütüphane kaynakları anında
                  taranır.
                </Text>
              </List.Item>
              <List.Item>
                <Text fw={700} c="white">
                  Kanıta Dayalı Yanıtlar
                </Text>
                <Text c="gray.5" size="sm">
                  Her iddia, sistem tarafından doğrulanmış bir akademik kaynağa
                  dayanır.
                </Text>
              </List.Item>
            </List>
          </Box>

          <Box
            className="rag-image"
            h={{ base: 300, md: 400 }}
            style={{ position: "relative" }}
          >
            <div
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: "24px",
                background:
                  "linear-gradient(45deg, rgba(11, 19, 43, 0.5), rgba(0, 188, 212, 0.2))",
                border: "1px solid rgba(0, 188, 212, 0.3)",
                overflow: "hidden",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {/* Siber Çip Görseli Efekti */}
              <div
                style={{
                  width: "150px",
                  height: "150px",
                  background: "rgba(0, 188, 212, 0.1)",
                  border: "2px solid #00bcd4",
                  borderRadius: "16px",
                  boxShadow: "0 0 50px rgba(0, 188, 212, 0.5)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  position: "relative",
                }}
              >
                <IconDatabase size={60} color="#00bcd4" />
                <div
                  style={{
                    position: "absolute",
                    top: "-50px",
                    width: "2px",
                    height: "50px",
                    background: "#00bcd4",
                    boxShadow: "0 0 10px #00bcd4",
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    bottom: "-50px",
                    width: "2px",
                    height: "50px",
                    background: "#00bcd4",
                    boxShadow: "0 0 10px #00bcd4",
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    left: "-50px",
                    width: "50px",
                    height: "2px",
                    background: "#00bcd4",
                    boxShadow: "0 0 10px #00bcd4",
                  }}
                />
                <div
                  style={{
                    position: "absolute",
                    right: "-50px",
                    width: "50px",
                    height: "2px",
                    background: "#00bcd4",
                    boxShadow: "0 0 10px #00bcd4",
                  }}
                />
              </div>
            </div>
            <Group
              justify="flex-end"
              mt="xs"
              style={{ position: "absolute", bottom: -15, right: 20 }}
            >
              <Badge color="gray" variant="outline" bg="#0b132b">
                Source: IŞIK 2026
              </Badge>
              <Badge color="gray" variant="outline" bg="#0b132b">
                Source: Qdrant DB
              </Badge>
            </Group>
          </Box>
        </SimpleGrid>
      </Container>

      {/* 4. AKADEMİK KÖKLERİMİZ */}
      <Box
        pt={{ base: 40, md: 80 }}
        pb={20}
        mt={{ base: 30, md: 60 }}
        className="roots-section"
      >
        <Container size="xl">
          <Flex
            direction={{ base: "column", sm: "row" }}
            justify="space-between"
            align={{ base: "flex-start", sm: "flex-end" }}
            gap="md"
            mb={50}
          >
            <Box maw={600}>
              <Title order={2} c="white" mb="md">
                Akademik Köklerimiz
              </Title>
              <Text c="gray.4">
                UniLex AI, Işık Üniversitesi AI Lab bünyesinde, akademisyenler
                ve veri bilimcilerinden oluşan disiplinlerarası bir ekip
                tarafından geliştirilmiştir.
              </Text>
            </Box>
            <Badge
              color="gray"
              variant="outline"
              size="lg"
              style={{ letterSpacing: "2px" }}
            >
              IŞIK UNIVERSITY AI LAB
            </Badge>
          </Flex>

          <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="xl">
            {rootsData.map((item, index) => {
              const Icon = item.icon;
              return (
                <Card
                  key={index}
                  radius="md"
                  p="xl"
                  bg="rgba(255,255,255,0.02)"
                  style={{ border: "1px solid rgba(255,255,255,0.05)" }}
                  className={`root-card ${classes.gradientCard}`}
                >
                  <div className={classes.cardContent}>
                    <Icon
                      size={32}
                      color={item.color}
                      style={{ marginBottom: "1rem" }}
                    />
                    <Title order={4} c="white" mb="sm">
                      {item.title}
                    </Title>
                    <Text c="gray.5" size="sm">
                      {item.description}
                    </Text>
                  </div>
                </Card>
              );
            })}
          </SimpleGrid>
        </Container>
      </Box>
    </div>
  );
}
