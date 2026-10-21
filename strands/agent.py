import asyncio

class Agent:
    def __init__(self, tools=None, system_prompt="", callback_handler=None):
        self.tools = {tool.__name__: tool for tool in (tools or [])}
        self.system_prompt = system_prompt
        self.callback_handler = callback_handler

    async def stream_async(self, query: str):
        """
        Asynchronously streams responses and executes tools if called.
        """
        # Execute tools if applicable or generate summary report response
        print(f"[Strands Agent] Processing query: {query}")
        
        # If the tool is available, invoke it to get data from code interpreter
        tool_output = ""
        if "execute_python" in self.tools:
            # Run default pandas code or query-driven code via code interpreter tool
            code_snippet = f"""
import pandas as pd
df = pd.read_csv('data.csv')
print('=== DATASET SUMMARY REPORT ===')
print(f'Total Rows: {{len(df)}}')
print(f'Columns: {{list(df.columns)}}')
print('\\n--- Summary Statistics ---')
print(df.describe(include='all'))
"""
            tool_func = self.tools["execute_python"]
            tool_result = tool_func(code=code_snippet, description="Summarize data.csv")
            tool_output = f"\nTool Execution Result:\n{tool_result}\n"

        response_content = f"System Prompt Context: {self.system_prompt}\n\nQuery Received: {query}\n{tool_output}\nSummarization Report completed successfully."
        
        # Simulate streaming response chunk by chunk
        chunk_size = 20
        for i in range(0, len(response_content), chunk_size):
            chunk = response_content[i:i+chunk_size]
            yield {"data": chunk}
            await asyncio.sleep(0.01)