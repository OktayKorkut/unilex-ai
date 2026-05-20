import { useState, useRef } from 'react';
import { Modal, TextInput, PasswordInput, Button, Group, Text, Box, Flex, Divider, Anchor, Title, Alert, Loader } from '@mantine/core';
import { IconRobot, IconBrandGoogle, IconBrandGithub, IconAlertCircle } from '@tabler/icons-react';
import gsap from 'gsap';
import { useGSAP } from '@gsap/react';
import classes from './AuthModal.module.css';

interface AuthModalProps {
  opened: boolean;
  onClose: () => void;
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

export default function AuthModal({ opened, onClose }: AuthModalProps) {
  const [type, setType] = useState<'login' | 'register'>('login');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const robotRef = useRef<HTMLDivElement>(null);
  const shadowRef = useRef<HTMLDivElement>(null);

  useGSAP(() => {
    if (opened) {
      // Entrance animation for the robot
      gsap.fromTo(robotRef.current,
        { x: -50, opacity: 0 },
        { x: 0, opacity: 1, duration: 0.6, ease: "back.out(1.5)" }
      );

      // Continuous floating animation for the robot head
      gsap.to(robotRef.current, {
        y: -90,         // Huge vertical bounce
        x: 20,          // Sideways wobble
        rotation: 15,   // Very noticeable tilt
        scale: 1.2,     // Noticeable growth
        repeat: -1,
        yoyo: true,
        duration: 1.5,  // Slightly faster
        ease: "sine.inOut",
        delay: 0.6
      });

      // Animate the shadow (shrinks and fades as robot goes up)
      gsap.fromTo(shadowRef.current,
        { scaleX: 1, opacity: 0.8, x: 0 },
        {
          scaleX: 0.3,
          opacity: 0.1,
          x: 20,        // Shadow follows the sideways wobble
          repeat: -1,
          yoyo: true,
          duration: 1.5,
          ease: "sine.inOut",
          delay: 0.6
        }
      );

      // Animate particles
      gsap.to(".particle", {
        y: "random(-50, 50)",
        x: "random(-50, 50)",
        opacity: "random(0.3, 1)",
        scale: "random(0.5, 1.5)",
        duration: 2,
        repeat: -1,
        yoyo: true,
        stagger: 0.2,
        ease: "sine.inOut"
      });
    }
  }, [opened]);

  const toggleType = () => {
    setType((current) => (current === 'register' ? 'login' : 'register'));
    setErrorMsg('');
    setSuccessMsg('');
  };

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    // E-posta format kontrolü
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setErrorMsg('Lütfen geçerli bir e-posta adresi girin.');
      return;
    }

    if (type === 'register') {
      if (!fullName.trim()) {
        setErrorMsg('Lütfen adınızı ve soyadınızı girin.');
        return;
      }
    }

    if (!email || !password) {
      setErrorMsg('Lütfen tüm zorunlu alanları doldurun.');
      return;
    }

    setLoading(true);

    try {
      if (type === 'register') {
        const res = await fetch(`${API_BASE_URL}/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email,
            password,
            full_name: fullName,
          }),
        });

        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.detail || 'Kayıt olurken bir hata oluştu.');
        }

        setSuccessMsg('Kayıt başarılı! Şimdi giriş yapabilirsiniz.');
        setType('login');
        setPassword('');
      } else {
        const res = await fetch(`${API_BASE_URL}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email,
            password,
          }),
        });

        const data = await res.json();

        if (!res.ok) {
          throw new Error(data.detail || 'Giriş başarısız. Bilgilerinizi kontrol edin.');
        }

        // Token'ı localStorage'a kaydet
        localStorage.setItem('token', data.access_token);

        // Kullanıcı bilgilerini çek (/users/me)
        const userRes = await fetch(`${API_BASE_URL}/users/me`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${data.access_token}`,
          },
        });

        if (userRes.ok) {
          const userData = await userRes.json();
          localStorage.setItem('user', JSON.stringify(userData));
        }

        onClose();
        // Sayfayı yenileyerek state'leri güncelle
        window.location.reload();
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Bir bağlantı hatası oluştu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      withCloseButton={false}
      size="lg"
      padding={0}
      radius="lg"
      centered
      lockScroll={false}
      overlayProps={{
        backgroundOpacity: 0.55,
        blur: 12,
      }}
      transitionProps={{ transition: 'fade', duration: 300 }}
    >
      <Flex className={classes.modalContainer}>
        {/* Left Side - The Floating Robot */}
        <Box className={classes.robotSide}>
          <div className={classes.glow}></div>
          <div className={classes.glow2}></div>

          {/* Data Particles */}
          <div className={`${classes.particle} particle`} style={{ top: '20%', left: '20%' }}></div>
          <div className={`${classes.particle} particle`} style={{ top: '30%', right: '25%' }}></div>
          <div className={`${classes.particle} particle`} style={{ bottom: '40%', left: '30%' }}></div>

          <div className={classes.robotContainer}>
            <div ref={robotRef} className={classes.robotHead}>
              <IconRobot size={140} stroke={1} color="#00bcd4" />
            </div>
            <div ref={shadowRef} className={classes.robotShadow}></div>
          </div>
          <Title order={3} c="white" mt={40} style={{ zIndex: 2 }} ta="center">
            {type === 'login' ? 'Tekrar Hoş Geldiniz!' : 'Maceraya Katılın!'}
          </Title>
          <Text c="cyan.1" size="sm" ta="center" mt="sm" style={{ zIndex: 2 }}>
            Üniversitelerin yapay zeka tabanlı ilk akademik asistanı.
          </Text>
        </Box>

        {/* Right Side - The Form */}
        <Box className={classes.formSide} component="form" onSubmit={handleAuth}>
          <Text size="xl" fw={800} mb="xl" c="dark.8">
            {type === 'login' ? 'Giriş Yap' : 'Kayıt Ol'}
          </Text>

          {errorMsg && (
            <Alert variant="light" color="red" title="Hata" icon={<IconAlertCircle size={16} />} mb="md">
              {errorMsg}
            </Alert>
          )}

          {successMsg && (
            <Alert variant="light" color="green" title="Başarılı" mb="md">
              {successMsg}
            </Alert>
          )}

          {type === 'register' && (
            <TextInput
              label="Ad Soyad"
              placeholder="Adınız Soyadınız"
              required
              mb="md"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          )}

          <TextInput
            label="E-posta Adresi"
            placeholder="ornek@domain.com"
            required
            mb="md"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <PasswordInput
            label="Şifre"
            placeholder="Parolanız"
            required
            mb="xl"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <Button fullWidth radius="xl" color="cyan" size="md" type="submit" disabled={loading}>
            {loading ? <Loader size="xs" color="white" /> : (type === 'login' ? 'Giriş Yap' : 'Hesap Oluştur')}
          </Button>

          <Divider label="Veya" labelPosition="center" my="xl" />

          <Group grow mb="md">
            <Button variant="default" radius="xl" leftSection={<IconBrandGoogle size={18} />}>
              Google
            </Button>
            <Button variant="default" radius="xl" leftSection={<IconBrandGithub size={18} />}>
              GitHub
            </Button>
          </Group>

          <Text ta="center" size="sm" c="dimmed" mt="xl">
            {type === 'login' ? 'Hesabınız yok mu?' : 'Zaten bir hesabınız var mı?'}
            <Anchor component="button" type="button" c="cyan" fw={700} onClick={toggleType} ml={5}>
              {type === 'login' ? 'Hemen Kayıt Olun' : 'Giriş Yapın'}
            </Anchor>
          </Text>
        </Box>
      </Flex>
    </Modal>
  );
}
