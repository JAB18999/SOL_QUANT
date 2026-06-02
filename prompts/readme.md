# Prompts 目录
 
本目录用于存放日常使用的 AI 提示词（Prompt），全部以 Markdown 格式保存，方便快速复制使用。
 
## 目录结构
 
- `01_市场分析提示词.md` - SOL 实时行情分析、趋势判断
- `02_策略优化提示词.md` - 网格参数优化、回测改进
- `03_回测报告解读.md` - 分析 sol_grid_analyzer.py 输出结果
- `04_风险评估提示词.md` - 清算价、仓位管理、杠杆评估
- `05_日常交易决策.md` - 每日开单决策模板
- `06_OKX数据分析.md` - 配合 okx_data_downloader.py 使用
 
## 使用方法
 
1. 直接复制 .md 文件中的提示词到 ChatGPT/Claude/Gemini
2. 根据当天数据替换 `[变量]`
3. 可自行添加新的 .md 文件
 
> 提示：所有提示词已针对本仓库的 `sol_grid_analyzer` 策略特点定制（5层网格、60x杠杆、RSI触发、ATR间距）
