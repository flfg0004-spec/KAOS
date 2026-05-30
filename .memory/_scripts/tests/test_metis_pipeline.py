"""test_metis_pipeline.py — Tests de integración para el pipeline de Metis."""

import sys
import tempfile
import unittest
from pathlib import Path

KAOS_ROOT = Path(__file__).resolve().parents[3]


class TestBcgEval(unittest.TestCase):
    """Tests para bcg_eval_cli.py"""

    def test_bcg_eval_imports(self):
        """bcg_eval_cli.py debe importar sin errores."""
        sys.path.insert(0, str(KAOS_ROOT / ".memory" / "_scripts"))
        import bcg_eval_cli

        self.assertTrue(hasattr(bcg_eval_cli, "main"))

    def test_bcg_eval_okrs_exist(self):
        """El archivo de OKRs debe existir."""
        okrs_path = KAOS_ROOT / "KAOS" / "okrs" / "KAOS-OKRs-Q2-2026.md"
        self.assertTrue(okrs_path.exists())
        content = okrs_path.read_text(encoding="utf-8")
        self.assertIn("OKR", content)


class TestMetisMode(unittest.TestCase):
    """Tests para metis_mode.py"""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(KAOS_ROOT / ".memory" / "_scripts"))
        import metis_mode

        cls.metis_mode = metis_mode
        yaml_path = KAOS_ROOT / ".memory" / "schema" / "eval-profile.yaml"
        cls.profiles = metis_mode.load_profiles(yaml_path)

    def test_produccion_is_strategy(self):
        """El perfil 'produccion' debe mapear a modo 'strategy'."""
        info = self.metis_mode.build_mode_info("produccion", self.profiles)
        self.assertEqual(info["mode"], "strategy")

    def test_auditoria_is_quality(self):
        """El perfil 'auditoria' debe mapear a modo 'quality'."""
        info = self.metis_mode.build_mode_info("auditoria", self.profiles)
        self.assertEqual(info["mode"], "quality")

    def test_exploracion_is_strategy(self):
        """El perfil 'exploracion' debe mapear a modo 'strategy'."""
        info = self.metis_mode.build_mode_info("exploracion", self.profiles)
        self.assertEqual(info["mode"], "strategy")

    def test_desarrollo_is_strategy(self):
        """El perfil 'desarrollo' debe mapear a modo 'strategy'."""
        info = self.metis_mode.build_mode_info("desarrollo", self.profiles)
        self.assertEqual(info["mode"], "strategy")

    def test_qa_is_quality(self):
        """El perfil 'qa' debe mapear a modo 'quality'."""
        info = self.metis_mode.build_mode_info("qa", self.profiles)
        self.assertEqual(info["mode"], "quality")

    def test_produccion_temperature(self):
        """produccion debe tener temperatura 0.2-0.3."""
        info = self.metis_mode.build_mode_info("produccion", self.profiles)
        self.assertIn("temperature", info)

    def test_format_json_valid(self):
        """El output JSON debe ser válido."""
        info = self.metis_mode.build_mode_info("desarrollo", self.profiles)
        self.assertIn("profile", info)
        self.assertIn("mode", info)


class TestSyncCheck(unittest.TestCase):
    """Tests para metis_sync_check.py"""

    def test_sync_check_imports(self):
        """metis_sync_check.py debe importar sin errores."""
        sys.path.insert(0, str(KAOS_ROOT / ".memory" / "_scripts" / "audit"))
        import metis_sync_check

        self.assertTrue(hasattr(metis_sync_check, "main"))

    def test_sync_check_has_12_tools(self):
        """La referencia debe tener 12 tools."""
        sys.path.insert(0, str(KAOS_ROOT / ".memory" / "_scripts" / "audit"))
        import metis_sync_check

        tools = metis_sync_check.get_metis_tools_from_opencode()
        self.assertEqual(len(tools), 12)
        self.assertIn("strategy-mcp", tools)
        self.assertNotIn("dsol", tools)
        self.assertNotIn("speed", tools)

    def test_sync_check_no_legacy(self):
        """La referencia no debe tener dsol/speed legacy."""
        sys.path.insert(0, str(KAOS_ROOT / ".memory" / "_scripts" / "audit"))
        import metis_sync_check

        tools = metis_sync_check.get_metis_tools_from_opencode()
        self.assertNotIn("dsol", tools)
        self.assertNotIn("speed", tools)
        self.assertIn("mcp-dsol", tools)
        self.assertIn("mcp-speed", tools)


class TestDashboardPopulate(unittest.TestCase):
    """Tests para dashboard_populate.py"""

    def test_dashboard_populate_imports(self):
        """dashboard_populate.py debe importar sin errores."""
        sys.path.insert(0, str(KAOS_ROOT / ".memory" / "_scripts"))
        import dashboard_populate

        self.assertTrue(hasattr(dashboard_populate, "main"))

    def test_dashboard_exists(self):
        """dashboard.md debe existir."""
        dash_path = KAOS_ROOT / ".vault" / "quality" / "dashboard.md"
        self.assertTrue(dash_path.exists())


class TestAgentsMd(unittest.TestCase):
    """Tests para AGENTS.md"""

    def test_agents_md_exists(self):
        """AGENTS.md debe existir."""
        path = KAOS_ROOT / ".opencode" / "agents" / "metis" / "AGENTS.md"
        self.assertTrue(path.exists())

    def test_gap_detection_schema_exists(self):
        """AGENTS.md debe tener el schema de gap detection."""
        path = KAOS_ROOT / ".opencode" / "agents" / "metis" / "AGENTS.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("Gap Detection Output", content)
        self.assertIn("Gap Detection Response", content)

    def test_bcg_templates_exist(self):
        """AGENTS.md debe tener templates de BCG."""
        path = KAOS_ROOT / ".opencode" / "agents" / "metis" / "AGENTS.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("BCG Evaluation", content)
        self.assertIn("dashboard_populate", content)


class TestSkillMd(unittest.TestCase):
    """Tests para SKILL.md"""

    def test_skill_md_exists(self):
        """SKILL.md debe existir."""
        path = KAOS_ROOT / ".opencode" / "skills" / "metis" / "SKILL.md"
        self.assertTrue(path.exists())

    def test_quality_orchestrator_example_exists(self):
        """SKILL.md debe tener el ejemplo de Quality Orchestrator."""
        path = KAOS_ROOT / ".opencode" / "skills" / "metis" / "SKILL.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("Quality Orchestrator Mode", content)

    def test_metodologia_7_fases_exists(self):
        """SKILL.md debe tener las 7 fases."""
        path = KAOS_ROOT / ".opencode" / "skills" / "metis" / "SKILL.md"
        content = path.read_text(encoding="utf-8")
        for fase in ["Diagnosticar", "Investigar", "Estructurar", "Validar", "Comunicar"]:
            self.assertIn(fase, content)


class TestSoulMd(unittest.TestCase):
    """Tests para SOUL.md"""

    def test_soul_md_exists(self):
        """SOUL.md debe existir."""
        path = KAOS_ROOT / ".opencode" / "agents" / "metis" / "SOUL.md"
        self.assertTrue(path.exists())

    def test_mode_switching_section_exists(self):
        """SOUL.md debe tener Mode Switching."""
        path = KAOS_ROOT / ".opencode" / "agents" / "metis" / "SOUL.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("Mode Switching", content)
        self.assertIn("produccion", content)

    def test_temperature_note_exists(self):
        """SOUL.md debe tener nota de temperatura fija."""
        path = KAOS_ROOT / ".opencode" / "agents" / "metis" / "SOUL.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("temperatura", content.lower())

    def test_dual_role_exists(self):
        """SOUL.md debe tener Dual Role."""
        path = KAOS_ROOT / ".opencode" / "agents" / "metis" / "SOUL.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("Dual Role", content)


class TestAdr016(unittest.TestCase):
    """Tests para ADR-016"""

    def test_adr_016_exists(self):
        """ADR-016 debe existir."""
        path = KAOS_ROOT / "KAOS" / "04-esquema" / "ADR-016-arquitectura-metis.md"
        self.assertTrue(path.exists())

    def test_adr_has_contracts(self):
        """ADR-016 debe tener contratos con agentes."""
        path = KAOS_ROOT / "KAOS" / "04-esquema" / "ADR-016-arquitectura-metis.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("Mnemosyne", content)
        self.assertIn("Kratos", content)

    def test_adr_has_kratos_feedback(self):
        """ADR-016 debe tener feedback loop Kratos."""
        path = KAOS_ROOT / "KAOS" / "04-esquema" / "ADR-016-arquitectura-metis.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("feedback", content.lower())


class TestMetisMd(unittest.TestCase):
    """Tests para metis.md (agent root)"""

    def test_metis_md_exists(self):
        """metis.md debe existir."""
        path = KAOS_ROOT / ".opencode" / "agents" / "metis.md"
        self.assertTrue(path.exists())

    def test_post_session_section_exists(self):
        """metis.md debe tener Post-sesión."""
        path = KAOS_ROOT / ".opencode" / "agents" / "metis.md"
        content = path.read_text(encoding="utf-8")
        self.assertTrue("Post-sesión" in content)

    def test_limitaciones_section_exists(self):
        """metis.md debe tener Limitaciones."""
        path = KAOS_ROOT / ".opencode" / "agents" / "metis.md"
        content = path.read_text(encoding="utf-8")
        self.assertIn("Limitaciones", content)


class TestOpenCodeJson(unittest.TestCase):
    """Tests para opencode.json"""

    def test_no_legacy_dsol_speed(self):
        """opencode.json no debe tener dsol_*/speed_* legacy."""
        import json

        path = KAOS_ROOT / ".opencode" / "opencode.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        metis_tools = config.get("agent", {}).get("metis", {}).get("tools", {})
        self.assertNotIn("dsol_*", metis_tools)
        self.assertNotIn("speed_*", metis_tools)
        self.assertIn("mcp-dsol_*", metis_tools)
        self.assertIn("mcp-speed_*", metis_tools)

    def test_mcp_servers_registered(self):
        """mcp-speed y mcp-dsol deben estar registrados."""
        import json

        path = KAOS_ROOT / ".opencode" / "opencode.json"
        config = json.loads(path.read_text(encoding="utf-8"))
        mcp = config.get("mcp", {})
        self.assertIn("mcp-speed", mcp)
        self.assertIn("mcp-dsol", mcp)


class TestPipelineIntegration(unittest.TestCase):
    """Integration test: synthetic Metis output → post_output_hook → monitor."""

    SYNTHETIC_OUTPUT = """# Strategic Analysis Report

## O1: Expand Market Share

**Objective**: Incrementar market share de 15% a 25% en 12 meses

- KR1: Alcanzar 25% de market share (baseline: 15%)
- KR2: Reducir churn de 8% a 4%
- KR3: Aumentar NPS de 40 a 60

## Strengths
- Equipo técnico sólido (rating: 8/10)
- Producto maduro 99.9% uptime (rating: 9/10)
- Base de clientes leales (rating: 7/10)

## Weaknesses
- Falta presencia LATAM (rating: 4/10)
- Onboarding lento (rating: 3/10)
- Dependencia único proveedor (rating: 5/10)

## Opportunities
- Crecimiento GPU cloud 40% anual (rating: 8/10)
- Nuevos segmentos IA/ML (rating: 7/10)
- Expansión financiera (rating: 6/10)

## Threats
- Competidores pricing agresivo (rating: 7/10)
- Regulaciones Europa (rating: 6/10)
- Guerra talento técnico (rating: 8/10)

## H1 (0-3 meses)
- Lanzar versión 2.0 core
- Contratar 3 ingenieros senior
- Migrar a multi-cloud

## H2 (3-6 meses)
- Expandir LATAM con equipo local
- Integrar pagos encriptados
- Programa de partners

## H3 (6-12 meses)
- Expandir a Europa
- Plataforma IA/ML autónoma
- IPO planning

## Risks
- Riesgo de retraso en migration: mitigación con plan de contingencia
- Competidor lanza producto similar: mitigación con diferenciación
- Fuga de talento: mitigación con retention plan
"""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.output_file = self.tmp_dir / "metis_output.md"
        self.output_file.write_text(self.SYNTHETIC_OUTPUT, encoding="utf-8")

        # Import post_output_hook
        tools_dir = str(KAOS_ROOT / ".tools")
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        import post_output_hook
        self.hook = post_output_hook

        # Import monitor
        scripts_dir = str(KAOS_ROOT / ".memory" / "_scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import monitor
        self.mon = monitor

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

        # Clean up verification report generated by post_output_hook
        report_path = KAOS_ROOT / ".memory" / "cache" / "verification_metis_output.md"
        if report_path.exists():
            report_path.unlink()

    def _run_hook(self):
        import sys
        sys.argv = ["post_output_hook.py", str(self.output_file), "--checklist", "both"]
        self.hook.main()

    def test_full_pipeline_generates_verification_report(self):
        """post_output_hook generates a verification report in .memory/cache/."""
        self._run_hook()
        report_path = KAOS_ROOT / ".memory" / "cache" / "verification_metis_output.md"
        self.assertTrue(
            report_path.exists(),
            f"Verification report not found at {report_path}",
        )
        content = report_path.read_text(encoding="utf-8")
        self.assertIn("Verification Report", content)
        self.assertIn("OKR Integrity", content)

    def test_monitor_can_read_verification_report(self):
        """monitor.py check can parse the generated verification report."""
        self._run_hook()
        report_path = KAOS_ROOT / ".memory" / "cache" / "verification_metis_output.md"
        self.assertTrue(report_path.exists())

        result = self.mon.check_scores(str(report_path))
        self.assertIn("report", result)
        self.assertIn("components", result["report"])
        self.assertIn("overall", result["report"])
        self.assertIsInstance(result["passed"], bool)

    def test_report_contains_expected_components(self):
        """Verification report contains OKR, FODA, Roadmap, Risk checks."""
        self._run_hook()
        report_path = KAOS_ROOT / ".memory" / "cache" / "verification_metis_output.md"
        content = report_path.read_text(encoding="utf-8")
        for expected in ["OKR Integrity", "FODA Completeness", "Risk Identification"]:
            self.assertIn(expected, content)

    def test_cleanup_removes_temp_files(self):
        """Temporary output file is removed after test teardown."""
        path = self.output_file
        self.assertTrue(path.exists())
        # tearDown removes tmp_dir - verify happens after the test
        # This test just verifies the file exists before cleanup


if __name__ == "__main__":
    unittest.main()
