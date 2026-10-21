FROM public.ecr.aws/lambda/python:3.12

# Copy requirements and install pure python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code, dataset, and local strands package directory
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY data.csv ${LAMBDA_TASK_ROOT}
COPY strands/ ${LAMBDA_TASK_ROOT}/strands/

# Set the CMD to your handler
CMD [ "lambda_function.lambda_handler" ]