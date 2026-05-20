import { Box, Container, Title, Text, Card, ThemeIcon } from '@mantine/core';
import { IconBrain, IconShieldCheck, IconRefresh, IconSearch, IconScale, IconDeviceLaptop } from '@tabler/icons-react';
import classes from './Features.module.css';

const featuresData = [
  {
    title: 'Akıllı RAG Sorgulama',
    description: 'Bağlama duyarlı veri erişimi ile binlerce sayfa arasında semantik aramalar yapın.',
    icon: <IconBrain size={24} />,
    color: 'cyan',
  },
  {
    title: 'Halüsinasyonsuz Yanıt',
    description: '%99.4 doğruluk oranı ile güvenilirliğinizden ödün vermeden bilimsel yanıtlar alın.',
    icon: <IconShieldCheck size={24} />,
    color: 'teal',
  },
  {
    title: 'Kesintisiz Senkronizasyon',
    description: 'Tüm akademik kütüphanenizi tek bir merkezden yönetin.',
    icon: <IconRefresh size={24} />,
    color: 'blue',
  },
  {
    title: 'Semantik Arama',
    description: 'Sadece anahtar kelimeleri değil, araştırma konunuzun özünü anlayan motor.',
    icon: <IconSearch size={24} />,
    color: 'indigo',
  },
  {
    title: 'Mevzuat Odaklı',
    description: 'Işık Üniversitesi yönetmeliklerine %100 uyumlu hukuki ve akademik zeka.',
    icon: <IconScale size={24} />,
    color: 'grape',
  },
  {
    title: 'Çoklu Platform',
    description: 'İster bilgisayarınızdan, ister telefonunuzdan; her zaman yanınızda.',
    icon: <IconDeviceLaptop size={24} />,
    color: 'orange',
  }
];

export default function Features() {
  return (
    <Box id="features" className={classes.featuresWrapper}>
      <Container size="xl" pt={100} pb={60}>
        <Title order={2} ta="center" className={classes.sectionTitle}>
          Akademik İş Akışınızı Yeniden Tanımlayın
        </Title>
        <Text c="dimmed" ta="center" maw={600} mx="auto" mt="md" mb={40}>
          Yapay zeka destekli araştırma ile saatler süren belge taramalarını saniyelere indirin.
        </Text>
      </Container>

      <Box className={classes.marqueeContainer}>
        <Box className={classes.marqueeContent}>
          {/* Render twice for infinite scrolling effect */}
          {[...featuresData, ...featuresData].map((feature, index) => (
            <Card 
              key={index} 
              shadow="md" 
              padding="xl" 
              radius="md" 
              withBorder 
              className={classes.featureCard}
              style={{
                '--card-color': `var(--mantine-color-${feature.color}-filled)`,
                '--card-color-light': `var(--mantine-color-${feature.color}-light-color)`,
                '--card-color-glow': `var(--mantine-color-${feature.color}-3)`
              } as React.CSSProperties}
            >
              <ThemeIcon size={50} radius="md" color={feature.color} variant="light" mb="xl">
                {feature.icon}
              </ThemeIcon>
              <Title order={3} fw={700} size="h4" mb="xs">
                {feature.title}
              </Title>
              <Text size="sm" c="dimmed">
                {feature.description}
              </Text>
            </Card>
          ))}
        </Box>
      </Box>
    </Box>
  );
}
