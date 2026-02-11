[English](README.md) | [繁體中文](README.zh.md)

# skill-optimizer

一個 Claude Code 的 meta-skill，分析技能執行結果並套用針對性改進。在保持核心原則和邏輯的同時，隨技術演進調整工具和技術手段，讓技能持續保持有效和現代化。

## 功能特色

1. 偵測最近執行的技能（或接受指定的技能名稱）
2. 分析對話上下文中的錯誤、繞道方案、使用者修正、過時模式
3. 依類別和風險等級分類每個發現
4. 提出結構化的變更建議，含前後對比
5. 套用核准的變更、升版、commit 並 push

## 設計哲學

> **原則穩定，工具可替換。**

| 層級 | 穩定性 | 更新策略 |
|------|--------|----------|
| 原則與目標 | 穩定 | 很少變動 |
| 邏輯與流程 | 半穩定 | 發現更好的模式時調整 |
| 工具與技術 | 易變 | 自由替換 |

## 前置條件

- 技能安裝於 `~/.claude/skills/`
- Git 已設定技能的遠端倉庫

## 安裝

```bash
git clone https://github.com/joneshong-skills/skill-optimizer.git ~/.claude/skills/skill-optimizer
```

## 使用方式

當技能執行後遇到問題或有改進空間時：

- *「optimize image-gen based on what just happened」*
- *「剛剛那個流程可以改進」*
- *「review smart-search skill performance」*
- *「skill 需要更新」*

## 變更類別

| 類別 | 風險 | 審核方式 |
|------|------|----------|
| Bug 修復 | 低 | 直接套用 |
| 增強改進 | 低 | 直接套用 |
| 技術更新 | 中 | 先摘要再套用 |
| 新邊界情況 | 中 | 先摘要再套用 |
| 流程重構 | 高 | 先與使用者討論 |
| 原則變更 | 重大 | 完整討論 |

## 專案結構

```
skill-optimizer/
├── SKILL.md                        # 技能定義及工作流程
├── README.md                       # 英文說明
├── README.zh.md                    # 繁體中文說明（本檔案）
└── references/
    └── analysis-framework.md       # 詳細分析檢查清單及模式
```

## 授權

MIT
