---
type: query
title: Wiki Gaps Report
tags: [dataview, query, gaps]
---

# Wiki Gaps

## Pages Without Outgoing Links
```dataview
TABLE length(file.outlinks) as "Outlinks", file.etags as "Tags"
FROM ".memory/wiki"
WHERE length(file.outlinks) = 0 AND file.name != "_index_"
SORT file.name ASC
```

## Pages Without Audience
```dataview
TABLE file.etags as "Tags"
FROM ".memory/wiki"
WHERE audience = null
SORT file.name ASC
```
