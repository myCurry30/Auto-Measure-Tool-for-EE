import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Form, Input, Button, Alert, Typography } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { useAuth } from "../../contexts/AuthContext";

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 已登录则跳转
  if (isAuthenticated) {
    navigate("/connect", { replace: true });
    return null;
  }

  const handleSubmit = async (values: { username: string }) => {
    setError(null);
    setLoading(true);
    try {
      await login(values.username);
    } catch (e: any) {
      setError(e.message || "登录失败，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      }}
    >
      <div style={{ textAlign: "center", marginBottom: 32, color: "#fff" }}>
        <Typography.Title level={2} style={{ color: "#fff", marginBottom: 4 }}>
          ⚡ EE Power On AutoTool
        </Typography.Title>
        <Typography.Text style={{ color: "rgba(255,255,255,0.8)", fontSize: 16 }}>
          示波器自动测量系统
        </Typography.Text>
      </div>

      <Card style={{ width: 400, borderRadius: 8 }}>
        <Form onFinish={handleSubmit} layout="vertical" size="large">
          <Form.Item
            name="username"
            rules={[{ required: true, message: "请输入用户名" }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入您的用户名"
              autoFocus
            />
          </Form.Item>

          {error && (
            <Alert
              type="error"
              message={error}
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {loading ? "正在验证设备…" : "进  入"}
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Typography.Text style={{ color: "rgba(255,255,255,0.5)", marginTop: 24, fontSize: 12 }}>
        如需开通权限，请联系管理员绑定笔记本
      </Typography.Text>
    </div>
  );
}
