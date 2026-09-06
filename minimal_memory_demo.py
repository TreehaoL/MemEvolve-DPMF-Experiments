import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from EvolveLab.memory_types import (
    MemoryRequest,
    MemoryStatus,
    TrajectoryData,
)
from EvolveLab.providers.lightweight_memory_provider import (
    LightweightMemoryProvider,
)


load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_name = os.getenv("DEFAULT_MODEL")

if not api_key or not base_url or not model_name:
    raise RuntimeError("Missing API configuration in .env")

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)


def deepseek_model(messages):
    """Adapt MemEvolve message format to the OpenAI-compatible API."""
    normalized_messages = []

    for message in messages:
        content = message.get("content", "")

        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            content = "\n".join(text_parts)

        normalized_messages.append(
            {
                "role": message.get("role", "user"),
                "content": str(content),
            }
        )

    response = client.chat.completions.create(
        model=model_name,
        messages=normalized_messages,
        temperature=0,
    )

    return response.choices[0].message.content or ""


storage_dir = Path("./storage/lightweight_memory_demo")

provider = LightweightMemoryProvider(
    {
        "model": deepseek_model,
        "storage_dir": str(storage_dir),
        "longterm_memory_path": str(storage_dir / "longterm_memory.json"),
        "enable_longterm_provision": True,
        "top_k_longterm": 3,
        "shortterm_provision_interval": 1,
    }
)

print("\n=== 1. Initialize memory system ===")
initialized = provider.initialize()
print("Initialized:", initialized)

if not initialized:
    raise RuntimeError("Memory provider initialization failed")


print("\n=== 2. Retrieve cold-start memory ===")
first_query = "How should I solve a numerical task involving unit conversion?"

first_response = provider.provide_memory(
    MemoryRequest(
        query=first_query,
        context="",
        status=MemoryStatus.BEGIN,
    )
)

print("Retrieved memory count:", first_response.total_count)

for index, memory in enumerate(first_response.memories, start=1):
    print(f"\nMemory {index}:")
    print(memory.content)


print("\n=== 3. Ingest one successful trajectory ===")
trajectory = TrajectoryData(
    query="Convert 2.5 kilometers to meters.",
    trajectory=[
        {
            "step": 1,
            "action": "Identify the conversion relation",
            "observation": "1 kilometer equals 1000 meters.",
        },
        {
            "step": 2,
            "action": "Perform the calculation",
            "observation": "2.5 multiplied by 1000 equals 2500.",
        },
        {
            "step": 3,
            "action": "Return the result with units",
            "observation": "The result is 2500 meters.",
        },
    ],
    result="2500 meters",
    metadata={
        "is_correct": True,
        "task_success": True,
        "full_query": "Convert 2.5 kilometers to meters.",
    },
)

success, description = provider.take_in_memory(trajectory)

print("Ingestion success:", success)
print("Description:", description)


print("\n=== 4. Inspect stored memory database ===")
database_path = storage_dir / "longterm_memory.json"

if not database_path.exists():
    raise FileNotFoundError(f"Memory database not found: {database_path}")

database = json.loads(database_path.read_text(encoding="utf-8"))

strategic = database.get("strategic", [])
operational = database.get("operational", [])

print("Database path:", database_path.resolve())
print("Strategic memories:", len(strategic))
print("Operational memories:", len(operational))

print("\nLatest strategic memory:")
if strategic:
    print(json.dumps(strategic[-1], ensure_ascii=False, indent=2))

print("\nLatest operational memory:")
if operational:
    print(json.dumps(operational[-1], ensure_ascii=False, indent=2))


print("\n=== MINIMAL MEMORY DEMO COMPLETED ===")
