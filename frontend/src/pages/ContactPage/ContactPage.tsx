import { Container, Title, Text, SimpleGrid, Paper, TextInput, Textarea, Button, Group, ThemeIcon, Box, Alert } from '@mantine/core';
import { IconMapPin, IconPhone, IconMail, IconSend, IconCheck, IconAlertCircle } from '@tabler/icons-react';
import { useRef, useState } from 'react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import classes from './ContactPage.module.css';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export default function ContactPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useGSAP(() => {
    gsap.from(".contact-header", { y: -30, opacity: 0, duration: 0.8, ease: "power2.out" });
    gsap.from(".contact-info", { x: -50, opacity: 0, duration: 0.8, delay: 0.2, ease: "power2.out" });
    gsap.from(".contact-form", { x: 50, opacity: 0, duration: 0.8, delay: 0.4, ease: "power2.out" });
  }, { scope: containerRef });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !message) {
      setStatus({ type: 'error', text: 'Lütfen tüm alanları doldurun.' });
      return;
    }

    setLoading(true);
    setStatus(null);

    try {
      const res = await fetch(`${API_BASE_URL}/feedbacks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: fullName,
          email,
          message,
        }),
      });

      if (!res.ok) {
        throw new Error('Mesaj gönderilemedi. Lütfen tekrar deneyin.');
      }

      setStatus({ type: 'success', text: 'Mesajınız başarıyla iletildi! En kısa sürede dönüş yapılacaktır.' });
      setFullName('');
      setEmail('');
      setMessage('');

      // Auto close after 4 seconds
      setTimeout(() => {
        setStatus(null);
      }, 4000);
    } catch (err: any) {
      setStatus({ type: 'error', text: err.message || 'Bir hata oluştu.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div ref={containerRef} className={classes.contactPage}>
      <Container size="xl" pt={200} pb={50}>
        <div className={`contact-header ${classes.contactHeaderContainer}`}>
          <Title order={1} className={classes.contactTitle}>
            Bize <span className={classes.titleSpan}>Ulaşın</span>
          </Title>
          <Text c="gray.4" mt="md" size="lg" maw={600} mx="auto" pb={50}>
            UniLex AI platformu hakkında detaylı bilgi almak, geri bildirimde bulunmak veya sistem yöneticileri ile iletişime geçmek için aşağıdaki formu doldurabilirsiniz.
          </Text>
        </div>

        <SimpleGrid cols={{ base: 1, md: 2 }} spacing={50}>
          {/* Sol Kısım: İletişim Bilgileri */}
          <Box className="contact-info">
            <Title order={3} c="white" mb="xl">UniLex AI İletişim Bilgileri</Title>

            <Group wrap="nowrap" mb="xl">
              <ThemeIcon size={50} radius="md" color="cyan" variant="light">
                <IconMapPin size={24} />
              </ThemeIcon>
              <div>
                <Text fw={700} c="white">Adres</Text>
                <Text c="gray.4">Maslak, Sarıyer, İstanbul</Text>
              </div>
            </Group>

            <Group wrap="nowrap" mb="xl">
              <ThemeIcon size={50} radius="md" color="yellow" variant="light">
                <IconPhone size={24} />
              </ThemeIcon>
              <div>
                <Text fw={700} c="white">Telefon</Text>
                <Text c="gray.4">+90 (850) 123 45 67</Text>
              </div>
            </Group>

            <Group wrap="nowrap" mb="xl">
              <ThemeIcon size={50} radius="md" color="teal" variant="light">
                <IconMail size={24} />
              </ThemeIcon>
              <div>
                <Text fw={700} c="white">E-Posta</Text>
                <Text c="gray.4">destek@unilex-ai.com / contact@unilex-ai.com</Text>
              </div>
            </Group>

            <Paper p="xl" radius="md" className={classes.infoCard}>
              <Text fw={700} c="white" size="lg" mb="sm">Destek Saatleri</Text>
              <Text size="sm" c="gray.4">Hafta içi her gün: 09:00 - 18:00</Text>
              <Text size="sm" c="gray.4" mt="xs">Mesajlarınıza maksimum 24 saat içerisinde yanıt verilmektedir.</Text>
            </Paper>
          </Box>

          {/* Sağ Kısım: İletişim Formu */}
          <Paper
            component="form"
            onSubmit={handleSubmit}
            className={`contact-form ${classes.formCard}`}
            radius="md"
            p="xl"
          >
            <Title order={3} c="white" mb="xl">Mesaj Gönder</Title>

            {status && (
              <Alert
                icon={status.type === 'success' ? <IconCheck size={16} /> : <IconAlertCircle size={16} />}
                title={status.type === 'success' ? 'Başarılı' : 'Hata'}
                color={status.type === 'success' ? 'teal' : 'red'}
                mb="md"
              >
                {status.text}
              </Alert>
            )}

            <TextInput
              label="Adınız Soyadınız"
              placeholder="John Doe"
              size="md"
              mb="md"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              classNames={{
                input: classes.formInput,
                label: classes.formLabel
              }}
            />

            <TextInput
              label="E-Posta Adresiniz"
              placeholder="ornek@domain.com"
              type="email"
              size="md"
              mb="md"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              classNames={{
                input: classes.formInput,
                label: classes.formLabel
              }}
            />

            <Textarea
              label="Mesajınız"
              placeholder="Görüş, öneri veya destek talebinizi buraya yazabilirsiniz..."
              size="md"
              minRows={5}
              mb="xl"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              required
              classNames={{
                input: classes.formInput,
                label: classes.formLabel
              }}
            />

            <Button type="submit" size="lg" color="cyan" fullWidth loading={loading} leftSection={<IconSend size={18} />}>
              Mesajı Gönder
            </Button>
          </Paper>
        </SimpleGrid>
      </Container>
    </div>
  );
}
