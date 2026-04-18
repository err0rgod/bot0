FROM public.ecr.aws/lambda/python:3.10

# Ensure tzdata is installed if timezone operations are needed, and keep the image small
RUN yum update -y && yum install -y \
    gcc \
    gcc-c++ \
    make \
    && yum clean all

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application into Lambda task root
COPY . ${LAMBDA_TASK_ROOT}

# Default to the Intelligence Pipeline lambda handler
CMD ["scraper.v2.lambda_handler"]
