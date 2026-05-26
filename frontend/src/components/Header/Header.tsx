import { useState, useEffect } from 'react';
import { Group, Button, Container, Text, Burger, Image, Menu, Avatar, UnstyledButton, Drawer, Stack, Box } from '@mantine/core';
import { Link, useNavigate } from 'react-router-dom';
import { useDisclosure, useWindowScroll } from '@mantine/hooks';
import { IconUser, IconLogout, IconChevronDown, IconLayoutDashboard } from '@tabler/icons-react';
import AuthModal from '../AuthModal/AuthModal';
import classes from './Header.module.css';

const links = [
  { link: '/', label: 'Ana Sayfa' },
  { link: '/chat', label: 'Asistan' },
  { link: '/admin', label: 'Yönetim' },
  { link: '/about', label: 'Hakkımızda' },
  { link: '/contact', label: 'İletişim' },
];

interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  is_admin: boolean;
  university_id?: number;
  avatar_url?: string;
}

export default function Header() {
  const [opened, { toggle, close }] = useDisclosure(false);
  const [scroll] = useWindowScroll();
  const [authOpened, setAuthOpened] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadUser = () => {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (e) {
          console.error('Error parsing user data:', e);
        }
      } else {
        setUser(null);
      }
    };

    loadUser();

    window.addEventListener('user-updated', loadUser);
    window.addEventListener('storage', loadUser);

    const handleOpenAuth = () => setAuthOpened(true);
    window.addEventListener('open-auth-modal', handleOpenAuth);

    return () => {
      window.removeEventListener('user-updated', loadUser);
      window.removeEventListener('storage', loadUser);
      window.removeEventListener('open-auth-modal', handleOpenAuth);
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    navigate('/');
    window.location.reload();
  };

  const isAdmin = user && (user.is_admin || user.email?.startsWith('admin'));

  const items = links.map((link) => {
    // Hide 'Yönetim' (Admin) if not logged in or not admin
    if (link.link === '/admin' && !isAdmin) return null;
    return (
      <Link
        key={link.label}
        to={link.link}
        className={classes.link}
      >
        {link.label}
      </Link>
    );
  });

  return (
    <header className={`${classes.header} ${scroll.y > 50 ? classes.scrolled : ''}`}>
      <Container size="xl" className={classes.inner}>
        <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center' }}>
          <Group gap="sm" className={classes.logo}>
            <Image src="/logo_gold.png" h={50} w="auto" fit="contain" />
            <Text fw={900} size="xl" className={classes.logoText}>
              UniLex AI
            </Text>
          </Group>
        </Link>

        <Group gap={30} visibleFrom="sm">
          {items}
        </Group>

        <Group visibleFrom="sm">
          {user ? (
            <Menu shadow="md" width={200} position="bottom-end" transitionProps={{ transition: 'pop-top-right' }}>
              <Menu.Target>
                <UnstyledButton className={classes.userMenuBtn}>
                  <Group gap={8}>
                    <Avatar color="cyan" radius="xl" size="sm" src={user.avatar_url || undefined}>
                      {(user.full_name || user.email || 'U')
                        .split(' ')
                        .filter(Boolean)
                        .map((n) => n[0])
                        .join('')
                        .toUpperCase()}
                    </Avatar>
                    <div style={{ flex: 1 }}>
                      <Text size="sm" fw={700} c="white">
                        {user.full_name || user.email}
                      </Text>
                    </div>
                    <IconChevronDown size={14} color="gray" />
                  </Group>
                </UnstyledButton>
              </Menu.Target>

              <Menu.Dropdown bg="#0b132b" style={{ border: '1px solid rgba(255,255,255,0.1)' }}>
                <Menu.Label c="dimmed">Hesabım</Menu.Label>

                <Menu.Item
                  leftSection={<IconUser size={14} />}
                  component={Link}
                  to="/profile"
                  c="white"
                  className={classes.menuItem}
                >
                  Profilim
                </Menu.Item>

                {isAdmin && (
                  <Menu.Item
                    leftSection={<IconLayoutDashboard size={14} />}
                    component={Link}
                    to="/admin"
                    c="white"
                    className={classes.menuItem}
                  >
                    Yönetim Paneli
                  </Menu.Item>
                )}

                <Menu.Divider style={{ borderColor: 'rgba(255,255,255,0.05)' }} />

                <Menu.Item
                  color="red"
                  leftSection={<IconLogout size={14} />}
                  onClick={handleLogout}
                >
                  Çıkış Yap
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          ) : (
            <>
              <Button variant="subtle" className={classes.loginBtn} onClick={() => setAuthOpened(true)}>
                Giriş Yap
              </Button>
              <Button radius="xl" color="cyan" className={classes.signupBtn} onClick={() => setAuthOpened(true)}>
                Ücretsiz Başla
              </Button>
            </>
          )}
        </Group>

        <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" color="white" className={classes.burger} />
      </Container>

      {/* Responsive Drawer for Mobile Navigation */}
      <Drawer
        opened={opened}
        onClose={close}
        size="100%"
        padding="md"
        title={
          <Group gap="sm">
            <Image src="/logo_gold.png" h={40} w="auto" fit="contain" />
            <Text fw={900} size="xl" c="white">
              UniLex AI
            </Text>
          </Group>
        }
        hiddenFrom="sm"
        zIndex={200}
        styles={{
          header: {
            backgroundColor: '#0b132b',
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
            paddingBottom: '15px',
          },
          content: {
            backgroundColor: '#0b132b',
          },
          body: {
            backgroundColor: '#0b132b',
            minHeight: 'calc(100vh - 80px)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            paddingTop: '30px',
          },
          close: {
            color: 'white',
            backgroundColor: 'transparent',
            '&:hover': {
              backgroundColor: 'rgba(255,255,255,0.05)',
            }
          }
        }}
      >
        <Stack gap="md" style={{ flex: 1 }}>
          {links.map((link) => {
            if (link.link === '/admin' && !isAdmin) return null;
            return (
              <Link
                key={link.label}
                to={link.link}
                className={classes.mobileLink}
                onClick={close}
              >
                {link.label}
              </Link>
            );
          })}
        </Stack>

        <Box mt="auto" pb="xl">
          {user ? (
            <Stack gap="sm">
              <Group gap="sm" p="sm" style={{ borderTop: '1px solid rgba(255,255,255,0.05)', borderBottom: '1px solid rgba(255,255,255,0.05)', width: '100%', marginBottom: '15px' }}>
                <Avatar color="cyan" radius="xl" src={user.avatar_url || undefined}>
                  {(user.full_name || user.email || 'U')
                    .split(' ')
                    .filter(Boolean)
                    .map((n) => n[0])
                    .join('')
                    .toUpperCase()}
                </Avatar>
                <Box style={{ flex: 1, minWidth: 0 }}>
                  <Text size="sm" fw={700} c="white" truncate>
                    {user.full_name}
                  </Text>
                  <Text size="xs" c="dimmed" truncate>
                    {user.email}
                  </Text>
                </Box>
              </Group>
              <Button
                component={Link}
                to="/profile"
                variant="light"
                color="cyan"
                fullWidth
                radius="xl"
                onClick={close}
                leftSection={<IconUser size={16} />}
              >
                Profilim
              </Button>
              {isAdmin && (
                <Button
                  component={Link}
                  to="/admin"
                  variant="light"
                  color="grape"
                  fullWidth
                  radius="xl"
                  onClick={close}
                  leftSection={<IconLayoutDashboard size={16} />}
                >
                  Yönetim Paneli
                </Button>
              )}
              <Button
                variant="outline"
                color="red"
                fullWidth
                radius="xl"
                onClick={() => {
                  close();
                  handleLogout();
                }}
                leftSection={<IconLogout size={16} />}
              >
                Çıkış Yap
              </Button>
            </Stack>
          ) : (
            <Stack gap="sm">
              <Button variant="subtle" className={classes.loginBtn} fullWidth onClick={() => { close(); setAuthOpened(true); }}>
                Giriş Yap
              </Button>
              <Button radius="xl" color="cyan" fullWidth onClick={() => { close(); setAuthOpened(true); }}>
                Ücretsiz Başla
              </Button>
            </Stack>
          )}
        </Box>
      </Drawer>

      <AuthModal opened={authOpened} onClose={() => setAuthOpened(false)} />
    </header>
  );
}


