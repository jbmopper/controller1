"""
Prompt Contract Configuration

This module locks down the exact prompt formats used for HumanEval and MBPP.
These match the canonical formats from the lm-evaluation-harness.

IMPORTANT: Any changes here will affect benchmark comparability.
Document all deviations and their rationale.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class HumanEvalPromptConfig:
    """
    HumanEval prompt configuration.
    
    The canonical format from OpenAI's human-eval uses the function signature
    and docstring as the prompt. The model completes the function body.
    
    Dataset: openai/openai_humaneval
    
    Example prompt:
        from typing import List
        
        def has_close_elements(numbers: List[float], threshold: float) -> bool:
            \"\"\" Check if in given list of numbers, are any two numbers closer to each other than
            given threshold.
            >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
            False
            >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
            True
            \"\"\"
    
    The model should complete the function body after this prompt.
    """
    
    # Dataset source
    dataset_path: str = "openai/openai_humaneval"
    split: str = "test"
    
    # The prompt is just the 'prompt' field from the dataset (signature + docstring)
    doc_to_text_template: str = "{{prompt}}"
    
    # Stop sequences - generation stops when any of these are encountered
    stop_sequences: tuple[str, ...] = (
        "\nclass",
        "\ndef",
        "\n#",
        "\nif",
        "\nprint",
    )
    
    # Generation parameters for deterministic baseline
    max_gen_tokens: int = 1024
    do_sample: bool = False  # Greedy decoding for pass@1
    
    # Placeholder for future multi-sample aggregation. The current baseline runner
    # executes a single attempt per problem per run.
    num_samples_for_pass_at_k: int = 1


@dataclass(frozen=True)
class MBPPPromptConfig:
    """
    MBPP prompt configuration.
    
    The canonical format uses 3-shot prompting with test cases visible.
    
    Dataset: google-research-datasets/mbpp (full split)
    
    Prompt template:
        You are an expert Python programmer, and here is your task: {text} 
        Your code should pass these tests:

        {test_list[0]}
        {test_list[1]}
        {test_list[2]}
        [BEGIN]
    
    Model completes until [DONE] token.
    """
    
    # Dataset source
    dataset_path: str = "google-research-datasets/mbpp"
    dataset_name: str = "full"
    split: str = "test"
    
    # Prompt template
    doc_to_text_template: str = (
        "You are an expert Python programmer, and here is your task: {{text}} "
        "Your code should pass these tests:\n\n"
        "{{test_list[0]}}\n{{test_list[1]}}\n{{test_list[2]}}\n[BEGIN]\n"
    )
    
    # Stop sequences
    stop_sequences: tuple[str, ...] = ("[DONE]",)
    
    # Few-shot configuration
    num_fewshot: int = 3
    
    # Generation parameters
    do_sample: bool = False


# Canonical few-shot examples for MBPP (from lm-evaluation-harness)
MBPP_FEWSHOT_EXAMPLES = [
    {
        "task_id": 2,
        "text": "Write a function to find the similar elements from the given two tuple lists.",
        "code": (
            "def similar_elements(test_tup1, test_tup2):\r\n"
            "  res = tuple(set(test_tup1) & set(test_tup2))\r\n"
            "  return (res) "
        ),
        "test_list": [
            "assert similar_elements((3, 4, 5, 6),(5, 7, 4, 10)) == (4, 5)",
            "assert similar_elements((1, 2, 3, 4),(5, 4, 3, 7)) == (3, 4)",
            "assert similar_elements((11, 12, 14, 13),(17, 15, 14, 13)) == (13, 14)",
        ],
    },
    {
        "task_id": 3,
        "text": "Write a python function to identify non-prime numbers.",
        "code": (
            "import math\r\n"
            "def is_not_prime(n):\r\n"
            "    result = False\r\n"
            "    for i in range(2,int(math.sqrt(n)) + 1):\r\n"
            "        if n % i == 0:\r\n"
            "            result = True\r\n"
            "    return result"
        ),
        "test_list": [
            "assert is_not_prime(2) == False",
            "assert is_not_prime(10) == True",
            "assert is_not_prime(35) == True",
        ],
    },
    {
        "task_id": 4,
        "text": "Write a function to find the largest integers from a given list of numbers using heap queue algorithm.",
        "code": (
            "import heapq as hq\r\n"
            "def heap_queue_largest(nums,n):\r\n"
            "  largest_nums = hq.nlargest(n, nums)\r\n"
            "  return largest_nums"
        ),
        "test_list": [
            "assert heap_queue_largest( [25, 35, 22, 85, 14, 65, 75, 22, 58],3)==[85, 75, 65] ",
            "assert heap_queue_largest( [25, 35, 22, 85, 14, 65, 75, 22, 58],2)==[85, 75] ",
            "assert heap_queue_largest( [25, 35, 22, 85, 14, 65, 75, 22, 58],5)==[85, 75, 65, 58, 35]",
        ],
    },
]


# Type for benchmark selection
BenchmarkType = Literal["humaneval", "mbpp"]


def get_prompt_config(benchmark: BenchmarkType):
    """Get the canonical prompt configuration for a benchmark."""
    if benchmark == "humaneval":
        return HumanEvalPromptConfig()
    elif benchmark == "mbpp":
        return MBPPPromptConfig()
    else:
        raise ValueError(f"Unknown benchmark: {benchmark}")

