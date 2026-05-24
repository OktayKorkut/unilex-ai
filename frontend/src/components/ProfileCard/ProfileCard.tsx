import { useState } from 'react';
import { Card, Box, Avatar, Badge, Title, Text, Grid } from '@mantine/core';
import { IconCamera } from '@tabler/icons-react';
import classes from '../../pages/ProfilePage/ProfilePage.module.css';

interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  university_id?: number;
  avatar_url?: string;
  history_saved: boolean;
  anonymized: boolean;
}

interface ProfileCardProps {
  user: UserProfile;
  roleInfo: { label: string; color: string };
  sessionsCount: number;
  token?: string;
  onUserUpdate?: (updatedUser: any) => void;
}

import { API_BASE_URL } from '../../config';

export default function ProfileCard({ 
  user, 
  roleInfo, 
  sessionsCount, 
  token,
  onUserUpdate
}: ProfileCardProps) {
  const [uploading, setUploading] = useState(false);

  const handleAvatarClick = () => {
    if (token && onUserUpdate) {
      document.getElementById('profile-avatar-file-input')?.click();
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !token || !onUserUpdate) return;

    const allowedTypes = ["image/jpeg", "image/png", "image/gif", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      alert('Yalnızca JPEG, PNG, GIF veya WEBP formatındaki resimler yüklenebilir.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/users/me/avatar`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (res.ok) {
        const updatedUser = await res.json();
        onUserUpdate(updatedUser);
        localStorage.setItem('user', JSON.stringify(updatedUser));
        window.dispatchEvent(new Event('user-updated'));
      } else {
        const errData = await res.json();
        alert(errData.detail || 'Resim yüklenirken hata oluştu.');
      }
    } catch (err) {
      alert('Sunucu ile bağlantı kurulamadı.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card radius="lg" p="xl" className={classes.glassCard}>
      <Box style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
        <div className={classes.avatarWrapper} onClick={handleAvatarClick}>
          <Avatar 
            color="cyan" 
            size={120} 
            radius="xl" 
            src={uploading ? undefined : (user.avatar_url || undefined)} 
            className={classes.avatarEl}
          >
            {uploading ? '...' : user.full_name.split(' ').map(n => n[0]).join('').toUpperCase()}
          </Avatar>
          
          {token && onUserUpdate && (
            <>
              <div className={classes.avatarOverlay}>
                <IconCamera size={24} color="white" style={{ marginBottom: 4 }} />
                <Text size="10px" fw={700} c="white">Fotoğraf Değiştir</Text>
              </div>
              <input
                id="profile-avatar-file-input"
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={handleFileChange}
              />
            </>
          )}
          
          <Badge 
            color={roleInfo.color} 
            size="sm" 
            radius="md" 
            className={classes.roleBadge}
          >
            {roleInfo.label}
          </Badge>
        </div>

        <Title order={3} c="white" mb={5}>
          {user.full_name}
        </Title>
        <Text size="sm" c="dimmed" mb="xl">
          {user.email}
        </Text>

        <Grid className={classes.profileStatsContainer}>
          <Grid.Col span={6}>
            <Text size="xl" fw={900} c="cyan" className={classes.monoFont}>{sessionsCount}</Text>
            <Text size="xs" c="dimmed">Aktif Sohbet</Text>
          </Grid.Col>
          <Grid.Col span={6} className={classes.statsDivider}>
            <Text size="xl" fw={900} c="grape" className={classes.monoFont}>50</Text>
            <Text size="xs" c="dimmed">Sohbet Limiti</Text>
          </Grid.Col>
        </Grid>
      </Box>
    </Card>
  );
}
