# RSI Statistical Analysis Framework (RSI_FRAME)

**项目目标**  
对 SOL（或其他标的）在 15 分钟与 30 分钟 K 线上，对 RSI14 指标进行结构化、工程化、可复现的统计与建模分析，构建完整的 RSI 行为数据库，并扩展至多维量价结构研究，为后续量化策略开发提供坚实的数据基础。

**适用周期**：15 分钟 K 线、30 分钟 K 线  
**时区**：统一使用东八区（北京时间，UTC+8）

---

## 1. 基础设定

### 1.1 时间跨度
分别独立统计以下时间窗口：

- 最近 60 天
- 最近 30 天
- 最近 15 天
- 最近 7 天
- 最近 3 天

### 1.2 RSI 参数
- 指标：RSI14
- 计算依据：每根 K 线的 **收盘价**
- 中轴：50
- 经典阈值：30（超卖）、70（超买）

### 1.3 RSI 区间划分（严格全覆盖、无重叠）

| 区间名称     | 条件                  |
|--------------|-----------------------|
| 超卖区       | RSI14 ≤ 30            |
| 中性偏空区   | 30 < RSI14 ≤ 50       |
| 中性偏多区   | 50 < RSI14 ≤ 70       |
| 超买区       | RSI14 > 70            |

**原则**：每个 RSI14 值必须且只能归属一个区间。

---

## 2. 核心数据结构（工程级定义）

### 2.1 Raw Kline Data（原始K线表）

| 字段           | 类型       | 说明                                       |
|----------------|------------|--------------------------------------------|
| timestamp      | datetime   | K线结束时间（北京时间）                    |
| open           | float      | 开盘价                                     |
| high           | float      | 最高价                                     |
| low            | float      | 最低价                                     |
| close          | float      | 收盘价                                     |
| volume         | float      | 成交量                                     |
| rsi14          | float      | 本K线RSI14值（保留4位小数）                |
| rsi_zone       | string     | 所属区间                                   |
| price_return   | float      | 单根K线收益率 = (close - open)/open        |
| vwap           | float      | 当根K线VWAP（高低收三均加权）              |

---

### 2.2 Zone Event Table（区间事件表 - 核心）

记录每一次完整进入某 RSI 区间的事件。

| 字段                       | 类型       | 说明                                                          |
|----------------------------|------------|---------------------------------------------------------------|
| event_id                   | int        | 自增ID                                                        |
| symbol                     | string     | 交易对（如 SOLUSDT）                                         |
| timeframe                  | string     | 15m / 30m                                                     |
| zone_name                  | string     | 区间名称                                                      |
| start_time                 | datetime   | 进入区间的第一根K线时间                                       |
| end_time                   | datetime   | 离开区间的前一根K线时间                                       |
| kline_count                | int        | 持续K线数量                                                   |
| duration_minutes           | int        | 持续分钟数                                                    |
| start_close                | float      | 第一根K线收盘价                                               |
| end_close                  | float      | 最后一根K线收盘价                                             |
| zone_return                | float      | 区间整体收益率 (%)                                            |
| mfe                        | float      | 最大有利偏移                                                  |
| mae                        | float      | 最大不利偏移                                                  |
| avg_single_return          | float      | 单根K线平均收益率                                             |
| volume_sum                 | float      | 区间内总成交量                                                |
| volume_ratio_vs_avg        | float      | 成交量相对均值倍数（区间平均成交量 / 全样本平均成交量）       |
| is_single_kline            | boolean    | 是否仅持续1根K线                                              |
| divergence_flag            | string     | 是否存在价格-RSI背离（none / bullish / bearish）              |

---

### 2.3 Transition Table（区间转换表）

| 字段           | 类型       | 说明                              |
|----------------|------------|-----------------------------------|
| transition_id  | int        | 自增ID                            |
| from_zone      | string     | 转换前区间                        |
| to_zone        | string     | 转换后区间                        |
| timestamp      | datetime   | 转换时间                          |
| price          | float      | 转换时收盘价                      |
| timeframe      | string     | 15m / 30m                         |

---

### 2.4 Summary Statistics Table（汇总统计表）

| 字段                          | 类型     | 说明                                  |
|-------------------------------|----------|---------------------------------------|
| timeframe                     | string   | 15m / 30m                             |
| period_days                   | int      | 3 / 7 / 15 / 30 / 60                  |
| zone_name                     | string   | 区间名称                              |
| total_kline_count             | int      | 总K线数                               |
| kline_ratio                   | float    | 占比                                  |
| total_event_count             | int      | 事件总次数                            |
| avg_kline_per_event           | float    | 平均K线数                             |
| max_kline_per_event           | int      | 最大K线数                             |
| avg_duration_minutes          | float    | 平均持续时间                          |
| avg_zone_return               | float    | 平均收益率                            |
| max_zone_return               | float    | 最大收益率                            |
| min_zone_return               | float    | 最小收益率                            |
| median_zone_return            | float    | 中位数收益率                          |
| win_rate                      | float    | 区间事件胜率（%）                     |
| avg_single_kline_return       | float    | 单K线平均涨跌幅                       |
| max_single_up_return          | float    | 单K线最大涨幅                         |
| max_single_down_return        | float    | 单K线最大跌幅                         |
| avg_volume_ratio              | float    | 区间平均成交量比                      |
| divergence_count              | int      | 背离次数                              |

---

## 3. 统计规则

### 3.1 事件定义
- 进入：收盘价确认 RSI14 进入区间
- 离开：收盘价确认 RSI14 离开区间的前一根K线
- 连续相同区间记为 1 次事件
- 单根K线事件标记并保留

### 3.2 转换定义
- from_zone ≠ to_zone 即记录
- 允许跨区跳跃转换

### 3.3 收益率
- `zone_return = (end_close - start_close) / start_close`
- `single_return = (close - open) / open`

---

## 4. 扩展模块（高级研究层）

### 4.1 成交量加权统计

**目标**：评估各 RSI 区间是否伴随显著的成交量结构变化，识别“放量信号区”。

#### 计算字段
- 区间总成交量
- 区间平均K线成交量
- 成交量比：区间成交量均值 / 全样本成交量均值
- 区间内 VWAP
- 价格相对 VWAP 偏离度

#### 输出表：`zone_volume_stat`

| 字段                     | 类型    | 说明                       |
|--------------------------|---------|----------------------------|
| zone_name                | string  | 区间名称                   |
| avg_volume               | float   | 平均成交量                 |
| volume_ratio_vs_global   | float   | 相对全样本均值倍数         |
| avg_vwap_deviation       | float   | VWAP偏离均值               |
| high_volume_event_count  | int     | 高于均值2倍的事件次数      |

---

### 4.2 RSI 与价格背离统计

**目标**：识别经典的顶背离与底背离结构，量化背离的发生频率与有效性。

#### 背离定义
- **顶背离**：价格创新高，RSI14未创新高
- **底背离**：价格创新低，RSI14未创新低
- 比较窗口：默认 14 根K线

#### 输出表：`divergence_event`

| 字段              | 类型     | 说明                            |
|-------------------|----------|---------------------------------|
| divergence_id     | int      | 自增ID                          |
| type              | string   | bullish / bearish               |
| timestamp         | datetime | 发生时间                        |
| price             | float    | 当时价格                        |
| rsi14             | float    | 当时RSI                         |
| zone_name         | string   | 当时所属RSI区间                 |
| forward_return_5  | float    | 之后5根K线收益率                |
| forward_return_10 | float    | 之后10根K线收益率               |
| forward_return_20 | float    | 之后20根K线收益率               |
| success_flag      | boolean  | 是否朝预期方向运行              |

---

### 4.3 RSI 状态转移概率矩阵（Markov Chain）

**目标**：构建 RSI 区间状态的马尔可夫转移模型，研究状态切换的概率结构。

#### 4×4 转移矩阵结构

|              | →超卖区 | →中性偏空 | →中性偏多 | →超买区 |
|--------------|---------|-----------|-----------|---------|
| 超卖区       | p11     | p12       | p13       | p14     |
| 中性偏空     | p21     | p22       | p23       | p24     |
| 中性偏多     | p31     | p32       | p33       | p34     |
| 超买区       | p41     | p42       | p43       | p44     |

#### 输出表：`markov_matrix`

| 字段        | 类型    | 说明           |
|-------------|---------|----------------|
| from_zone   | string  | 起始状态       |
| to_zone     | string  | 目标状态       |
| count       | int     | 转换次数       |
| probability | float   | 转换概率       |

#### 拓展指标
- 稳态分布（Stationary Distribution）
- 平均停留时间（Expected Holding Time）

---

### 4.4 多时间框架共振分析（MTF Resonance）

**目标**：分析 15m 与 30m RSI 状态共振时的市场行为特征。

#### 共振状态定义

| 共振类别        | 条件                                  |
|-----------------|---------------------------------------|
| 强共振多        | 15m 与 30m 同处中性偏多 或 超买区     |
| 强共振空        | 15m 与 30m 同处中性偏空 或 超卖区     |
| 弱共振          | 15m 与 30m 同侧但不同区间             |
| 背离            | 15m 与 30m 处于相反方向区间           |

#### 输出表：`mtf_resonance_stat`

| 字段                 | 类型    | 说明                          |
|----------------------|---------|-------------------------------|
| timestamp            | datetime| 时间                          |
| zone_15m             | string  | 15m所属区间                   |
| zone_30m             | string  | 30m所属区间                   |
| resonance_type       | string  | 共振类型                      |
| forward_return_5     | float   | 之后5根15mK线收益率           |
| forward_return_10    | float   | 之后10根15mK线收益率          |
| forward_return_20    | float   | 之后20根15mK线收益率          |

---

### 4.5 基于本框架的策略原型设计层

**目标**：以本框架统计结果为基础，构建可回测的初级策略原型。

#### 策略候选方向

1. **超卖反转策略**
   - 进场：RSI14 由 ≤30 区间向上突破至中性偏空区
   - 出场：RSI14 触及 50 或 70
2. **超买回落策略**
   - 进场：RSI14 由 >70 区间向下跌破至中性偏多区
   - 出场：RSI14 触及 50 或 30
3. **背离反转策略**
   - 进场：出现底背离/顶背离
   - 出场：之后10根K线 或 RSI触及中轴
4. **MTF共振策略**
   - 进场：15m 与 30m 同向强共振
   - 出场：共振消失

#### 策略评估输出表：`strategy_backtest`

| 字段                 | 类型    | 说明                |
|----------------------|---------|---------------------|
| strategy_name        | string  | 策略名称            |
| trade_count          | int     | 交易次数            |
| win_rate             | float   | 胜率                |
| avg_return           | float   | 平均收益            |
| max_drawdown         | float   | 最大回撤            |
| profit_factor        | float   | 盈亏比              |
| sharpe_ratio         | float   | 夏普比率            |
| expectancy           | float   | 期望收益            |

---

## 5. 输出报告内容（建议结构）

1. 总体概览
2. 各区间K线分布
3. 区间事件持续分析
4. 区间收益分布
5. 区间转换矩阵（热力图）
6. 成交量结构分析
7. 背离事件统计
8. 多时间框架共振分析
9. 策略原型回测结果

---

## 6. 研究问题（Research Questions）

- 各 RSI 区间的时间结构、收益结构、成交量结构是否存在显著差异？
- RSI 状态转换是否符合马尔可夫性质？
- 多时间框架共振是否具备显著的方向性预测能力？
- 背离信号是否具备可量化的有效性？
- 哪些基于 RSI 的策略原型具备稳定 alpha 潜力？

---

## 7. 版本信息

- **文档版本**：v3.0  
- **状态**：完整研究框架版  
- **用途**：量化策略研究、回测、论文写作、数据建模
