---
type: query
title: Library Overview
tags: [dataview, query, library]
---

# Library Overview

## All Library Content
```dataview
TABLE audience, type, file.mday as "Modified"
FROM "library"
SORT file.name ASC
```

## Public Content
```dataview
TABLE type, file.etags as "Tags"
FROM "library"
WHERE audience = "public"
SORT file.name ASC
```

## Recently Added
```dataview
TABLE audience, type
FROM "library"
SORT file.ctime DESC
LIMIT 10
```

## Content by Type
```dataview
TABLE rows.file.link as "Files"
FROM "library"
GROUP BY type
SORT type ASC
```
