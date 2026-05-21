import { Card, Box, Avatar, Badge, Title, Text, Grid } from '@mantine/core';
import classes from '../../pages/ProfilePage/ProfilePage.module.css';

interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  university_id?: number;
}

interface ProfileCardProps {
  user: UserProfile;
  roleInfo: { label: string; color: string };
  sessionsCount: number;
  usedQueries: number;
}

export default function ProfileCard({ user, roleInfo, sessionsCount, usedQueries }: ProfileCardProps) {
  return (
    <Card radius="lg" p="xl" className={classes.glassCard}>
      <Box style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
        <div className={classes.avatarWrapper}>
          <Avatar color="cyan" size={120} radius="xl" className={classes.avatarEl}>
            {user.full_name.split(' ').map(n => n[0]).join('').toUpperCase()}
          </Avatar>
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
            <Text size="xl" fw={900} c="grape" className={classes.monoFont}>{usedQueries}</Text>
            <Text size="xs" c="dimmed">Toplam Sorgu</Text>
          </Grid.Col>
        </Grid>
      </Box>
    </Card>
  );
}
