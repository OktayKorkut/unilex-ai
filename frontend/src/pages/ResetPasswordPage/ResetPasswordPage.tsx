import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Container, Paper, Title, Text, PasswordInput, Button, Alert, Loader, Center, Box } from '@mantine/core';
import { IconAlertCircle, IconCheck } from '@tabler/icons-react';
import { API_BASE_URL } from '../../config';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!token) {
      setErrorMsg('Geçersiz sıfırlama bağlantısı. Lütfen yeni bir talepte bulunun.');
      return;
    }
    if (newPassword.length < 6) {
      setErrorMsg('Şifre en az 6 karakter olmalıdır.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMsg('Şifreler eşleşmiyor.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Şifre sıfırlama başarısız.');
      }
      setSuccess(true);
      setTimeout(() => navigate('/'), 3000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Bir hata oluştu. Bağlantınızın süresi dolmuş olabilir.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Center style={{ minHeight: '100vh' }} bg="gray.0">
      <Container size={420} w="100%">
        <Paper withBorder shadow="md" p="xl" radius="md">
          <Title order={2} ta="center" mb="xs">Şifre Sıfırlama</Title>
          <Text size="sm" c="dimmed" ta="center" mb="xl">
            Hesabınız için yeni bir şifre belirleyin.
          </Text>

          {success ? (
            <Box>
              <Alert icon={<IconCheck size={16} />} color="green" title="Başarılı!" mb="md">
                Şifreniz güncellendi. Giriş sayfasına yönlendiriliyorsunuz...
              </Alert>
              <Button fullWidth radius="xl" color="cyan" onClick={() => navigate('/')}>
                Giriş Sayfasına Git
              </Button>
            </Box>
          ) : (
            <form onSubmit={handleSubmit}>
              {errorMsg && (
                <Alert icon={<IconAlertCircle size={16} />} color="red" title="Hata" mb="md">
                  {errorMsg}
                </Alert>
              )}

              {!token && (
                <Alert color="orange" mb="md">
                  Geçersiz veya eksik sıfırlama kodu. E-posta'daki bağlantıya tam olarak tıkladığınızdan emin olun.
                </Alert>
              )}

              <PasswordInput
                label="Yeni Şifre"
                placeholder="En az 6 karakter"
                required
                mb="md"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              <PasswordInput
                label="Yeni Şifre (Tekrar)"
                placeholder="Şifrenizi tekrar girin"
                required
                mb="xl"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />

              <Button fullWidth radius="xl" color="cyan" size="md" type="submit" disabled={loading || !token}>
                {loading ? <Loader size="xs" color="white" /> : 'Şifremi Güncelle'}
              </Button>
            </form>
          )}
        </Paper>
      </Container>
    </Center>
  );
}
