import { useState, useCallback, useEffect } from "react";
import { Card, Form, Select, InputNumber, Input, Button, Tabs, Space, message, Switch, Row, Col, Tag, Timeline, Statistic } from "antd";
import {
  SaveOutlined, UploadOutlined, FolderOpenOutlined,
  PlayCircleOutlined, LeftOutlined, RightOutlined, FastForwardOutlined, SwapOutlined,
} from "@ant-design/icons";
import { apiFetch } from "../../services/auth";
import { useWebSocket } from "../../hooks/useWebSocket";

interface LogEntry { ts: string; level: string; message: string; }
interface ExcelInfo { file_path: string; active_sheet: string; sheet_names: string[]; }

const levelColors: Record<string, string> = { info: "blue", warning: "orange", error: "red" };

export default function WorkbenchPage() {
  // ── File paths ──
  const [pathsLoading, setPathsLoading] = useState(false);
  const [pathForm] = Form.useForm();

  // ── Excel info ──
  const [activeSheet, setActiveSheet] = useState<string>("");
  const [sheetNames, setSheetNames] = useState<string[]>([]);
  const [selectedSheet, setSelectedSheet] = useState<string>("");
  const [sheetSwitching, setSheetSwitching] = useState(false);

  // ── Measurement config ──
  const [configForm] = Form.useForm();
  const [configLoading, setConfigLoading] = useState(false);

  // ── Measurement control ──
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [status, setStatus] = useState<any>({});
  const [jumpTarget, setJumpTarget] = useState<number>(0);
  const [running, setRunning] = useState(false);

  // ── Init ──
  useEffect(() => {
    apiFetch("/api/config/paths").then(r => r.json()).then(data => pathForm.setFieldsValue(data)).catch(() => {});
    apiFetch("/api/excel/info").then(r => r.json()).then((data: ExcelInfo) => {
      if (data.active_sheet) {
        setActiveSheet(data.active_sheet);
        setSelectedSheet(data.active_sheet);
        setSheetNames(data.sheet_names || []);
      }
    }).catch(() => {});
    apiFetch("/api/measure/status").then(r => r.json()).then(setStatus).catch(() => {});
  }, []);

  // ── WebSocket ──
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

  // ── Actions ──
  const handleSavePaths = async (values: any) => {
    setPathsLoading(true);
    try {
      const res = await apiFetch("/api/config/paths", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(values) });
      if (!res.ok) throw new Error((await res.json()).detail);
      message.success("路径已保存");

      if (values.file_path) {
        try {
          const r2 = await apiFetch("/api/excel/open", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ file_path: values.file_path }) });
          if (r2.ok) {
            const data: ExcelInfo = await r2.json();
            setActiveSheet(data.active_sheet);
            setSheetNames(data.sheet_names);
            setSelectedSheet(data.active_sheet);
            message.success(`Excel 已打开，当前 Sheet: ${data.active_sheet}`);
          } else {
            message.warning(`Excel 打开失败: ${(await r2.json()).detail}`);
          }
        } catch (e: any) { message.warning(`Excel 打开失败: ${e.message}`); }
      }
    } catch (e: any) { message.error(e.message); }
    finally { setPathsLoading(false); }
  };

  const handleSwitchSheet = async () => {
    if (!selectedSheet) return;
    setSheetSwitching(true);
    try {
      const res = await apiFetch("/api/excel/activate-sheet", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sheet_name: selectedSheet }) });
      if (!res.ok) throw new Error((await res.json()).detail);
      setActiveSheet(selectedSheet);
      message.success(`已切换到 ${selectedSheet}`);
    } catch (e: any) { message.error(e.message); }
    finally { setSheetSwitching(false); }
  };

  const handleSaveConfig = async (values: any) => {
    setConfigLoading(true);
    try {
      const res = await apiFetch("/api/measure/config", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(values) });
      if (!res.ok) throw new Error((await res.json()).detail);
      message.success("配置已保存");
    } catch (e: any) { message.error(e.message); }
    finally { setConfigLoading(false); }
  };

  const handleImport = async () => {
    try {
      const res = await apiFetch("/api/config/import", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ file_path: "config.json" }) });
      if (!res.ok) throw new Error((await res.json()).detail);
      message.success(`已导入 ${(await res.json()).keys?.length || 0} 项配置`);
    } catch (e: any) { message.error(e.message); }
  };

  const fetchStatus = async () => {
    try { const res = await apiFetch("/api/measure/status"); setStatus(await res.json()); } catch {}
  };

  const doAction = async (endpoint: string, body?: any) => {
    setRunning(true);
    try {
      const res = await apiFetch(endpoint, { method: "POST", headers: body ? { "Content-Type": "application/json" } : {}, body: body ? JSON.stringify(body) : undefined });
      if (!res.ok) throw new Error((await res.json()).detail);
      fetchStatus();
    } catch (e: any) { message.error(e.message); }
    finally { setRunning(false); }
  };

  // ── Tab items ──
  const tabItems = [
    { key: "signal", label: "信号配置", children: (
      <>
        <Form.Item name="test_type" label="测试类型">
          <Select options={[{ value: "sequence", label: "Sequence（时序）" }, { value: "monotony", label: "Monotony（单调性）" }]} />
        </Form.Item>
        <Form.Item name="init_row" label="起始行"><InputNumber min={1} /></Form.Item>
        <Form.Item name="pn_direction" label="P/N 方向">
          <Select options={[{ value: 1, label: "P（正向/Rise）" }, { value: 0, label: "N（反向/Fall）" }]} />
        </Form.Item>
        {[1, 2, 3, 4].map((n) => (
          <Row gutter={16} key={n}>
            <Col span={4}><Form.Item name={`signal${n}_enabled`} label={`信号 ${n}`} valuePropName="checked"><Switch /></Form.Item></Col>
            <Col span={6}><Form.Item name={`signal${n}_col`} label="数据列"><Input placeholder="A" maxLength={2} /></Form.Item></Col>
            <Col span={6}><Form.Item name={`ch${n}_label`} label={`CH${n} 标签`}><Input placeholder={`CH${n}`} /></Form.Item></Col>
            <Col span={4}><Form.Item name={`ch${n}_enabled`} label="启用" valuePropName="checked"><Switch /></Form.Item></Col>
          </Row>
        ))}
      </>
    )},
    { key: "mso", label: "MSO 设置", children: (
      <>
        <Form.Item name="hor_mode" label="水平模式"><Input placeholder="AUTO" /></Form.Item>
        <Form.Item name="hor_scale" label="水平刻度"><Input placeholder="40ms" /></Form.Item>
        <Form.Item name="hor_pos" label="水平偏移"><Input placeholder="50%" /></Form.Item>
        {[1, 2, 3, 4].map((n) => (
          <Form.Item key={n} name={`ch${n}_scale`} label={`CH${n} 垂直刻度`}><Input placeholder="1.0V" /></Form.Item>
        ))}
      </>
    )},
    { key: "pic", label: "截图/数据列", children: (
      <>
        <Form.Item name="data_col" label="数据写入列"><Input placeholder="A" /></Form.Item>
        <Form.Item name="seq_pic_col" label="Sequence 截图列"><Input placeholder="B" /></Form.Item>
        <Form.Item name="mono_p_pic_col" label="Monotony P 截图列"><Input placeholder="B" /></Form.Item>
        <Form.Item name="mono_n_pic_col" label="Monotony N 截图列"><Input placeholder="C" /></Form.Item>
      </>
    )},
  ];

  return (
    <div>
      {/* Card 1: File Paths */}
      <Card title={<><FolderOpenOutlined /> 文件路径设置</>} style={{ marginBottom: 16 }}>
        <Form layout="inline" form={pathForm} onFinish={handleSavePaths}>
          <Form.Item name="file_path" label="Excel 文件路径" style={{ minWidth: 280 }}
            tooltip="服务器可访问的 Excel 文件路径（例如网络共享路径 \\IP\share\test.xlsx）">
            <Input placeholder="\\10.31.133.57\share\test.xlsx" style={{ width: 240 }} />
          </Form.Item>
          <Form.Item name="pic_path" label="截图本地保存路径" style={{ minWidth: 280 }}>
            <Input placeholder="D:\Pic" style={{ width: 240 }} />
          </Form.Item>
          <Form.Item name="project_name" label="示波器保存路径" style={{ minWidth: 280 }}>
            <Input placeholder="C:\AutoTool" style={{ width: 240 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={pathsLoading} icon={<SaveOutlined />}>保存路径</Button>
          </Form.Item>
        </Form>
      </Card>

      {/* Card 2: Excel Info */}
      <Card title="Excel 信息" style={{ marginBottom: 16 }}>
        <Space size="middle">
          <span>当前 Sheet：</span>
          <Tag color="blue">{activeSheet || "未打开"}</Tag>
          <Select
            style={{ width: 200 }}
            value={selectedSheet || undefined}
            onChange={(v) => setSelectedSheet(v)}
            options={sheetNames.map(s => ({ value: s, label: s }))}
            placeholder="选择 Sheet"
            notFoundContent="请先保存 Excel 路径"
          />
          <Button icon={<SwapOutlined />} onClick={handleSwitchSheet} loading={sheetSwitching} disabled={!selectedSheet}>
            切换
          </Button>
        </Space>
      </Card>

      {/* Card 3: Measurement Control */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}><Card><Statistic title="当前行" value={status.row || 0} /></Card></Col>
        <Col span={6}><Card><Statistic title="总条目" value={status.total || 0} /></Card></Col>
        <Col span={6}><Card><Statistic title="当前条目" value={status.current_item || "-"} /></Card></Col>
        <Col span={6}><Card><Statistic title="连接状态" value={status.connected ? "已连接" : "未连接"}
          valueStyle={{ color: status.connected ? "#52c41a" : "#ff4d4f" }} /></Card></Col>
      </Row>

      <Card title="导航控制" style={{ marginBottom: 16 }}>
        <Space size="middle">
          <Button icon={<LeftOutlined />} onClick={() => doAction("/api/measure/last")} disabled={running}>上一条</Button>
          <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => doAction("/api/measure/go")} loading={running}>GO</Button>
          <Button icon={<RightOutlined />} onClick={() => doAction("/api/measure/next")} disabled={running}>下一条</Button>
          <InputNumber min={1} value={jumpTarget} onChange={(v) => setJumpTarget(v || 0)} placeholder="目标行" />
          <Button icon={<FastForwardOutlined />} onClick={() => doAction("/api/measure/jump", { target_row: jumpTarget })} disabled={running}>Jump</Button>
        </Space>
      </Card>

      {/* Card 4: Config Tabs */}
      <Card title="测量配置" extra={
        <Space>
          <Button icon={<UploadOutlined />} onClick={handleImport}>导入</Button>
          <Button onClick={() => message.info("请使用导出接口")}>导出</Button>
        </Space>
      } style={{ marginBottom: 16 }}>
        <Form form={configForm} layout="vertical" onFinish={handleSaveConfig}
          initialValues={{ test_type: "sequence", init_row: 1, pn_direction: 1,
            signal1_enabled: true, signal2_enabled: false, signal3_enabled: false, signal4_enabled: false,
            signal1_col: "A", signal2_col: "B", signal3_col: "C", signal4_col: "D",
            ch1_enabled: true, ch2_enabled: false, ch3_enabled: false, ch4_enabled: false }}>
          <Tabs items={tabItems} />
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={configLoading} icon={<SaveOutlined />}>保存配置</Button>
          </Form.Item>
        </Form>
      </Card>

      {/* Card 5: Log */}
      <Card title="实时日志" bodyStyle={{ maxHeight: 400, overflow: "auto" }}>
        <Timeline items={logs.map((l, i) => ({ key: i, color: levelColors[l.level] || "gray",
          children: <><Tag>{l.ts}</Tag> {l.message}</> }))} />
      </Card>
    </div>
  );
}
