import { useState } from "react";
import { Card, Input, Button, Typography, Space, message } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

const { Title, Text } = Typography;

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Already authenticated: redirect
  if (isAuthenticated) {
    navigate("/connect", { replace: true });
    return null;
  }

  const handleLogin = async () => {
    if (!username.trim()) {
      message.warning("Please enter your username");
      return;
    }
    setLoading(true);
    try {
      await login(username.trim());
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Login failed";
      message.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "#f5f5f5",
      }}
    >
      <Card style={{ width: 400 }} title="EE Power On AutoTool">
        <Space
          direction="vertical"
          size="middle"
          style={{ width: "100%" }}
        >
          <div style={{ textAlign: "center" }}>
            <Title level={4}>Welcome</Title>
            <Text type="secondary">
              Enter your Windows username to login
            </Text>
          </div>
          <Input
            prefix={<UserOutlined />}
            placeholder="Username (e.g., domain\\user)"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onPressEnter={handleLogin}
            size="large"
            autoFocus
          />
          <Button
            type="primary"
            block
            size="large"
            loading={loading}
            onClick={handleLogin}
          >
            Login
          </Button>
        </Space>
      </Card>
    </div>
  );
}
