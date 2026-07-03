import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Typography } from "antd";
import {
  LinkOutlined,
  ExperimentOutlined,
  BookOutlined,
  LogoutOutlined,
} from "@ant-design/icons";
import { useAuth } from "../contexts/AuthContext";

const { Sider, Content, Footer } = Layout;

const menuItems = [
  { key: "/connect", icon: <LinkOutlined />, label: "Connect" },
  { key: "/workbench", icon: <ExperimentOutlined />, label: "工作台" },
  { key: "/help", icon: <BookOutlined />, label: "Manual" },
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { displayName, role, logout } = useAuth();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        width={180}
        theme="light"
        style={{ borderRight: "1px solid #f0f0f0" }}
      >
        <div
          style={{
            padding: "16px",
            textAlign: "center",
            fontWeight: 600,
            fontSize: 14,
          }}
        >
          EE AutoTool
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
        <div
          style={{
            position: "absolute",
            bottom: 0,
            width: "100%",
            padding: 12,
          }}
        >
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            {displayName} ({role})
          </Typography.Text>
          <Menu
            mode="inline"
            items={[
              {
                key: "logout",
                icon: <LogoutOutlined />,
                label: "Logout",
              },
            ]}
            onClick={({ key }) => key === "logout" && logout()}
            style={{ borderRight: 0 }}
          />
        </div>
      </Sider>
      <Layout>
        <Content
          style={{ padding: 24, background: "#fff", overflow: "auto" }}
        >
          <Outlet />
        </Content>
        <Footer
          style={{
            textAlign: "center",
            padding: "4px 16px",
            fontSize: 12,
            background: "#FAFAFA",
          }}
        >
          EE Power On AutoTool Web V3.0 &middot; Nettrix &middot; liujch2
        </Footer>
      </Layout>
    </Layout>
  );
}
