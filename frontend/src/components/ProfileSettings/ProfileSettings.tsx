import React, { useState, useEffect } from 'react';
import { Card, Title, Box, Alert, TextInput, PasswordInput, Button, Switch, Select, Divider, Group, Anchor, Text, Badge } from '@mantine/core';
import { IconUser, IconCheck, IconAlertCircle, IconMail, IconLock, IconShieldLock, IconSchool, IconChevronRight, IconTrash } from '@tabler/icons-react';
import classes from '../../pages/ProfilePage/ProfilePage.module.css';

interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  university_id?: number;
}

interface ProfileSettingsProps {
  user: UserProfile;
  token: string;
  universities: { value: string; label: string }[];
  onUserUpdate: (updatedUser: UserProfile) => void;
  onDeleteAccount: () => void;
  historySaved: boolean;
  setHistorySaved: (val: boolean) => void;
  anonymized: boolean;
  setAnonymized: (val: boolean) => void;
  onUniversityChange: (val: string | null) => Promise<void>;
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

export default function ProfileSettings({
  user,
  token,
  universities,
  onUserUpdate,
  onDeleteAccount,
  historySaved,
  setHistorySaved,
  anonymized,
  setAnonymized,
  onUniversityChange,
}: ProfileSettingsProps) {
  const [fullName, setFullName] = useState(user.full_name);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [updateStatus, setUpdateStatus] = useState<{ type: 'success' | 'error' | null; message: string }>({ type: null, message: '' });

  // Update fullName if user prop changes
  useEffect(() => {
    setFullName(user.full_name);
  }, [user.full_name]);

  useEffect(() => {
    if (updateStatus.type) {
      const timer = setTimeout(() => {
        setUpdateStatus({ type: null, message: '' });
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [updateStatus.type]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdateStatus({ type: null, message: '' });

    if (!fullName.trim()) {
      setUpdateStatus({ type: 'error', message: 'İsim alanı boş bırakılamaz.' });
      return;
    }

    if (password && password !== confirmPassword) {
      setUpdateStatus({ type: 'error', message: 'Şifreler eşleşmiyor.' });
      return;
    }

    setLoading(true);
    try {
      const payload: any = { full_name: fullName.trim() };
      if (password) {
        payload.password = password;
      }

      const res = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const updatedUser = await res.json();
        onUserUpdate(updatedUser);
        setUpdateStatus({ 
          type: 'success', 
          message: 'Bilgileriniz başarıyla güncellendi.' 
        });
        setPassword('');
        setConfirmPassword('');
      } else {
        const errData = await res.json();
        setUpdateStatus({ type: 'error', message: errData.detail || 'Güncelleme sırasında hata oluştu.' });
      }
    } catch (err) {
      setUpdateStatus({ type: 'error', message: 'Sunucu ile bağlantı kurulamadı.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Account Details Update Card */}
      <Card radius="lg" p="xl" className={classes.glassCard}>
        <Title order={4} c="white" mb="xl" className={classes.flexCenterGap}>
          <IconUser size={20} color="#00bcd4" />
          Hesap Bilgileri
        </Title>

        {updateStatus.type && (
          <Alert 
            icon={updateStatus.type === 'success' ? <IconCheck size={16} /> : <IconAlertCircle size={16} />} 
            title={updateStatus.type === 'success' ? 'Başarılı' : 'Hata'} 
            color={updateStatus.type === 'success' ? 'teal' : 'red'}
            mb="md"
            styles={{
              root: {
                backgroundColor: updateStatus.type === 'success' ? 'rgba(47, 158, 68, 0.15)' : 'rgba(224, 49, 49, 0.15)',
                border: updateStatus.type === 'success' ? '1px solid rgba(47, 158, 68, 0.3)' : '1px solid rgba(224, 49, 49, 0.3)',
              },
              title: { color: updateStatus.type === 'success' ? '#40c057' : '#fa5252' },
              message: { color: 'white' }
            }}
          >
            {updateStatus.message}
          </Alert>
        )}

        <form onSubmit={handleUpdateProfile}>
          <Box className={classes.flexColumnGap}>
            <TextInput
              label="Ad Soyad"
              placeholder="Adınız Soyadınız"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              leftSection={<IconUser size={16} color="gray" />}
              required
              classNames={{
                input: classes.formInput,
                label: classes.formLabel
              }}
            />

            <TextInput
              label="E-posta Adresi"
              description="Kurumsal kimlik doğrulaması için kilitlenmiştir."
              value={user.email}
              disabled
              leftSection={<IconMail size={16} color="gray" />}
              rightSection={<IconLock size={16} color="gray" />}
              classNames={{
                input: classes.formInput,
                label: classes.formLabel
              }}
              styles={{
                description: { color: 'var(--mantine-color-dimmed)', fontSize: '10px', marginBottom: '3px' },
                input: {
                  backgroundColor: 'rgba(255, 255, 255, 0.01) !important',
                  border: '1px solid rgba(255, 255, 255, 0.04) !important',
                  color: 'rgba(255, 255, 255, 0.5) !important',
                  cursor: 'not-allowed'
                }
              }}
            />

            <PasswordInput
              label="Yeni Şifre"
              placeholder="Değiştirmek istemiyorsanız boş bırakın"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              leftSection={<IconLock size={16} color="gray" />}
              classNames={{
                input: classes.formInput,
                label: classes.formLabel
              }}
              styles={{
                innerInput: {
                  color: '#fff'
                }
              }}
            />

            <PasswordInput
              label="Yeni Şifre Tekrar"
              placeholder="Yeni şifrenizi tekrar girin"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              leftSection={<IconLock size={16} color="gray" />}
              classNames={{
                input: classes.formInput,
                label: classes.formLabel
              }}
              styles={{
                innerInput: {
                  color: '#fff'
                }
              }}
            />

            <Button 
              type="submit" 
              variant="gradient" 
              gradient={{ from: 'cyan', to: 'blue' }} 
              mt="sm"
              fullWidth
              loading={loading}
            >
              Bilgileri Güncelle
            </Button>
          </Box>
        </form>
      </Card>

      {/* Privacy & Settings Card */}
      <Card radius="lg" p="xl" className={classes.glassCard}>
        <Title order={4} c="white" mb="xl" className={classes.flexCenterGap}>
          <IconShieldLock size={20} color="#00bcd4" />
          Gizlilik ve Ayarlar
        </Title>

        <Box className={classes.flexColumnSettings}>
          {/* Scalable University Selection */}
          <Box>
            <Group justify="space-between" mb="xs">
              <Text size="xs" fw={700} c="cyan" className={classes.campusTitle}>
                <IconSchool size={14} />
                AKTİF AKADEMİK KAMPÜS
              </Text>
              <Badge size="xs" color="cyan" variant="light">Ölçeklenebilir Altyapı</Badge>
            </Group>
            <Select
              placeholder="Üniversite seçin"
              data={universities}
              value={user.university_id ? String(user.university_id) : null}
              onChange={onUniversityChange}
              classNames={{
                input: classes.formInput
              }}
              styles={{
                dropdown: {
                  backgroundColor: '#0b132b',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                },
                option: {
                  color: '#fff',
                  '&[data-hovered]': {
                    backgroundColor: 'rgba(0, 188, 212, 0.1)',
                  },
                  '&[data-selected]': {
                    backgroundColor: 'rgba(0, 188, 212, 0.3)',
                  }
                }
              }}
            />
            <Text size="10px" c="dimmed" mt={5}>
              * UniLex veritabanı çoklu üniversite destekli tasarlanmıştır. Aktif kampüsünüzü dilediğiniz zaman değiştirebilirsiniz.
            </Text>
          </Box>

          <Divider my="xs" className={classes.settingsDivider} />

          <Switch
            label="Arama Geçmişini Kaydet"
            description="Asistan ile olan sohbetleriniz geçmişe kaydedilir."
            checked={historySaved}
            onChange={(e) => setHistorySaved(e.currentTarget.checked)}
            color="cyan"
            styles={{
              label: { color: 'white', fontWeight: 600 },
              description: { color: 'var(--mantine-color-dimmed)' }
            }}
          />

          <Switch
            label="Veri Anonimleştirme"
            description="Yapay zekaya gönderilen tüm veriler maskelenir."
            checked={anonymized}
            onChange={(e) => setAnonymized(e.currentTarget.checked)}
            color="cyan"
            styles={{
              label: { color: 'white', fontWeight: 600 },
              description: { color: 'var(--mantine-color-dimmed)' }
            }}
          />

          <Box className={classes.settingsFooter}>
            <Group justify="space-between" style={{ width: '100%' }}>
              <Anchor href="#" size="sm" c="dimmed" className={classes.kvkkLink}>
                KVKK Aydınlatma Metni
              </Anchor>
              <IconChevronRight size={16} color="gray" />
            </Group>

            <Button 
              variant="subtle" 
              color="red" 
              fullWidth 
              leftSection={<IconTrash size={16} />}
              justify="flex-start"
              p={0}
              h="auto"
              className={classes.deleteBtn}
              onClick={onDeleteAccount}
            >
              Hesabı Sil
            </Button>
          </Box>
        </Box>
      </Card>
    </>
  );
}
