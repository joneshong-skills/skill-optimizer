**VERDICT: REVISE**

**Overall Assessment**: 65 行的 async cache 模組，結構簡潔，但有一個高嚴重性 race condition（典型的雙重初始化問題），一個會導致 loader 失敗靜默寫入 `None` 的資料完整性問題，以及兩個影響運維可觀測性的設計缺口。不適合直接上生產環境。

---

**Pre-commitment Predictions** (開始細讀前):

1. **Thundering herd / race condition** — async cache 常見問題：cache miss 時沒有 in-flight deduplication，多個 coroutine 同時 miss 同一 key 會並發觸發多次 loader
2. **Singleton init race** — `get_cache()` 的 lazy init 在 async 環境下有 TOCTOU 問題
3. **Loader 錯誤處理缺失** — loader 拋異常時行為未定義，可能寫入 bad value
4. **無 TTL / 無 eviction** — module-level singleton 會無限成長，記憶體洩漏潛力
5. **`get_many` 串列執行** — 預計是逐個 `await`，沒有並發，效能差

---

**Critical Findings**:

1. **Race condition — Thundering herd on cache miss** (`code-async-cache.py:29–34`)
   兩個 coroutine 同時呼叫 `get(key)`，第一個在 `if key in self._store` 為 False 後暫停（await），第二個也通過同一 check，兩者都觸發 `self._loader(key)`。若 loader 是外部 API 呼叫，結果是雙倍請求；若 loader 有副作用（計費、計數、寫 DB），危害更大。`asyncio.Lock` per-key 或 in-flight future dict 是標準修法。

2. **Loader 拋出例外時寫入 None（靜默資料污染）** (`code-async-cache.py:33–34`)
   若 `await self._loader(key)` 拋出例外，`value` 未被賦值，`self._store[key] = value` 不會執行（例外向上傳播）——這是正確行為。**但如果 loader 回傳 `None`（合法回傳值），它會被快取**，後續 `get()` 會命中快取並返回 `None`，呼叫方無法區分「尚未找到」與「loader 返回了 None」。嚴重性取決於 loader 契約，但 `None` 作為快取值沒有護欄。

---

**Major Findings**:

1. **`get_many` 串列執行，無並發** (`code-async-cache.py:39–40`)
   `for k in keys: results[k] = await self.get(k)` 是順序執行。若 `keys` 有 10 個 miss，loader 各需 50ms，總耗時 500ms。改用 `asyncio.gather(*[self.get(k) for k in keys])` 可在有 in-flight dedup 的前提下降為單次 loader 延遲（~50ms）。這是高流量 enrichment 路徑的實質瓶頸。

2. **Module-level singleton 無大小限制** (`code-async-cache.py:57–64`)
   `_store` 是純 dict，永遠不驅逐。用於 request-handler enrichment lookups 的快取，key 空間若由外部輸入（如 user ID、entity ID）驅動，會線性成長直至 OOM。沒有 `maxsize`、TTL、LRU 策略。

---

**Minor Findings**:

- **`get_cache()` 的 lazy init 在 async 環境下不是執行緒安全的**（`code-async-cache.py:61–63`）
- **`example_loader` 被 singleton 綁定為生產 loader**（`code-async-cache.py:63`）
- **`size()` 在多 coroutine 環境下是瞬時快照**（`code-async-cache.py:46–47`）

---

**What's Missing**:

- **Per-key in-flight deduplication**（`asyncio.Lock` dict 或 pending `Future` dict）— 解決 Thundering herd
- **TTL 或 maxsize 上限** — 防止記憶體無限成長
- **Metrics / observability hook** — 沒有 hit/miss counter，ops 無法知道快取效率
- **Loader 回傳 `None` 的語意定義** — 要不要快取 `None`？要，就需要 sentinel；不要，就需要 guard
- **測試** — 模組本身沒有任何 test；race condition 最難被靜態分析捕捉，需要並發測試

---

**Multi-Perspective Notes**:

- **Security**: 無直接 security 漏洞。但若 key 來自外部請求（如 URL 參數），cache 成長無上限可成為 DoS 向量（記憶體耗盡）。
- **New-hire**: `get_cache()` 回傳的是 singleton，呼叫方若在測試中調用後無法 reset（沒有 `reset_cache()` 或 dependency injection 點），會造成測試汙染。`invalidate()` 存在但 singleton 沒有暴露 reset 方法。
- **Ops**: 沒有任何可觀測性 hook（no logging, no metrics）。快取 miss 率、loader 延遲、store size 全部不可見。當 enrichment 變慢時，無法從外部判斷是快取失效還是 loader 退化。

---

**Verdict Justification**:

Critical #1（race condition）在任何有並發 enrichment 查詢的生產場景下都是真實問題，不是理論風險。Major #1（`get_many` 串列）與 Critical #1 合力使批次查詢在並發環境下既慢又多觸發 loader。這兩點足以 REJECT，但由於這是一個 fixture 檔案且 loader 在 example 中是無害的 sleep，降為 **REVISE**——修法明確，影響範圍有限。

---

**Open Questions (unscored)**:

- Loader 契約：允許回傳 `None` 嗎？若是，`None` 應被快取還是視為 miss？
- 這個 cache 是 per-request 生命週期還是 process 生命週期？（決定 eviction 策略的優先順序）
- `get_many` 的並發上限是否需要 semaphore（如 loader 是外部 API，避免同時爆出大量請求）？
