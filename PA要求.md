# Software Architecture - Project Assignment
- 邓紫坤: zkdeng@scut.edu.cn
- 刘俊贤: jxliumk@163.com


## Example I: Exploratory Data Analysis
核心环节：Feature Selection（特征选择）、Dimension Reduction（降维）、Clustering（聚类）

关键问题：
- Where is the data stored?（数据存储位置？）
- Which parts are calculated on the server?（哪些部分在服务器上计算？）
- How to render the scatter plot?（如何渲染散点图？）


## Example II: OCR
### 核心流程
1. Pre-processing（预处理）
2. Text Detection（文本检测）
3. Text Recognition（文本识别）
4. Image Reconstruction（图像重建）

### 关键问题
- Which parts are placed on the server for calculation?（哪些部分部署在服务器上计算？）
- Is there any difference between the server in the LAN and the server in the external network?（局域网服务器与外网服务器是否存在差异？）
- Will it be faster to use parallel computing?（使用并行计算是否会提升速度？）


## Computation Partitioning - A Simple Example
### 整体流程与数据
| 核心环节 | 输入（Input） | 输出（Output） |
|----------|---------------|----------------|
| 基础流程 | Image（图像） | Result（结果） |
| 细分步骤 | Grayscale（灰度处理）、Localization（定位）、Keypoint Generation（关键点生成）、Descriptor（描述符）、Classification（分类） | - |
| 关键子步骤 | Local Extrama Detection（局部极值检测）、Assignment（分配）、Orientation Caculation（方向计算）、Similarity（相似度） | - |

### 数值数据（无单位）
原始数值序列：1.89、0.1、1.42、0.2、0.84、0.2、0.71、0.3、0.47、0.2、0.24、0.15、0.42、0.1、0.31；0.28、0.55、0.55、0.86、0.55、0.44、0.28

### 计算过程
1. 特定项求和：\[0.28 + 0.55 + 0.84 + \underline{0.2 + 0.3 + 0.2 + 0.15 + 0.1} + 0.31 = 2.93\]
2. 本地执行（Local Execution）：\(0.28 + 0.55 + 0.55 + 0.86 + 0.55 + 0.44 + 0.28 = 3.51\)
3. 远程执行（Remote Execution）：\[1.89 + 0.1 + 0.2 + 0.2 + 0.3 + 0.2 + 0.15 + 0.1 + 0.31 = 3.45\]


## Project Assignment Details
### Part A（50分）
1. 任务要求：选择1个Web/移动应用程序，在浏览器/移动设备上实现并测试其性能。
2. 应用要求：需满足**计算密集型**和**延迟敏感型**，示例包括但不限于：
   - 探索性数据分析（exploratory data analysis）
   - 手势识别（hand gesture recognition）
   - 人脸识别（face recognition）
   - 基于图像的目标识别（image based object recognition）
   - 增强现实（augmented reality）
   - 光学字符识别（OCR）


### Part B（50分）
1. 任务1：分析所选应用的模块结构。
2. 任务2：尝试在浏览器/移动设备与远程服务器（或云）之间划分模块。
3. 任务3：在不同条件/设置下测试应用性能，通过实验说明影响应用性能的因素及影响方式。


## Score Criteria（评分标准）
| 评分维度 | 分值占比 | 说明 |
|----------|----------|------|
| Part A | 50分 | 应用实现完整性、基础性能达标情况 |
| Part B | 50分 | 模块结构分析深度、分区合理性、实验完整性 |
| 最终交付物 | - | 1. 最终报告（Final Report）：占60%<br>2. 演示（Demonstration）：占40% |


## Final Report（最终报告）
### 格式要求
- 除封面外，需使用LaTeX编辑（编辑平台：cn.overleaf.com），具体参考QQ群通知。
- 需包含应用的**模块结构（module structure）** 。
- 尽可能在多场景下测量应用性能，例如：不同计算分区、输入数据、网络连接（WiFi/4G/5G）、带宽、移动设备/浏览器。
- 除实验结果外，需提炼并呈现核心洞察（insights）。

### 章节要求
| 章节 | 内容要求 | 字数/格式说明 |
|------|----------|----------------|
| 1 引言 | 1.1 背景<br>1.2 应用介绍 | 1.1：300-600字<br>1.2：1000-2000字，需配图 |
| 2 实验设置 | 实验环境、参数、设备等说明 | 1000-2000字，需配图或表格 |
| 3 实验结果 | 实验数据、性能表现等 | 1000-2000字，图表需丰富，图文并茂 |
| 4 讨论及结论 | 结果分析、核心发现、总结 | 1000字以内 |
| 5 其他章节 | 按需自行添加子章节 | - |


## Demonstrations（演示要求）
1. 时长限制：每组演示时间为6分钟。
2. 流程要求：设计清晰、逻辑连贯的演示流程，确保顺利进行。
3. 准备材料：需提供“演示清单（checklist）”，明确演示内容。
4. 预演要求：提前至少调试10次演示流程，确保无故障。


## Time Schedule（时间安排）
| 任务 | 截止时间 | 具体要求 |
|------|----------|----------|
| 提交小组信息 | 2025年10月9日23:59（仅限当天） | 1. 由组长发送至jxliumk@163.com<br>2. 内容：所有成员（5-7人）姓名+学号，组长邮箱+手机号 |
| 提交确认报告 | 2025年10月19日23:59 | 1. 发送至jxliumk@163.com<br>2. 内容：所选应用名称、应用源代码的模块结构<br>3. 无模板格式要求 |
| 演示（Demonstration） | 2025年11月30日 | 具体时间另行通知 |
| 提交最终报告+源代码 | 2025年11月30日23:59 | 1. 发送至jxliumk@163.com<br>2. 有模板格式要求，**不接受晚交** |