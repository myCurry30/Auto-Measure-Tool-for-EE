import { useState, useCallback, useEffect } from "react";
import { Card, Button, Space, InputNumber, Timeline, Tag, Statistic, Row, Col, message } from "antd";
import { PlayCircleOutlined, LeftOutlined, RightOutlined, FastForwardOutlined } from "@ant-design/icons";
import { apiFetch } from "../../services/auth";
import { useWebSocket } from "../../hooks/useWebSocket";

interface LogEntry {
  ts: string;
  level: string;
  message: string;
}

const levelColors: Record<string, string> = { info: "blue", warning: "orange", error: "red" };

export default function MeasurePage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [status, setStatus] = useState<any>({});
  const [jumpTarget, setJumpTarget] = useState<number>(0);
  const [running, setRunning] = useState(false);

  const onWsMessage = useCallback((data: any) => {
    if (data.type === "log") {
      setLogs((prev) => [...prev.slice(-99), { ts: data.ts, level: data.level, message: data.message }]);
    } else if (data.type === "heartbeat") {
      setStatus((prev: any) => ({ ...prev, connected: data.connected, model: data.model }));
    } else if (data.type === "progress") {
      setStatus((prev: any) => ({ ...prev, current: data.current, total: data.total, item: data.item }));
    }
  }, []);
  useWebSocket(onWsMessage);

  const fetchStatus = async () => {
    try {
      const res = await apiFetch("/api/measure/status");
      setStatus(await res.json());
    } catch {}
  };
  useEffect(() => { fetchStatus(); }, []);

  const doAction = async (endpoint: string, body?: any) => {
    setRunning(true);
    try {
      const res = await apiFetch(endpoint, {
        method: "POST",
        headers: body ? { "Content-Type": "application/json" } : {},
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      fetchStatus();
    } catch (e: any) {
      message.error(e.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}><Card><Statistic title="当前行" value={status.row || 0} /></Card></Col>
        <Col span={6}><Card><Statistic title="总条目" value={status.total || 0} /></Card></Col>
        <Col span={6}><Card><Statistic title="当前条目" value={status.current_item || "-"} /></Card></Col>
        <Col span={6}><Card>
          <Statistic title="连接状态" value={status.connected ? "已连接" : "未连接"}
            valueStyle={{ color: status.connected ? "#52c41a" : "#ff4d4f" }} />
        </Card></Col>
      </Row>

      <Card title="导航控制" style={{ marginBottom: 16 }}>
        <Space size="middle">
          <Button icon={<LeftOutlined />} onClick={() => doAction("/api/measure/last")} disabled={running}>
            上一条
          </Button>
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => doAction("/api/measure/go")} loading={running}>
            GO
          </Button>
          <Button icon={<RightOutlined />} onClick={() => doAction("/api/measure/next")} disabled={running}>
            下一条
          </Button>
          <InputNumber min={1} value={jumpTarget} onChange={(v) => setJumpTarget(v || 0)} placeholder="目标行" />
          <Button icon={<FastForwardOutlined />} onClick={() => doAction("/api/measure/jump", { target_row: jumpTarget })} disabled={running}>
            Jump
          </Button>
        </Space>
      </Card>

      <Card title="实时日志" bodyStyle={{ maxHeight: 400, overflow: "auto" }}>
        <Timeline
          items={logs.map((l, i) => ({
            key: i,
            color: levelColors[l.level] || "gray",
            children: <><Tag>{l.ts}</Tag> {l.message}</>,
          }))}
        />
      </Card>
    </div>
  );
}
