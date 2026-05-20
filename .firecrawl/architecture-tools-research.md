# Open-Source Tools for Software Architecture Auditing, Dependency Analysis & System Health Checking

> Research compiled: May 2026

---

## 1. Architecture Analysis & Dependency Checking

### ArchUnit (Java)
- **URL:** https://github.com/TNG/ArchUnit
- **Stars:** 3,700+
- **License:** Apache-2.0
- **Description:** A Java architecture test library that lets you specify and assert architecture rules in plain Java unit tests. Checks package dependencies, layer/slice rules, cyclic dependencies, class naming conventions, etc.
- **Self-hosted:** Yes (library dependency in your project; no server needed)
- **Python integration:** No (Java only; but similar Python tools exist like `import-linter`)
- **Unique:** Fluent API that integrates directly into JUnit/TestNG — architecture tests as part of CI. No external analysis server needed.

### jQAssistant
- **URL:** https://github.com/jQAssistant/jqassistant
- **Stars:** 276
- **License:** GPL-3.0
- **Description:** Scans software structures and stores them in a Neo4j graph database. You can query architecture rules using Cypher (graph queries) and enforce them in CI pipelines.
- **Self-hosted:** Yes (CLI + Neo4j backend)
- **Python integration:** Via plugins; primarily Java-focused but multi-language support via plugins
- **Unique:** Graph-based architecture analysis — query dependencies like a knowledge graph. Extremely powerful for complex structural queries.

### clang-tidy (C/C++)
- **URL:** https://github.com/llvm/llvm-project (part of LLVM)
- **Stars:** 38,400+ (entire LLVM project)
- **License:** Apache-2.0 with LLVM Exceptions
- **Description:** A clang-based C++ linter and static analyzer. Provides checks for naming conventions, code smells, modern C++ migration, and includes a modular check framework.
- **Self-hosted:** Yes (CLI tool)
- **Python integration:** No (but can be invoked from Python via subprocess)
- **Unique:** Deep C/C++ AST analysis built on the Clang compiler infrastructure. Includes fix-it suggestions for auto-correction.

### cppcheck (C/C++)
- **URL:** https://github.com/cppcheck-opensource/cppcheck
- **Stars:** 6,600+
- **License:** GPL-3.0
- **Description:** Static analysis tool for C/C++ code. Detects buffer overflows, null pointer dereferences, memory leaks, STL usage errors, and unused functions.
- **Self-hosted:** Yes (CLI, GUI, and IDE integrations)
- **Python integration:** Via subprocess; Python addon scripts available (e.g., misra.py)
- **Unique:** Very low false-positive rate compared to many other C/C++ analyzers. Has a "donate CPU" program where users donate compute to analyze open-source packages.

### OWASP Dependency-Check
- **URL:** https://github.com/dependency-check/DependencyCheck
- **Stars:** 7,600+
- **License:** Apache-2.0
- **Description:** Software Composition Analysis (SCA) tool that identifies publicly disclosed vulnerabilities (CVEs) in project dependencies. Supports Java, .NET, Python, Ruby, Node.js, Go, and more.
- **Self-hosted:** Yes (CLI, Maven plugin, Gradle plugin, Jenkins plugin, Docker)
- **Python integration:** Yes (pip install, Maven/Gradle via plugins, Docker)
- **Unique:** Focused entirely on supply-chain security. Uses NVD, OSS Index, and Retire.js feeds. Integrates into build pipelines for automated CVE detection.

### NetArchTest (.NET)
- **URL:** https://github.com/BenMorris/NetArchTest
- **Stars:** 1,700+
- **License:** MIT
- **Description:** A fluent API for .NET that enforces architectural rules in unit tests. Inspired by ArchUnit for Java. Supports layered architecture checks, namespace/class dependency rules, and custom rules.
- **Self-hosted:** Yes (NuGet package, runs alongside unit tests)
- **Python integration:** No (.NET only)
- **Unique:** .NET-native port of the ArchUnit concept. Uses Mono.Cecil for assembly inspection. Supports policy grouping of rules.

### import-linter (Python)
- **URL:** https://github.com/seddonym/import-linter
- **Stars:** 1,000+
- **License:** BSD-2-Clause
- **Description:** Lets you enforce constraints on imports between Python modules. Supports layer rules, forbidden imports, and dependency direction rules. Includes a web UI for architecture exploration.
- **Self-hosted:** Yes (pip install; CLI + pre-commit hook)
- **Python integration:** Yes (native Python package)
- **Unique:** Purpose-built for Python architecture enforcement. Can be used as a pre-commit hook. Has a browser UI to visualize Python package architecture.

### Depends (Multi-language)
- **URL:** https://github.com/multilang-depends/depends
- **Stars:** 251
- **License:** MIT
- **Description:** A multi-language source code dependency extraction tool. Supports Java, C/C++, Ruby, Python, and Maven/POM files. Outputs to JSON, XML, Excel, DOT (Graphviz), PlantUML, and DV8 formats.
- **Self-hosted:** Yes (Java CLI; no server required)
- **Python integration:** Yes (supports Python source as input)
- **Unique:** Designed as a research-grade framework for dependency extraction. Extensible to new languages via ANTLR. Aims to be a universal dependency extraction engine for architecture analysis tools.

### Structure101 Alternatives (Open-Source)
Structure101 is a commercial dependency analysis tool. Notable **open-source alternatives** include:
- **Depends** (above) — closest in capability for multi-language dependency extraction
- **jQAssistant** — graph-based dependency analysis
- **ArchUnit / NetArchTest** — test-based architecture enforcement
- **SonarQube** (Community Edition) — includes dependency cycle detection
- **DV8** (freemium) — architecture visualization built on top of Depends

---

## 2. Architecture Diagramming

### PlantUML
- **URL:** https://github.com/plantuml/plantuml
- **Stars:** 13,000+
- **License:** Dual-licensed (GPL, LGPL, Apache, EPL, MIT — choose per your use case)
- **Description:** Generate UML diagrams (sequence, class, activity, component, deployment, state, etc.) from plain-text descriptions. Supports C4 model diagrams, ArchiMate, network diagrams, Gantt charts, mind maps, and more.
- **Self-hosted:** Yes (JAR, Docker image, or official PlantUML server)
- **Python integration:** Via `plantuml` Python package or CLI subprocess
- **Unique:** De-facto standard for text-based UML. Extremely broad diagram type support. Can run client-side via TeaVM (JavaScript). Very active community with IDE plugins.

### Mermaid.js
- **URL:** https://github.com/mermaid-js/mermaid
- **Stars:** 88,200+
- **License:** MIT
- **Description:** JavaScript-based diagramming tool that generates flowcharts, sequence diagrams, class diagrams, state diagrams, Gantt charts, pie charts, git graphs, C4 diagrams, and more from Markdown-like text.
- **Self-hosted:** Yes (npm package, Docker, or HTTP server)
- **Python integration:** Via `mermaid` Python package or CLI tools (`mermaid-cli`)
- **Unique:** Natively rendered in browsers — zero server dependency. Native GitHub integration (render diagrams in Markdown files). Extremely popular (88k+ stars). Ideal for documentation-as-code workflows.

### Structurizr
- **URL:** https://github.com/structurizr (org)
- **Stars:** 199 (core library), 1,133 (Java library), 563 (CLI)
- **License:** Apache-2.0
- **Description:** "C4 models as code" — creates multiple software architecture diagrams from a single model. Supports the C4 model (Context, Container, Component, Code). Includes Structurizr Lite (embedded server).
- **Self-hosted:** Yes (Structurizr Lite — single JAR, no dependencies)
- **Python integration:** Community Python client libraries available
- **Unique:** Model-first (not diagram-first). A single model generates multiple views. Designed specifically for the C4 model. Supports DSL-based workspace definition.

### Diagrams (Python library)
- **URL:** https://github.com/mingrammer/diagrams
- **Stars:** 42,300+
- **License:** MIT
- **Description:** "Diagram as Code" — draw cloud system architecture diagrams in Python code. Supports AWS, Azure, GCP, Kubernetes, Alibaba Cloud, Oracle Cloud, On-Premises, SaaS, C4, and Programming framework nodes.
- **Self-hosted:** Yes (pip install; uses Graphviz for rendering)
- **Python integration:** Yes (native Python library)
- **Unique:** Best-in-class for **cloud architecture** diagrams. Massive provider icon set built-in. Ideal for prototyping and version-controlling cloud architecture designs.

### Graphviz
- **URL:** https://gitlab.com/graphviz/graphviz (active repo)
- **Stars:** N/A (hosted on GitLab); was previously on GitHub (archived)
- **License:** EPL (Eclipse Public License)
- **Description:** Graph visualization software. Uses DOT language to describe graphs. Renders to SVG, PNG, PDF, and many other formats. The underlying layout engine for most diagram-as-code tools.
- **Self-hosted:** Yes (system package; CLI tool)
- **Python integration:** Via `graphviz` Python package
- **Unique:** The foundational graph layout engine that powers PlantUML, Diagrams, D2, and many other tools. Handles directed/undirected graphs, hierarchies, and custom layouts with sophisticated algorithms.

### Kroki
- **URL:** https://github.com/yuzutech/kroki
- **Stars:** 4,100+
- **License:** MIT
- **Description:** Unified API for generating diagrams from text. Supports PlantUML, Mermaid, BlockDiag, BPMN, Bytefield, C4, D2, Diagrams.net, Ditaa, Erd, Excalidraw, GraphViz, Nomnoml, Pikchr, Svgbob, UMLet, Vega, Vega-Lite, WaveDrom, and WireViz.
- **Self-hosted:** Yes (Docker images; modular microservice architecture)
- **Python integration:** Via HTTP API (GET/POST with text encoding)
- **Unique:** **Unified diagramming API** — one endpoint to render 20+ diagram types. Modular companion containers for each library. Self-hostable via Docker Compose. Eliminates the need to install and maintain multiple diagramming tools individually.

---

## 3. Architecture Health / Quality Metrics

### SonarQube
- **URL:** https://github.com/SonarSource/sonarqube
- **Stars:** 10,600+
- **License:** LGPL-3.0 (Community Edition)
- **Description:** Continuous code quality inspection platform. Provides static analysis, code coverage, duplication detection, security hotspots, architecture analysis (dependency cycles, package tangle index), and quality gates for CI/CD.
- **Self-hosted:** Yes (Community Edition; Docker, or standalone server)
- **Python integration:** Yes (SonarPython plugin; also via `sonar-scanner` CLI)
- **Unique:** Gold-standard enterprise code quality platform. Quality Gates enforce "clean code" policies. 30+ language support. Rich dashboards, trend analysis, and developer workflow integration.

### CodeClimate Alternatives (Open-Source)
CodeClimate is a commercial code quality platform. Notable **open-source alternatives** include:
- **SonarQube Community Edition** — most comprehensive free alternative
- **Codacy** (open-source self-hosted option available)
- **PMD / Checkstyle / ESLint** — language-specific analyzers that can be aggregated
- **Radon + xenon** — Python-specific metrics suite
- **Reviewdog** — wrapper that runs linters and posts results

### Radon (Python)
- **URL:** https://github.com/rubik/radon
- **Stars:** 2,000+
- **License:** MIT
- **Description:** Python tool that computes McCabe's cyclomatic complexity, raw metrics (SLOC, comment lines, blank lines), Halstead metrics, and Maintainability Index. Supports CLI and programmatic usage.
- **Self-hosted:** Yes (pip install; CLI tool)
- **Python integration:** Yes (native Python library)
- **Unique:** Purpose-built for Python source code metrics. Used by Codacy, Code Climate, and CodeFactor. Integrated with Jupyter notebooks (`.ipynb`). Companion tool `xenon` monitors thresholds in CI.

### PMD
- **URL:** https://github.com/pmd/pmd
- **Stars:** 5,400+
- **License:** BSD-style (custom license)
- **Description:** Extensible multi-language static code analyzer. 400+ built-in rules across Java, JavaScript, Apex, PL/SQL, Kotlin, Swift, Python, Ruby, Go, and more. Includes CPD (Copy-Paste Detector).
- **Self-hosted:** Yes (CLI, Maven/Gradle plugin, IDE plugins)
- **Python integration:** Limited (PMD supports Python via CPD only; main Python support is through PMD's Java ecosystem wrapper)
- **Unique:** Extremely mature (20+ years). Highly customizable via XPath rules against the AST. Built-in duplicate code detection (CPD) is industry-leading.

### Checkstyle
- **URL:** https://github.com/checkstyle/checkstyle
- **Stars:** 8,900+
- **License:** LGPL-2.1
- **Description:** Static code analysis tool for Java that enforces coding standards (Google Java Style, Sun Code Conventions, or custom). Checks naming conventions, Javadoc, imports, code layout, and more.
- **Self-hosted:** Yes (CLI, ANT task, Maven/Gradle plugin)
- **Python integration:** No (Java only)
- **Unique:** The reference implementation for Java code style enforcement. 190+ built-in checks. Extremely configurable via XML. Industry standard for Java coding conventions.

### Xradar
- **URL:** https://github.com/atlanmod/xradar (tentative — tool may be less active)
- **License:** (varies)
- **Description:** A software quality radar chart generator. Visualizes quality metrics from tools like SonarQube, PMD, Checkstyle, etc., into a unified radar/spider chart.
- **Self-hosted:** Yes
- **Python integration:** Possible via data export/import
- **Unique:** Aggregates metrics from multiple tools into a single visual radar chart for quick architectural health assessment.

---

## Summary Matrix

| Tool | Category | Lang Focus | Stars | License | Python Integration | Self-Hosted |
|------|----------|-----------|-------|---------|-------------------|-------------|
| **ArchUnit** | Dependency checking | Java | 3.7k | Apache-2.0 | ❌ | ✅ (library) |
| **jQAssistant** | Dependency/Graph analysis | Java, multi-lang | 276 | GPL-3.0 | ⚠️ (plugins) | ✅ |
| **clang-tidy** | C/C++ static analysis | C/C++ | 38.4k* | Apache-2.0 | ❌ | ✅ |
| **cppcheck** | C/C++ static analysis | C/C++ | 6.6k | GPL-3.0 | ⚠️ (subprocess) | ✅ |
| **OWASP Dep-Check** | SCA/security | Multi-lang | 7.6k | Apache-2.0 | ✅ | ✅ |
| **NetArchTest** | Dependency checking | .NET | 1.7k | MIT | ❌ | ✅ (library) |
| **import-linter** | Import/enforcement | Python | 1.0k | BSD-2 | ✅ (native) | ✅ |
| **Depends** | Dependency extraction | Multi-lang | 251 | MIT | ✅ (input lang) | ✅ |
| **PlantUML** | Diagramming | Text→UML | 13k | Multi | ✅ (pkg + CLI) | ✅ |
| **Mermaid.js** | Diagramming | Text→Dia | 88.2k | MIT | ✅ (pkg + CLI) | ✅ |
| **Structurizr** | C4 modeling | Java, DSL | 1.1k | Apache-2.0 | ⚠️ (community) | ✅ (Lite) |
| **Diagrams** | Diagramming | Python→Dia | 42.3k | MIT | ✅ (native) | ✅ |
| **Graphviz** | Graph layout | DOT→Graph | ** | EPL | ✅ (pkg) | ✅ |
| **Kroki** | Unified API | Aggregator | 4.1k | MIT | ✅ (HTTP API) | ✅ (Docker) |
| **SonarQube** | Quality platform | 30+ langs | 10.6k | LGPL-3.0 | ✅ (plugin) | ✅ (CE) |
| **Radon** | Python metrics | Python | 2.0k | MIT | ✅ (native) | ✅ |
| **PMD** | Static analysis | Java+16 langs | 5.4k | BSD | ⚠️ (limited) | ✅ |
| **Checkstyle** | Style enforcement | Java | 8.9k | LGPL-2.1 | ❌ | ✅ |

\* = LLVM project-wide star count (clang-tidy is a component)
** = Graphviz hosted on GitLab (not GitHub)

---

## Recommendations by Use Case

| Use Case | Recommended Tools |
|----------|-----------------|
| **Java architecture testing** | ArchUnit + jQAssistant + PMD |
| **Python architecture enforcement** | import-linter + Radon |
| **.NET architecture enforcement** | NetArchTest |
| **C/C++ static analysis** | clang-tidy + cppcheck |
| **Multi-language dependency extraction** | Depends + jQAssistant |
| **Supply chain security** | OWASP Dependency-Check |
| **Full-platform quality monitoring** | SonarQube Community Edition |
| **Cloud architecture diagrams** | Diagrams (Python) + PlantUML |
| **C4 architecture modeling** | Structurizr |
| **Documentation-as-code diagrams** | Mermaid.js (GitHub-native) |
| **Unified diagram server** | Kroki (Docker) |
| **Code metrics & complexity** | Radon + PMD + Checkstyle |
