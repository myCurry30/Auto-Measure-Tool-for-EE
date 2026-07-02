import { Layout, Tree } from "antd";
import type { DataNode } from "antd/es/tree";
import ReactMarkdown from "react-markdown";

const { Sider, Content } = Layout;

// 内嵌 Markdown 手册内容（与 Doc/用户操作手册.md 同步）
const MANUAL_MD = `# EE Power On AutoTool V2.0 — 用户操作手册

## 1. 环境准备

### 1.1 硬件需求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 / 11（64 位） |
| 示波器 | Tektronix MSO4/5/6、DPO7000、DPO5000 系列 |

### 1.2 软件依赖

需要安装 NI-VISA 驱动。

## 2. 操作流程

1. 连接示波器
2. 打开 Excel 文件
3. 配置信号参数
4. 开始测量
`;

interface Chapter {
  title: string;
  anchor: string;
  children?: Chapter[];
}

function extractChapters(md: string): Chapter[] {
  const chapters: Chapter[] = [];
  for (const line of md.split("\n")) {
    if (line.startsWith("## ") && !line.startsWith("### ")) {
      const title = line.slice(3).trim();
      if (title === "目录") continue;
      chapters.push({ title, anchor: title.replace(/\s/g, "-"), children: [] });
    } else if (line.startsWith("### ") && chapters.length > 0) {
      const title = line.slice(4).trim();
      chapters[chapters.length - 1].children!.push({ title, anchor: title.replace(/\s/g, "-") });
    }
  }
  return chapters;
}

function chaptersToTreeData(chapters: Chapter[]): DataNode[] {
  return chapters.map((ch) => ({
    title: ch.title,
    key: ch.anchor,
    children: ch.children?.map((sub) => ({ title: sub.title, key: sub.anchor, isLeaf: true })),
  }));
}

export default function HelpPage() {
  const chapters = extractChapters(MANUAL_MD);
  const treeData = chaptersToTreeData(chapters);

  const scrollTo = (keys: any[]) => {
    if (keys.length > 0) {
      const el = document.getElementById(keys[0] as string);
      el?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <Layout style={{ background: "#fff" }}>
      <Sider width={220} theme="light" style={{ borderRight: "1px solid #f0f0f0", padding: 8 }}>
        <Tree treeData={treeData} onSelect={scrollTo} defaultExpandAll />
      </Sider>
      <Content style={{ padding: "0 24px", maxHeight: "calc(100vh - 160px)", overflow: "auto" }}>
        <ReactMarkdown>{MANUAL_MD}</ReactMarkdown>
      </Content>
    </Layout>
  );
}
