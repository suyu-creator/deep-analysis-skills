# Reflexion Memory: 坑模式(Pitfalls Patterns)

> 用途:记录每次深度分析中踩到/发现的坑模式,供下次分析复用。
> 由 deep-analysis skill 的 reporter(或主 Agent,kill 场景)在流程关键节点 append。
> 格式:每条以 `## <YYYY-MM-DD> <项目>` 开头,下面列坑模式。
> 首次使用:本文件为空骨架,skill 会自动填充。

<!-- 示例(由 skill 自动写入):
## 2026-08-16 电商小程序

### 发现的坑模式
- 支付回调幂等:用户支付中断网,回调可能重复到达 → 需幂等表(引用 GitHub: repo/file:line)
- 库存防超卖:并发下单需数据库行锁或 Redis 原子扣减
-->
