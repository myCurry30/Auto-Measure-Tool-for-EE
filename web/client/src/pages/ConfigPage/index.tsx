import { useState, useEffect } from "react";
import { Card, Form, Select, InputNumber, Input, Button, Tabs, Space, message, Switch, Row, Col } from "antd";
import { SaveOutlined, UploadOutlined, DownloadOutlined, FolderOpenOutlined } from "@ant-design/icons";
import { apiFetch } from "../../services/auth";

export default function ConfigPage() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [, setPaths] = useState({ file_path: "", pic_path: "", project_name: "" });
  const [pathsLoading, setPathsLoading] = useState(false);

  const [pathForm] = Form.useForm();

  useEffect(() => {
    apiFetch("/api/config/paths").then(r => r.json()).then(data => {
      setPaths(data);
      pathForm.setFieldsValue(data);
    }).catch(() => {});
  }, []);

  const handleSavePaths = async (values: any) => {
    setPathsLoading(true);
    try {
      const res = await apiFetch("/api/config/paths", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      setPaths(values);
      message.success("路径已保存");
    } catch (e: any) {
      message.error(e.message);
    } finally {
      setPathsLoading(false);
    }
  };

  const handleSave = async (values: any) => {
    setLoading(true);
    try {
      const res = await apiFetch("/api/measure/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      message.success("配置已保存");
    } catch (e: any) {
      message.error(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    try {
      const res = await apiFetch("/api/config/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: "config.json" }),
      });
      if (!res.ok) throw new Error((await res.json()).detail);
      const data = await res.json();
      message.success(`已导入 ${data.keys?.length || 0} 项配置`);
    } catch (e: any) {
      message.error(e.message);
    }
  };

  const tabItems = [
    {
      key: "signal",
      label: "信号配置",
      children: (
        <>
          <Form.Item name="test_type" label="测试类型">
            <Select options={[{ value: "sequence", label: "Sequence（时序）" }, { value: "monotony", label: "Monotony（单调性）" }]} />
          </Form.Item>
          <Form.Item name="init_row" label="起始行">
            <InputNumber min={1} />
          </Form.Item>
          <Form.Item name="pn_direction" label="P/N 方向">
            <Select options={[{ value: 1, label: "P（正向/Rise）" }, { value: 0, label: "N（反向/Fall）" }]} />
          </Form.Item>
          {[1, 2, 3, 4].map((n) => (
            <Row gutter={16} key={n}>
              <Col span={4}>
                <Form.Item name={`signal${n}_enabled`} label={`信号 ${n}`} valuePropName="checked">
                  <Switch />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name={`signal${n}_col`} label="数据列">
                  <Input placeholder="A" maxLength={2} />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name={`ch${n}_label`} label={`CH${n} 标签`}>
                  <Input placeholder={`CH${n}`} />
                </Form.Item>
              </Col>
              <Col span={4}>
                <Form.Item name={`ch${n}_enabled`} label="启用" valuePropName="checked">
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
          ))}
        </>
      ),
    },
    {
      key: "mso",
      label: "MSO 设置",
      children: (
        <>
          <Form.Item name="hor_mode" label="水平模式"><Input placeholder="AUTO" /></Form.Item>
          <Form.Item name="hor_scale" label="水平刻度"><Input placeholder="40ms" /></Form.Item>
          <Form.Item name="hor_pos" label="水平偏移"><Input placeholder="50%" /></Form.Item>
          {[1, 2, 3, 4].map((n) => (
            <Form.Item key={n} name={`ch${n}_scale`} label={`CH${n} 垂直刻度`}>
              <Input placeholder="1.0V" />
            </Form.Item>
          ))}
        </>
      ),
    },
    {
      key: "pic",
      label: "截图/数据列",
      children: (
        <>
          <Form.Item name="data_col" label="数据写入列"><Input placeholder="A" /></Form.Item>
          <Form.Item name="seq_pic_col" label="Sequence 截图列"><Input placeholder="B" /></Form.Item>
          <Form.Item name="mono_p_pic_col" label="Monotony P 截图列"><Input placeholder="B" /></Form.Item>
          <Form.Item name="mono_n_pic_col" label="Monotony N 截图列"><Input placeholder="C" /></Form.Item>
        </>
      ),
    },
  ];

  return (
    <div>
      <Card title={<><FolderOpenOutlined /> 文件路径设置</>} style={{ marginBottom: 16 }}>
        <Form layout="inline" form={pathForm} onFinish={handleSavePaths}>
          <Form.Item name="file_path" label="Excel 文件路径" style={{ minWidth: 280 }}
            tooltip="服务器可访问的 Excel 模板文件路径（例如网络共享路径 \\10.31.133.57\share\test.xlsx）">
            <Input placeholder="\\10.31.133.57\share\test.xlsx" style={{ width: 240 }} />
          </Form.Item>
          <Form.Item name="pic_path" label="截图本地保存路径" style={{ minWidth: 280 }}
            tooltip="示波器截图保存到服务器本地的目录">
            <Input placeholder="D:\Pic" style={{ width: 240 }} />
          </Form.Item>
          <Form.Item name="project_name" label="示波器保存路径" style={{ minWidth: 280 }}
            tooltip="示波器磁盘上保存截图的目录路径（如 C:\AutoTool）">
            <Input placeholder="C:\AutoTool" style={{ width: 240 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={pathsLoading} icon={<SaveOutlined />}>
              保存路径
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="测量配置" extra={
        <Space>
          <Button icon={<UploadOutlined />} onClick={handleImport}>导入</Button>
          <Button icon={<DownloadOutlined />} onClick={() => message.info("请使用导出接口")}>导出</Button>
        </Space>
      }>
        <Form form={form} layout="vertical" onFinish={handleSave}
          initialValues={{ test_type: "sequence", init_row: 1, pn_direction: 1,
            signal1_enabled: true, signal2_enabled: false, signal3_enabled: false, signal4_enabled: false,
            signal1_col: "A", signal2_col: "B", signal3_col: "C", signal4_col: "D",
            ch1_enabled: true, ch2_enabled: false, ch3_enabled: false, ch4_enabled: false }}>
          <Tabs items={tabItems} />
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
