---
type: query
title: Quality Report
tags: [dataview, query, quality]
---

# Quality Report

## Notes by Backlink Count
```dataview
TABLE length(file.inlinks) as "Backlinks", file.etags as "Tags"
FROM ".memory/wiki"
SORT length(file.inlinks) DESC
```

## Notes With Complete Frontmatter
```dataview
TABLE audience, type, file.etags as "Tags"
FROM ".memory/wiki"
WHERE type != null AND audience != null
SORT file.name ASC
```

## Notes Missing Aliases
```dataview
TABLE file.etags as "Tags"
FROM ".memory/wiki"
WHERE aliases = null OR length(aliases) = 0
SORT file.name ASC
```

## Content Distribution
```dataview
TABLE length(file.outlinks) as "Outlinks", length(file.inlinks) as "Backlinks"
FROM ".memory/wiki"
SORT length(file.inlinks) DESC
```
