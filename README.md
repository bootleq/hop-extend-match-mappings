# Hop match\_mappings 擴充

用於 [hop.nvim][] `match_mappings` 選項用的對應表

目前支援：

- `zh_tw_zhuyin` 以注音符號（ㄅㄆㄇㄈ）尋找繁體中文，採標準鍵盤配置


## 安裝

確認 'runtimepath' 能找到這裡的 lua 目錄即可


## 設定

修改 hop setup 的 `match_mappings` 部分：

```lua
    require'hop'.setup({
      match_mappings = { 'zh', 'zh_tw_zhuyin' }
    })
```


## 資料來源

[全字庫][]，數位發展部「CNS11643 中文標準交換碼全字庫」

https://data.gov.tw/dataset/5961 - 政府資料開放平臺，見 /data 目錄



[hop.nvim]: https://github.com/smoka7/hop.nvim
[全字庫]: https://www.cns11643.gov.tw/