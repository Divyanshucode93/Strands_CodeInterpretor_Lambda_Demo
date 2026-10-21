import json
import boto3
from bedrock_agentcore.tools.code_interpreter_client import code_session

# Initialize Bedrock Runtime client in us-east-1
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

def execute_python_tool(code: str, description: str = "") -> str:
    """Execute Python code in a Bedrock AgentCore code interpreter session with data.csv preloaded."""
    if description:
        code = f"# {description}\n{code}"
    
    with code_session("us-east-1") as code_client:
        try:
            with open("data.csv", "r", encoding="utf-8") as f:
                csv_content = f.read()
            code_client.invoke("writeFiles", {
                "content": [{
                    "path": "data.csv",
                    "text": csv_content
                }]
            })
        except Exception as e:
            print(f"File load warning: {e}")

        response = code_client.invoke("executeCode", {
            "code": code,
            "language": "python",
            "clearContext": False
        })

    for event in response.get("stream", []):
        if "result" in event:
            return json.dumps(event["result"])
    return json.dumps({"status": "completed"})

def synthesize_with_claude(metrics_text: str) -> str:
    """
    Invokes Claude Sonnet 4.5 on Amazon Bedrock using the US cross-region inference profile.
    """
    # Use the US inference profile ID for Claude Sonnet 4.5
    model_id = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    
    system_prompt = (
        "You are an expert data storyteller and synthesis assistant. "
        "Take the raw technical dataset report and translate it into a clear, "
        "concise, and engaging human-readable essay/narrative paragraph format that highlights "
        "the key findings, totals, missing values, and top distributions so a non-technical "
        "user can instantly understand what the dataset represents."
    )

    user_message = f"Please synthesize this raw dataset analysis report into a fluent essay:\n\n{metrics_text}"

    response = bedrock.converse(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [{"text": user_message}]
            }
        ],
        system=[{"text": system_prompt}],
        inferenceConfig={
            "maxTokens": 1000,
            "temperature": 0.3
        }
    )

    return response["output"]["message"]["content"][0]["text"]

def lambda_handler(event, context):
    """
    AWS Lambda handler that extracts dataset metrics via code interpreter 
    and uses Claude Sonnet 4.5 to generate the final summary.
    """
    # 1. Python code to analyze data.csv using pandas
    analysis_code = """
import pandas as pd
df = pd.read_csv('data.csv')
print(f'Total Rows: {len(df)}')
print(f'Columns: {list(df.columns)}')
print('Missing Values: None found' if df.isnull().sum().sum() == 0 else f'Missing: {df.isnull().sum().to_dict()}')
print(f'Top Name: {df["Name"].mode()[0]} (Count: {df["Name"].value_counts().iloc[0]})')
print(f'Top Place: {df["Place"].mode()[0]} (Count: {df["Place"].value_counts().iloc[0]})')
print(f'Top Animal: {df["Animal"].mode()[0]} (Count: {df["Animal"].value_counts().iloc[0]})')
print(f'Top Thing: {df["Thing"].mode()[0]} (Count: {df["Thing"].value_counts().iloc[0]})')
"""

    # 2. Execute analysis via code interpreter
    raw_result_json = execute_python_tool(code=analysis_code, description="Extract dataset summary metrics")
    raw_data = json.loads(raw_result_json)
    stdout_text = raw_data.get("structuredContent", {}).get("stdout", "No output generated.")

    # 3. Synthesize the report using Claude Sonnet 4.5 via Bedrock
    readable_narrative = synthesize_with_claude(stdout_text)

# Return the clean human-readable narrative text directly
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/plain"},
        "body": readable_narrative
    }