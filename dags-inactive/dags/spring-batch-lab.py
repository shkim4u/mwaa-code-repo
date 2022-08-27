"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
# import boto3
import os
from airflow import DAG
from airflow.models import Variable
from datetime import datetime
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
# from kubernetes.client import models as k8s

default_args = {
    'owner': 'aws',
    'depends_on_past': False,
    'start_date': datetime(2022, 6, 15),
    'provide_context': True
}

# dag = DAG('spring-batch-lab', default_args=default_args, schedule_interval=None)
# dag = DAG('spring-batch-lab', default_args=default_args, schedule_interval='*/5 * * * *')
dag = DAG('spring-batch-lab', default_args=default_args, schedule_interval='@daily')

# [2022-06-20] Setting AWS credentials from variables.
# [2022-06-20] Not working! - Credentials do not seem to be passed to KubernetesPodOperator.
# aws_access_key_id = Variable.get("aws_access_key_id")
# aws_secret_access_key = Variable.get("aws_secret_access_key")
# aws_default_region = Variable.get("aws_default_region")
# if not ((not aws_access_key_id) or (not aws_secret_access_key) or (not aws_default_region)):
#     os.environ['AWS_ACCESS_KEY_ID'] = aws_secret_access_key
#     os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
#     os.environ['AWS_DEFAULT_REGION'] = aws_default_region

#use a kube_config stored in s3 dags folder for now
kube_config_path = '/usr/local/airflow/dags/kube_config.yaml'
now = datetime.now()

podRun = KubernetesPodOperator(
    namespace="mwaa",
    image="301391518739.dkr.ecr.ap-northeast-2.amazonaws.com/eksworkshop-buildanddeliverystack-repository:latest",
    cmds=[
        "/bin/sh",
        "-c" ,
        "exec java -XX:+HeapDumpOnOutOfMemoryError -Djava.security.egd=file:/dev/.urandom -Duser.timezone=Asia/Seoul -jar /spring-batch-lab.jar "
        "--jobName=SyncEgiftCardOrderInfoJob "
        "--fileName=https://raw.githubusercontent.com/benas/spring-batch-lab/master/blog/spring-batch-kubernetes/data/sample1.csv "
        "--ts=\"" + str(now) + "\""
    ],
    # arguments=[
    #     "--jobName=SyncEgiftCardOrderInfoJob",
    #     "--fileName=https://raw.githubusercontent.com/benas/spring-batch-lab/master/blog/spring-batch-kubernetes/data/sample1.csv",
    #     "--ts=" + str(now)
    # ],
    env_vars={
        'SPRING_DATASOURCE_DRIVER-CLASS-NAME': 'com.mysql.cj.jdbc.Driver',
        'SPRING_DATASOURCE_URL': 'jdbc:mysql://mysql-cluster-ip-service/test',
        # TODO: From Secret.
        'SPRING_DATASOURCE_USERNAME': 'root',
        'SPRING_DATASOURCE_PASSWORD': 'root',
        'spring.batch.job.enabled': 'false'
    },
    labels={"foo": "bar"},
    name="mwaa-spring-batch-lab",
    task_id="mwaa-spring-batch-lab-task",
    get_logs=True,
    dag=dag,
    is_delete_operator_pod=True,
    config_file=kube_config_path,
    in_cluster=False,
    cluster_context='aws'
)
