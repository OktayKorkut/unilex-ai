import { Paper, Title, Group, Text } from "@mantine/core";
import { LineChart } from "@mantine/charts";

export interface LoadHistoryPoint {
  hour_utc: string;
  chat_count: number;
  event_count: number;
}

interface Props {
  data: LoadHistoryPoint[];
}

export function SystemLoadChart({ data }: Props) {
  const formatted = data.map((p) => ({
    saat: new Date(p.hour_utc).toLocaleTimeString("tr-TR", {
      hour: "2-digit",
      minute: "2-digit",
    }),
    "Sohbet sorguları": p.chat_count,
    "Sistem olayları": p.event_count,
  }));

  return (
    <Paper p="lg" radius="md" withBorder mb="lg">
      <Group justify="space-between" mb="md">
        <Title order={3} fz="md" fw={600}>
          Son 24 Saatlik Sistem Yükü
        </Title>
        <Text c="dimmed" size="xs">
          Saatlik aktivite
        </Text>
      </Group>
      <LineChart
        h={260}
        data={formatted}
        dataKey="saat"
        series={[
          { name: "Sohbet sorguları", color: "blue.5" },
          { name: "Sistem olayları", color: "orange.5" },
        ]}
        curveType="monotone"
        withLegend
        withDots={false}
        tickLine="x"
        gridAxis="xy"
      />
    </Paper>
  );
}
