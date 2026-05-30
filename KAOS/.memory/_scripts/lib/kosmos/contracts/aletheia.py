"""aletheia.py — KosmosAletheiaContract: Factual Grounding.

Extraído de kosmos_contracts.py (D3).
"""
import logging
import re
from datetime import datetime
from typing import Any

from .models import (
    FactualVerification,
)

logger = logging.getLogger(__name__)


class KosmosAletheiaContract:
    """Contrato Kosmos → Aletheia para verificación factual de claims.

    Kosmos identifica claims en ADRs que necesitan verificación factual y
    los envía a Aletheia para grounding en fuentes externas.
    """

    def __init__(self, real_mode: bool = True) -> None:
        """Initialize the Kosmos-Aletheia contract.

        G4: Supports real Aletheia calls with graceful fallback to heuristic.

        Args:
            real_mode: If True, attempts real Aletheia call first,
                       falling back to heuristic simulation.
        """
        self.real_mode = real_mode
        self.real_calls = 0
        self.fallback_calls = 0
        self._status: dict[str, Any] = {
            "active": True,
            "last_run": "",
            "last_score": 0.0,
            "total_runs": 0,
            "errors": 0,
        }
        logger.debug("KosmosAletheiaContract initialized (real_mode=%s)", real_mode)

    # ── Public API ──

    def request_verification(self, claim: str, context: str = "") -> FactualVerification:
        """Request factual verification of a claim from Aletheia.

        Simula la verificación factual analizando el claim contra reglas
        heurísticas (sin LLM). En producción, esto enviaría el claim a
        Aletheia para búsqueda web.

        Args:
            claim: The claim to verify.
            context: Optional context to help disambiguate.

        Returns:
            FactualVerification with confidence, sources, and contradictions.
        """
        try:
            claim_lower = claim.lower()
            sources: list[str] = []
            contradictions: list[str] = []
            all_claims: list[str] = [claim]

            # Heuristic verification
            # Check for evidence patterns in the claim itself
            has_url = bool(re.search(r'https?://\S+', claim))
            has_number = bool(re.search(r'\d+', claim))
            has_reference = bool(re.search(r'(?:según|basado en|fuente|source|ref|paper|estudio)', claim_lower))

            if has_url:
                urls = re.findall(r'(https?://\S+)', claim)
                sources.extend(urls)
            if has_reference:
                refs = re.findall(r'(?:según|basado en|fuente|source)\s*:?\s*([^.,\n]+)', claim, re.IGNORECASE)
                sources.extend(r.strip() for r in refs if r.strip())

            # Check for uncertainty signals
            uncertainty_signals = [
                r'(?:creo|pienso|quizás|tal vez|maybe|perhaps|posiblemente|probablemente)',
                r'(?:no estoy seguro|not sure|uncertain|dudoso|doubtful)',
                r'(?:sin evidencia|no evidence|lacks evidence|no hay datos)',
            ]
            has_uncertainty = any(re.search(p, claim_lower) for p in uncertainty_signals)

            # Also check for potential contradictions in the claim itself
            contradiction_words = [
                (r'aumentar|incrementar', r'disminuir|reducir|decrecer'),
                (r'rápido|veloz', r'lento|slow'),
                (r'barato|económico', r'caro|costoso|costly'),
                (r'simple|fácil|easy', r'complejo|difícil|complex|hard'),
            ]
            for pos_pat, neg_pat in contradiction_words:
                if re.search(pos_pat, claim_lower) and re.search(neg_pat, claim_lower):
                    contradictions.append(f"Claim contiene términos contradictorios: {pos_pat} vs {neg_pat}")

            # Confidence scoring
            confidence = 0.5  # baseline
            if has_url:
                confidence += 0.2
            if has_number:
                confidence += 0.1
            if has_reference:
                confidence += 0.15
            if has_uncertainty:
                confidence -= 0.2
            if contradictions:
                confidence -= 0.15
            confidence = max(0.0, min(1.0, confidence))

            verified = confidence >= 0.6

            result = FactualVerification(
                query=claim,
                claims=all_claims,
                sources=sources[:5],
                confidence=round(confidence, 2),
                verified=verified,
                contradictions=contradictions,
                timestamp=datetime.now().isoformat(),
            )

            self._status["last_run"] = datetime.now().isoformat()
            self._status["last_score"] = confidence * 100
            self._status["total_runs"] += 1
            logger.info("Factual: confidence=%.2f, verified=%s, sources=%d", confidence, verified, len(sources))
            return result

        except Exception as exc:
            logger.error("request_verification failed: %s", exc)
            self._status["errors"] += 1
            return FactualVerification(
                query=claim,
                confidence=0.0,
                verified=False,
                contradictions=[f"Error: {exc}"],
                timestamp=datetime.now().isoformat(),
            )

    def parse_verification(self, response_text: str) -> FactualVerification:
        """Parse Aletheia's verification response.

        Args:
            response_text: Text response from Aletheia with verification results.

        Returns:
            FactualVerification with parsed data.
        """
        try:
            text = response_text or ""

            # Extract confidence
            conf_match = re.search(r'(?:confidence|confianza|score)\s*[:=]\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
            confidence = float(conf_match.group(1)) if conf_match else 0.5

            # Extract sources (URLs)
            sources = re.findall(r'https?://\S+', text)

            # Extract claims (sentences that look like factual statements)
            claims = re.findall(r'(?:claim|afirmaci[oó]n|statement|hecho)\s*:?\s*([^.\n]+)', text, re.IGNORECASE)
            if not claims:
                # Fallback: extract sentences with verification markers
                claims = re.findall(r'(?:✅|✓|verificado|confirmed|verified|cierto)\s*[:\s]*([^.\n]+)', text, re.IGNORECASE)

            # Extract contradictions
            contradictions = re.findall(r'(?:contradiction|contradicci[oó]n|conflict|conflicto)\s*:?\s*([^.\n]+)', text, re.IGNORECASE)
            contradictions = [c.strip() for c in contradictions if len(c.strip()) > 5]

            # Extract verification markers
            verified = bool(re.search(r'(?:verified|confirmed|verificado|confirmado|✅)', text, re.IGNORECASE))
            if not verified:
                has_positive = bool(re.search(r'(?:true|cierto|correcto|válido|valid|correct)', text, re.IGNORECASE))
                has_negative = bool(re.search(r'(?:false|falso|incorrecto|invalid|no\s+verified)', text, re.IGNORECASE))
                verified = has_positive and not has_negative

            # Extract query
            query_match = re.search(r'(?:query|claim|pregunta|question)\s*:?\s*([^.\n]+)', text, re.IGNORECASE)
            query = query_match.group(1).strip() if query_match else ""

            result = FactualVerification(
                query=query,
                claims=claims,
                sources=sources[:5],
                confidence=round(confidence, 2),
                verified=verified,
                contradictions=contradictions,
                timestamp=datetime.now().isoformat(),
            )

            self._status["last_run"] = datetime.now().isoformat()
            self._status["last_score"] = confidence * 100
            self._status["total_runs"] += 1
            logger.info("Verification parsed: confidence=%.2f, verified=%s", confidence, verified)
            return result

        except Exception as exc:
            logger.error("parse_verification failed: %s", exc)
            self._status["errors"] += 1
            return FactualVerification(
                confidence=0.0,
                verified=False,
                contradictions=[f"Parse error: {exc}"],
                timestamp=datetime.now().isoformat(),
            )

    def detect_uncertain_claims(self, adr_text: str) -> list[str]:
        """Scan ADR text and detect claims that need factual verification.

        Identifica claims basados en patrones como:
        - "según [fuente]"
        - "basado en [referencia]"
        - URLs
        - Referencias a tecnologías específicas
        - Afirmaciones cuantitativas (números, porcentajes)
        - Citas a estudios o papers

        Args:
            adr_text: The ADR text to scan.

        Returns:
            List of claim strings that need verification.
        """
        if not adr_text:
            return []

        claims: list[str] = []
        text_lines = adr_text.split("\n")

        # Pattern 1: Explicit references (según, basado en, fuente, etc.)
        ref_patterns = [
            r'(?:según|according to|basado en|based on|fuente|source)\s*:?\s*([^.\n]+)',
            r'(?:citando|citing|referencia|reference)\s*:?\s*([^.\n]+)',
            r'(?:estudio|study|paper|investigación|research)\s+(?:muestra|indica|sugiere|suggests|shows)\s+([^.\n]+)',
        ]
        for pat in ref_patterns:
            for match in re.finditer(pat, adr_text, re.IGNORECASE):
                claim = match.group(0).strip()
                if len(claim) > 15 and claim not in claims:
                    claims.append(claim)

        # Pattern 2: URLs as evidence
        url_matches = re.finditer(r'(https?://\S+)', adr_text)
        for match in url_matches:
            start = max(0, match.start() - 60)
            end = min(len(adr_text), match.end() + 60)
            context = adr_text[start:end].strip()
            if len(context) > 20 and context not in claims:
                claims.append(context)

        # Pattern 3: Quantitative claims (numbers, percentages, metrics)
        quant_patterns = [
            r'(?:precisión|accuracy|latencia|throughput|rendimiento)\s+(?:de|del|of)\s+\d+[%]?',
            r'\d+%\s+(?:de|del|de los|of)\s+(?:mejora|reducción|incremento|aumento|reduction|improvement)',
            r'(?:tiempo|time|velocidad|speed)\s+(?:de|del)\s+\d+\s*(?:ms|s|min|h)',
        ]
        for pat in quant_patterns:
            for match in re.finditer(pat, adr_text, re.IGNORECASE):
                claim = match.group(0).strip()
                if claim not in claims:
                    claims.append(claim)

        # Pattern 4: Technology-specific references (nombres de tecnologías con versiones)
        tech_patterns = [
            r'(?:Python|JavaScript|TypeScript|Rust|Go|Java)\s+\d+\.\d+',
            r'(?:Django|React|Vue|Angular|FastAPI|Flask|Spring|Laravel)\s+\d+',
            r'(?:PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch)\s+\d+',
            r'(?:AWS|Azure|GCP|Kubernetes|Docker)\s+\S+',
        ]
        for pat in tech_patterns:
            for match in re.finditer(pat, adr_text, re.IGNORECASE):
                claim = match.group(0).strip()
                if claim not in claims:
                    claims.append(claim)

        # Pattern 5: Decision-related claims with "porque", "ya que", "since"
        decision_claims = re.findall(
            r'(?:decidimos|optamos|elegimos|seleccionamos)\s+(.*?)(?:porque|ya que|since|because)\s+([^.\n]+)',
            adr_text, re.IGNORECASE
        )
        for action, reason in decision_claims:
            claim = f"Decidimos {action.strip()} porque {reason.strip()}"
            if len(claim) > 20 and claim not in claims:
                claims.append(claim)

        # Deduplicate and limit
        seen = set()
        unique_claims = []
        for c in claims:
            normalized = c.lower().strip()
            if normalized not in seen and len(c) > 15:
                seen.add(normalized)
                unique_claims.append(c)

        logger.info("Detected %d uncertain claims in ADR text", len(unique_claims))
        return unique_claims[:15]

    # ── G4: Real Aletheia verification ──

    def real_request_verification(self, claim: str, context: str = "") -> FactualVerification:
        """Real verification via Aletheia subagent (G4).

        First attempts to call Aletheia via agent_executor's LLM call mechanism.
        Falls back to heuristic simulation if Aletheia is unavailable.

        Args:
            claim: The claim to verify.
            context: Optional context to help disambiguate.

        Returns:
            FactualVerification with sources and confidence.
        """
        logger.info("G4: real_request_verification for claim: %.80s", claim)

        if not self.real_mode:
            logger.info("G4: real_mode=False, using heuristic fallback")
            self.fallback_calls += 1
            return self.request_verification(claim, context)

        # Build verification prompt for Aletheia
        prompt_parts = [
            "# Verification Request",
            "",
            "You are Aletheia, the factual grounding agent. Verify the following claim",
            "using web search and your knowledge base. Provide sources and confidence.",
            "",
            "## Claim to Verify",
            f"{claim}",
            "",
        ]
        if context:
            prompt_parts.append("## Context")
            prompt_parts.append(f"{context}")
            prompt_parts.append("")

        prompt_parts.extend([
            "## Output Format",
            "Respond with a structured verification:",
            "- **Verified**: Yes/No/Partial",
            "- **Confidence**: 0.0-1.0",
            "- **Sources**: List URLs and references",
            "- **Evidence**: Supporting or contradicting evidence",
            "- **Contradictions**: Any conflicting information found",
        ])
        prompt = "\n".join(prompt_parts)

        # Attempt real Aletheia call via agent_executor
        aletheia_response = None
        used_fallback = False
        try:
            from lib.agent_executor import _llm_or_executor_call
            aletheia_response = _llm_or_executor_call("aletheia", prompt)
            if aletheia_response and len(aletheia_response.strip()) > 20:
                self.real_calls += 1
                logger.info("G4: Aletheia real call succeeded (response=%d chars)", len(aletheia_response))
            else:
                logger.warning("G4: Aletheia returned empty/short response, using fallback")
                aletheia_response = None
                used_fallback = True
        except ImportError:
            logger.warning("G4: agent_executor._llm_or_executor_call not available, using fallback")
            used_fallback = True
        except Exception as exc:
            logger.warning("G4: Aletheia call failed (%s), using fallback", exc)
            used_fallback = True

        if aletheia_response is None:
            # Graceful degradation: use heuristic verification
            self.fallback_calls += 1
            fallback_result = self.request_verification(claim, context)
            fallback_result.query = claim
            if used_fallback:
                fallback_result.sources.append("(G4 fallback: Aletheia unavailable)")
            logger.info("G4: fallback used (real=%d, fallback=%d)", self.real_calls, self.fallback_calls)
            return fallback_result

        # Parse Aletheia response
        try:
            parsed = self.parse_verification(aletheia_response)
            parsed.query = claim
            logger.info("G4: parsed Aletheia response: confidence=%.2f, verified=%s",
                        parsed.confidence, parsed.verified)
            return parsed
        except Exception as exc:
            logger.warning("G4: failed to parse Aletheia response (%s), using fallback", exc)
            self.fallback_calls += 1
            fallback_result = self.request_verification(claim, context)
            fallback_result.query = claim
            return fallback_result

    def status(self) -> dict[str, Any]:
        """Return contract status (includes G4 real_mode metrics)."""
        status_dict = dict(self._status)
        status_dict["real_mode"] = self.real_mode
        status_dict["real_calls"] = self.real_calls
        status_dict["fallback_calls"] = self.fallback_calls
        return status_dict
