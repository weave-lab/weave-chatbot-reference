import argparse
import json
from typing import Dict, List, Any
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Import application components
from app import (
    PROJECT_ID,
    LOCATION,
    init_vector_store,
    read_prompt_from_file,
    retrieve_context,
    generate_chat_response,
)

# Evaluation constants
JUDGE_MODEL = "gemini-2.5-pro"
JUDGE_TEMPERATURE = 0.0  # Deterministic evaluation for consistency


# Pydantic models for structured data validation
class AnswerQualityResponse(BaseModel):
    """Structure for LLM-generated answer quality evaluation responses."""

    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0.0 and 1.0")
    reasoning: str = Field(..., description="Brief explanation for the score")


class UsefulnessResponse(BaseModel):
    """Structure for LLM-generated usefulness evaluation responses."""

    useful: bool = Field(..., description="True if context chunk was useful")


class EvaluationCase(BaseModel):
    """Structure for individual test cases in the evaluation dataset."""

    question: str = Field(..., description="The question to ask the RAG system")
    expected_answer: str = Field(..., description="The expected/correct answer")


def get_answer_quality_score(
    client: genai.Client,
    question: str,
    reference_answer: str,
    predicted_answer: str,
    model: str = JUDGE_MODEL,
) -> float:
    """
    Evaluate the quality of a predicted answer against a reference answer.

    This function uses an LLM to judge how well the predicted answer addresses
    the question compared to the reference answer. It's more nuanced than simple
    text matching because it compares semantic meaning and context.

    Score range: 0.0 to 1.0 (higher is better)
    - 1.0 = Excellent answer (accurate, complete, addresses the question well)
    - 0.5 = Partially correct (some relevant info but incomplete or minor errors)
    - 0.0 = Poor answer (major errors, irrelevant, or completely misses the point)
    """
    system_instruction = (
        "You are an expert evaluator for question-answering systems. Your task is to assess "
        "how well a model's predicted answer addresses the given question compared to a "
        "reference answer. Consider both factual accuracy and completeness."
    )

    # Define the structure we want the LLM to return
    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "score": types.Schema(
                type=types.Type.NUMBER,
                description="Quality score: 0.0 = Poor/Incorrect, 0.5 = Partially Correct, 1.0 = Good/Complete",
            ),
            "reasoning": types.Schema(
                type=types.Type.STRING, description="Brief explanation for the score"
            ),
        },
        required=["score", "reasoning"],
    )

    evaluation_prompt = (
        f"Evaluate the PREDICTED answer against the REFERENCE answer for the given QUESTION.\n\n"
        f"QUESTION: {question}\n\n"
        f"REFERENCE: {reference_answer}\n\n"
        f"PREDICTED: {predicted_answer}\n\n"
        f"Rate the PREDICTED answer using this scale:\n"
        f"- 0.0: Poor/Incorrect - Major factual errors, irrelevant, or completely misses the point\n"
        f"- 0.5: Partially Correct - Some relevant information but incomplete or contains minor errors\n"
        f"- 1.0: Good/Complete - Accurate, addresses the question well, consistent with reference\n\n"
        f"Provide your assessment as JSON with 'score' and 'reasoning' fields."
    )

    config = types.GenerateContentConfig(
        temperature=JUDGE_TEMPERATURE,
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=response_schema,
    )

    response = client.models.generate_content(
        model=model, contents=evaluation_prompt, config=config
    )
    if not response or not response.text:
        raise ValueError("Failed to generate evaluation response.")

    response_data = json.loads(response.text.strip())
    validated_response = AnswerQualityResponse(**response_data)

    return validated_response.score


def calculate_contextual_precision(
    client: genai.Client,
    question: str,
    reference_answer: str,
    retrieved_contexts: List[str],
) -> float:
    """
    Calculate how well relevant context chunks are ranked in the retrieval results.

    This metric tells us: "Are the most useful pieces of information appearing first?"

    LLMs have limited attention and can be distracted by irrelevant information.
    When irrelevant contexts appear early, they can mislead the model.
    Additionally, irrelevant information increases context length.
    Good retrieval systems should rank the most useful information first.

    How it works:
    1. For each retrieved context chunk, ask an LLM: "Was this context useful in arriving at the answer?"
    2. Calculate weighted precision: Each useful context contributes based on its position
    3. Formula: sum([(relevant_count_up_to_k / k) * is_useful_k]) / total_useful_contexts

    Example with K=4 retrieved contexts where positions 1 and 3 are useful:
    - Position 1: Useful → contributes (1/1) * 1 = 1.0
    - Position 2: Not useful → contributes (1/2) * 0 = 0.0
    - Position 3: Useful → contributes (2/3) * 1 = 0.67
    - Position 4: Not useful → contributes (2/4) * 0 = 0.0
    - Final score = (1.0 + 0.0 + 0.67 + 0.0) / 2 = 0.83

    Score range: 0.0 to 1.0 (higher is better)
    - 1.0 = Perfect ranking (all useful contexts appear first)
    - 0.0 = Poor ranking (no useful contexts found)

    This metric is based on RAGAS library
    https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/context_precision

    Context Recall is also equally important that measures how many relevant contexts were successfully retrieved.
    https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/context_recall/
    """
    if not retrieved_contexts:
        return 0.0

    # Define schema for usefulness response
    usefulness_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "useful": types.Schema(
                type=types.Type.BOOLEAN,
                description="True if context chunk was useful in arriving at the given answer",
            )
        },
        required=["useful"],
    )

    # Determine usefulness of each context chunk using LLM
    usefulness_scores = []

    # Total number of retrieved contexts
    K = len(retrieved_contexts)

    for context_chunk in retrieved_contexts:
        usefulness_prompt = (
            f"Given the following question, context chunk, and answer, determine if the context chunk "
            f"was useful in arriving at the given answer.\n\n"
            f"Question: {question}\n"
            f"Context chunk: {context_chunk}\n"
            f"Answer: {reference_answer}\n\n"
            f"Respond with JSON containing 'useful' field (true/false)."
        )

        response = client.models.generate_content(
            model=JUDGE_MODEL,
            contents=usefulness_prompt,
            config=types.GenerateContentConfig(
                temperature=JUDGE_TEMPERATURE,
                response_mime_type="application/json",
                response_schema=usefulness_schema,
            ),
        )
        if not response or not response.text:
            raise ValueError("Failed to generate usefulness response.")

        response_data = json.loads(response.text.strip())
        validated_response = UsefulnessResponse(**response_data)
        usefulness_scores.append(validated_response.useful)

    total_useful_contexts = sum(usefulness_scores)

    # If no contexts are useful, precision is 0
    if total_useful_contexts == 0:
        return 0.0

    # Calculate numerator: sum of (precision@rank_i * usefulness_i) for all i
    # This weights each useful context by the precision up to its position
    numerator = sum(
        [
            # precision@rank_i: how many useful contexts in first (i+1) positions
            (sum(usefulness_scores[: i + 1]) / (i + 1)) * usefulness_scores[i]
            for i in range(K)  # For each position from 0 to K-1
        ]
    )

    return numerator / total_useful_contexts


def load_evaluation_cases(goldens_path: str) -> List[EvaluationCase]:
    """
    Load test cases from a JSONL file for evaluation.

    Each line in the file should be a JSON object with at least:
    - question: The question to ask
    - expected_answer: The correct/expected answer
    """
    with open(goldens_path, "r") as f:
        cases = [
            EvaluationCase(**json.loads(line.strip())) for line in f if line.strip()
        ]

    return cases


def evaluate_rag_system(goldens_path: str, prompt_version: str = "v1") -> None:
    # Set up all the components we need for evaluation
    genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    vector_store = init_vector_store(genai_client)
    system_prompt = read_prompt_from_file(prompt_version)

    # Load our test cases
    evaluation_cases = load_evaluation_cases(goldens_path)

    if not evaluation_cases:
        print("Error: No valid evaluation cases found")
        return

    print(f"Starting evaluation with {len(evaluation_cases)} test cases...")
    print("-" * 60)

    # Keep track of scores for all test cases
    answer_quality_scores = []
    precision_scores = []
    # Maintain conversation history across test cases
    chat_history: List[Dict[str, Any]] = []

    # Evaluate each test case
    for idx, case in enumerate(evaluation_cases, 1):
        question = case.question
        reference_answer = case.expected_answer

        # Generate response using the RAG system
        context_snippets = retrieve_context(
            client=genai_client,
            vector_store=vector_store,
            user_message=question,
        )
        predicted_answer = generate_chat_response(
            client=genai_client,
            system_prompt=system_prompt,
            user_message=question,
            chat_history=chat_history,
            context_snippets=context_snippets,
        )

        # Update chat history to maintain conversation context
        chat_history.append({"role": "user", "parts": [{"text": question}]})
        chat_history.append({"role": "model", "parts": [{"text": predicted_answer}]})

        # Evaluate the quality of the generated answer
        answer_quality_score = get_answer_quality_score(
            client=genai_client,
            question=question,
            reference_answer=reference_answer,
            predicted_answer=predicted_answer,
        )

        # Evaluate the quality of context retrieval
        precision_score = calculate_contextual_precision(
            client=genai_client,
            question=question,
            reference_answer=reference_answer,
            retrieved_contexts=context_snippets,
        )

        # Store scores for final summary
        answer_quality_scores.append(answer_quality_score)
        precision_scores.append(precision_score)

        # Show results for this test case
        print(f"Test Case {idx}:")
        print(f"  Question: {question}")
        print(f"  Expected: {reference_answer}")
        print(f"  Generated: {predicted_answer}")
        print(f"  Retrieved Context: {context_snippets}")
        print(f"  Answer Quality: {answer_quality_score:.1f}/1.0")
        print(f"  Context Precision: {precision_score:.3f}")
        print()

    # Calculate overall performance across all test cases
    avg_answer_quality = sum(answer_quality_scores) / len(answer_quality_scores)
    avg_precision = sum(precision_scores) / len(precision_scores)

    # Generate YAML evaluation summary
    yaml_content = f"""evaluation_summary:
  total_test_cases: {len(evaluation_cases)}
  prompt_version: {prompt_version}
  answer_quality:
    average_score: {avg_answer_quality:.3f}
    max_score: 1.0
  context_precision:
    average_score: {avg_precision:.3f}
    max_score: 1.0
  individual_scores:
    answer_quality: {answer_quality_scores}
    context_precision: {precision_scores}
"""

    # Save to file
    with open("evaluation_results.yaml", "w") as f:
        f.write(yaml_content)

    print(f"Average Answer Quality: {avg_answer_quality:.3f}/1.0")
    print(f"Average Context Precision: {avg_precision:.3f}/1.0")


def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG system performance")
    parser.add_argument(
        "--prompt-version",
        default="v1",
        help="Version of the system prompt to use (default: v1)",
    )
    parser.add_argument(
        "--goldens-path",
        default="goldens.jsonl",
        help="Path to the test cases file (default: goldens.jsonl)",
    )

    args = parser.parse_args()

    # Run the evaluation
    evaluate_rag_system(args.goldens_path, args.prompt_version)


if __name__ == "__main__":
    main()
