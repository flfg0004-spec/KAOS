"""Chain-of-Thought + Self-Consistency para generación mejorada."""
import json, sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

def generate_with_cot(prompt: str, agent: str = "") -> tuple[str, str]:
    """Generate response with chain-of-thought reasoning.
    
    Args:
        prompt: Input prompt
        agent: Agent name for context
    
    Returns:
        (reasoning, answer) tuple
    """
    try:
        from lib.dsol import generate_structured
        cot_prompt = f"""{prompt}

IMPORTANT: First reason step by step about the problem, then provide your final answer.
Format your response as JSON with two fields:
- "reasoning": your step-by-step reasoning process
- "answer": your final answer"""
        result = generate_structured(cot_prompt)
        if isinstance(result, dict) and "error" not in result:
            reasoning = result.get("reasoning", "")
            answer = result.get("answer", json.dumps(result))
            return reasoning, answer
    except Exception:
        pass
    
    # Fallback: return raw response
    return "", prompt


def self_consistency(prompt: str, n: int = 3, agent: str = "") -> str:
    """Generate n responses and return the most consistent one.
    
    Args:
        prompt: Input prompt
        n: Number of samples to generate
        agent: Agent name for context
    
    Returns:
        Most consistent answer string
    """
    import random
    from lib.dsol import generate_structured
    
    responses = []
    for i in range(n):
        try:
            temp = 0.5 + random.random() * 0.5  # random temp 0.5-1.0
            result = generate_structured(prompt)
            if isinstance(result, dict) and "error" not in result:
                responses.append(json.dumps(result))
        except Exception:
            continue
    
    if not responses:
        return prompt
    
    if len(responses) == 1:
        return responses[0]
    
    # Simple majority: return the most common response (exact match)
    from collections import Counter
    counter = Counter(responses)
    return counter.most_common(1)[0][0]


if __name__ == "__main__":
    # Test CoT
    reasoning, answer = generate_with_cot("Explain how to fix a Python NoneType error")
    print(f"CoT reasoning: {reasoning[:100]}...")
    print(f"CoT answer: {answer[:100]}...")
    
    # Test self-consistency
    consistent = self_consistency("Write a function to sort a list", n=2)
    print(f"\nSelf-consistency result: {consistent[:100]}...")
