import { useState, useEffect, useCallback } from "react";
import { Card, Form, Select, Input, Button, Badge, Descriptions, Space, message } from "antd";
import { ApiOutlined, DisconnectOutlined } from "@ant-design/icons";
import { apiFetch } from "../../services/auth";
import { useWebSocket } from "../../hooks/useWebSocket";

interface ConnectStatus {
  connected: boolean;
  model?: string;
  addr?: string;
}

export default function ConnectPage() {
  const [status, setStatus] = useState<ConnectStatus>({ connected: false });
  const [connecting, setConnecting] = useState(false);

  const onWsMessage = useCallback((data: any) => {
    if (data.type === "heartbeat") {
      setStatus({ connected: data.connected, model: data.model, addr: data.scope_addr });
    }
  }, []);
  useWebSocket(onWsMessage);

  const fetchStatus = async () => {
    try {
      const res = await apiFetch("/api/connect/status");
      const data = await res.json();
      setStatus(data);
    } catch {}
  };

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 10000);
    return () => clearInterval(timer);
  }, []);

  const handleConnect = async (values: any) => {
    setConnecting(true);
    try {
      const res = await apiFetch("/api/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      const data = await res.json();
      setStatus({ connected: true, model: data.model, addr: data.addr });
      message.success(`已连接 ${data.model}`);
    } catch (e: any) {
      message.error(e.message || "连接失败");
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await apiFetch("/api/connect", { method: "DELETE" });
      setStatus({ connected: false });
      message.info("已断开");
    } catch {
      message.error("断开失败");
    }
  };

  return (
    <div>
      <Card title="示波器连接" style={{ maxWidth: 600, marginBottom: 16 }}>
        <Form
          layout="vertical"
          onFinish={handleConnect}
          initialValues={{ method: "usb_gpib", port: 4000, use_socket: false }}
        >
          <Form.Item name="method" label="连接方式">
            <Select
              options={[
                { value: "usb_gpib", label: "GPIB / USB（自动扫描）" },
                { value: "ip", label: "TCP/IP（手动输入 IP）" },
              ]}
            />
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.method !== cur.method}>
            {({ getFieldValue }) =>
              getFieldValue("method") === "ip" ? (
                <>
                  <Form.Item name="ip" label="IP 地址" rules={[{ required: true }]}>
                    <Input placeholder="192.168.1.100" />
                  </Form.Item>
                  <Form.Item name="port" label="Port">
                    <Input type="number" />
                  </Form.Item>
                  <Form.Item name="use_socket" label="Socket 模式" valuePropName="checked">
                    <Select options={[{ value: false, label: "INSTR" }, { value: true, label: "SOCKET" }]} />
                  </Form.Item>
                </>
              ) : null
            }
          </Form.Item>

          <Space>
            <Button type="primary" htmlType="submit" loading={connecting} icon={<ApiOutlined />}>
              连接
            </Button>
            <Button danger onClick={handleDisconnect} disabled={!status.connected} icon={<DisconnectOutlined />}>
              断开
            </Button>
          </Space>
        </Form>
      </Card>

      <Card title="连接状态">
        <Descriptions column={2}>
          <Descriptions.Item label="状态">
            <Badge status={status.connected ? "success" : "default"} text={status.connected ? "已连接" : "未连接"} />
          </Descriptions.Item>
          <Descriptions.Item label="型号">{status.model || "-"}</Descriptions.Item>
          <Descriptions.Item label="地址" span={2}>{status.addr || "-"}</Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
}
