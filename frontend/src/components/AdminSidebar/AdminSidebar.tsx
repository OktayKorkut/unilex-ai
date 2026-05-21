import { AppShell, Group, Text, Paper, Avatar, ActionIcon, NavLink, Image } from '@mantine/core';
import { IconDashboard, IconSpider, IconHeartbeat, IconLogout } from '@tabler/icons-react';
import { Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import classes from './AdminSidebar.module.css';

interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  is_admin: boolean;
}

interface AdminSidebarProps {
  activePage: 'dashboard' | 'crawler' | 'health';
  onClose?: () => void;
}

export default function AdminSidebar({ activePage, onClose }: AdminSidebarProps) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('Error parsing user data in AdminSidebar:', e);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/');
    window.location.reload();
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .filter(Boolean)
      .map((n) => n[0])
      .join('')
      .toUpperCase();
  };

  return (
    <AppShell.Navbar p="md" bg="#0b132b" className={classes.navbar}>
      <Link to="/" className={classes.logoLink}>
        <Group className={classes.logoGroup}>
          <Image src="/logo_gold.png" h={32} w="auto" fit="contain" />
          <div>
            <Text className={classes.logoText}>UniLex</Text>
            <Text className={classes.logoSubtitle}>AI LAB ADMIN</Text>
          </div>
        </Group>
      </Link>

      <div className={classes.navigationSection}>
        <NavLink
          label="Dashboard"
          component={Link}
          to="/admin"
          leftSection={<IconDashboard size={18} />}
          active={activePage === 'dashboard'}
          color="cyan"
          variant="light"
          className={activePage === 'dashboard' ? classes.navLinkActive : classes.navLink}
          onClick={onClose}
        />
        <NavLink
          label="Crawler (PDF)"
          component={Link}
          to="/admin/crawler"
          leftSection={<IconSpider size={18} />}
          active={activePage === 'crawler'}
          color="cyan"
          variant="light"
          className={activePage === 'crawler' ? classes.navLinkActive : classes.navLink}
          onClick={onClose}
        />
        <NavLink
          label="Sistem Sağlığı"
          component={Link}
          to="/admin/health"
          leftSection={<IconHeartbeat size={18} />}
          active={activePage === 'health'}
          color="cyan"
          variant="light"
          className={activePage === 'health' ? classes.navLinkActive : classes.navLink}
          onClick={onClose}
        />

      </div>

      <Paper withBorder p="sm" radius="md" className={classes.userPanel}>
        <Group justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <Avatar radius="xl" color="cyan" size="sm">
              {user?.full_name ? getInitials(user.full_name) : 'A'}
            </Avatar>
            <div>
              <Text className={classes.userTitle} truncate>
                {user?.full_name || 'Admin Panel'}
              </Text>
              <Text className={classes.userSubtitle}>SÜPER YÖNETİCİ</Text>
            </div>
          </Group>
          <ActionIcon variant="subtle" color="gray" onClick={handleLogout}>
            <IconLogout size={18} color="white" />
          </ActionIcon>
        </Group>
      </Paper>
    </AppShell.Navbar>
  );
}
