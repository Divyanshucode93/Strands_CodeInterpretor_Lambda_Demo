# strands_ci_agent.py

import json
from strands import Agent, tool
from bedrock_agentcore.tools.code_interpreter_client import code_session
import asyncio

#Define the detailed system prompt for the assistant
SYSTEM_PROMPT = """You are a helpful AI assistant that validates all answers through code execution.

VALIDATION PRINCIPLES:
1. When making claims about code, algorithms, or calculations - write code to verify them
2. Use execute_python to test mathematical calculations, algorithms, and logic
3. Create test scripts to validate your understanding before giving answers
4. Always show your work with actual code execution
5. If uncertain, explicitly state limitations and validate what you can

APPROACH:
- If asked about a programming concept, implement it in code to demonstrate
- If asked for calculations, compute them programmatically AND show the code
- If implementing algorithms, include test cases to prove correctness
- Document your validation process for transparency
- The state is maintained between executions, so you can refer to previous results

TOOL AVAILABLE:
- execute_python: Run Python code and see output

RESPONSE FORMAT: The execute_python tool returns a JSON response with:
- sessionId: The code interpreter session ID
- id: Request ID
- isError: Boolean indicating if there was an error
- content: Array of content objects with type and text/data
- structuredContent: For code execution, includes stdout, stderr, exitCode, executionTime

For successful code execution, the output will be in content[0].text and also in structuredContent.stdout.
Check isError field to see if there was an error.

Be thorough, accurate, and always validate your answers when possible."""

#Define and configure the code interpreter tool
@tool
def execute_python(code: str, description: str = "") -> str:
    """Execute Python code"""

    if description:
        code = f"# {description}\n{code}"

    #Print code to be executed
    print(f"\n Code: {code}")


    # Call the Invoke method and execute the generated code, within the initialized code interpreter session
    with code_session("us-east-1") as code_client:
        response = code_client.invoke("executeCode", {
        "code": code,
        "language": "python",
        "clearContext": False
    })

    for event in response["stream"]:
        return json.dumps(event["result"])

#configure the strands agent including the tool(s)
agent=Agent(
        tools=[execute_python],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None)

# query="Can all the planets in the solar system fit between the earth and moon?"
query = "Summarize the contents of the data.csv file in a human readable form"

# Invoke the agent asynchcronously and stream the response
async def main():
    response_text = ""
    async for event in agent.stream_async(query):
        if "data" in event:
            # Stream text response
            chunk = event["data"]
            response_text += chunk
            print(chunk, end="")

asyncio.run(main())
