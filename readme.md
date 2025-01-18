# 文档搜索助手 (Document Search Assistant)

一个基于 Python 的图形界面应用程序，用于文档内容搜索和分析。该应用程序可以提取文档中的标题，并利用 Google Search API 和 OpenAI API 进行深度内容分析。

## 功能特点

- 图形用户界面（GUI）支持
- 文件导入功能
- 标题自动提取
- Google 搜索集成
- OpenAI API 智能分析
- 结果缓存机制
- 进度显示和控制
- 结果导出功能
- 粉色主题界面设计

## 技术栈

- **Python 3.x**
- **GUI 框架**：
  - tkinter
  - ttk (主题化控件)
- **网络请求**：
  - requests
  - urllib3
- **API 集成**：
  - Google Custom Search API
  - OpenAI API
- **数据存储**：
  - SQLite3
- **其他依赖**：
  - tenacity (重试机制)
  - google-api-python-client
  - hashlib (缓存哈希)
  - threading (异步处理)

## 安装依赖

```bash
pip install -r requirements.txt
```

requirements.txt 内容：
```
tkinter
requests
urllib3
google-api-python-client
tenacity
```

## 配置要求

在运行程序前，需要配置以下 API 密钥：

1. OpenAI API 配置：
   - API Base URL
   - API Key

2. Google Search API 配置：
   - Google API Key
   - Custom Search Engine ID

## 使用说明

1. **启动程序**：
   ```bash
   python titletotext.py
   ```

2. **基本操作流程**：
   - 点击"选择文件"导入文档
   - 点击"提取标题"分析文档标题
   - 检查预览区域中的标题是否正确
   - 点击"开始处理"进行内容分析
   - 处理完成后可点击"下载结果"保存分析结果

3. **功能按钮说明**：
   - 选择文件：导入本地文档
   - 提取标题：从文档中提取标题
   - 开始处理：开始内容分析
   - 停止处理：中断当前处理
   - 下载结果：保存分析结果

## 数据缓存

- 程序使用 SQLite 数据库缓存搜索结果
- 缓存文件：`search_cache.db`
- 缓存机制可避免重复请求，提高效率

## 界面主题

采用粉色主题设计：
- 主背景：浅粉色 (#FFE6E6)
- 按钮颜色：粉色 (#FF9999)
- 文字颜色：深灰 (#4A4A4A)
- 输入框背景：更浅的粉色 (#FFF0F0)

## 注意事项

1. 确保网络连接稳定
2. API 密钥需要正确配置
3. 处理大量内容时可能需要较长时间
4. 建议定期清理缓存数据库

## 错误处理

程序包含以下错误处理机制：
- API 请求重试机制
- 网络连接错误提示
- 处理中断机制
- 结果验证检查

## 许可证

MIT License

Copyright (c) 2024 Document Search Assistant

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

## 作者

- 主要开发者：[Your Name]
- 联系邮箱：[your.email@example.com]
- GitHub：[your-github-username]

## 贡献指南

1. Fork 该项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 更新日志

### [1.0.0] - 2024-03-20
#### 添加
- 初始版本发布
- 基本文档搜索功能
- GUI 界面实现
- Google 搜索集成
- OpenAI API 集成
- 缓存系统实现

### [1.0.1] - 2024-03-21
#### 优化
- 改进错误处理机制
- 优化搜索结果缓存
- 更新用户界面样式

### [1.1.0] - 2024-03-22
#### 添加
- 新增结果导出功能
- 添加处理进度显示
- 实现处理中断功能

#### 修复
- 修复标题提取bug
- 优化内存使用
- 改进API请求稳定性