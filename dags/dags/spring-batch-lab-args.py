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
from typing import Dict
from airflow.decorators import dag
from airflow.decorators import task
from airflow.operators.python import get_current_context
from datetime import datetime
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator
from airflow.models.variable import Variable

default_args = {
    'owner': 'aws',
    'depends_on_past': False,
    'start_date': datetime(2022, 6, 15),
    'provide_context': True
}

#use a kube_config stored in s3 dags folder for now
# kube_config_path = '/usr/local/airflow/dags/kube_config.yaml'
kube_config_path = './dags/kube_config.yaml'
now = datetime.now()

container_image = Variable.get("spring-batch-lab-image")
interval = Variable.get("spring-batch-lab-interval")

sync_batch_default_args = {
    'namespace': 'mwaa',
    # TODO: 환경별로 이미지 변경: (1안) MWAA 분리, (2안) DAG 이름 접두사 사용
    # 'image': '301391518739.dkr.ecr.ap-northeast-2.amazonaws.com/eksworkshop-buildanddeliverystack-repository:latest',
    'image': container_image,
    # TODO: 스프링 프로파일: (1안) 현재와 같이 env_vars 사용, (2안) ConfigMap 사용
    # 'env_vars': {
    #     'SPRING_DATASOURCE_DRIVER-CLASS-NAME': 'com.mysql.cj.jdbc.Driver',
    #     'SPRING_DATASOURCE_URL': 'jdbc:mysql://mysql-cluster-ip-service/test',
    #     # TODO: From Secret.
    #     'SPRING_DATASOURCE_USERNAME': 'root',
    #     'SPRING_DATASOURCE_PASSWORD': 'root',
    #     'spring.batch.job.enabled': 'false'
    # },

    'env_vars': {
        'SPRING_PROFILES_ACTIVE': 'dev'
    },

    # [2022-06-27] Environment Variable을 위해 ConfigMap 사용 가능
    # [2022-07-16] Spring Profiles
    # 'configmaps': [
    #     "spring-batch-lab-env"
    # ],
    'config_file': kube_config_path,
    'in_cluster': False,
    'cluster_context': "aws",
}

@dag(
    default_args=default_args,
    schedule_interval=interval
)
def sync_batch_simulator() :
    @task
    def get_interval() -> Dict[str, str]:
        context = get_current_context()

        overlap_duration_in_seconds = 10
        # start_date = (context["data_interval_start"].in_timezone(local_tz) - datetime.timedelta(seconds=overlap_duration_in_seconds)).format("YYYY-MM-DDTHH:mm:ss")
        # end_date = context["data_interval_end"].in_timezone(local_tz).format("YYYY-MM-DDTHH:mm:ss")

        # return {"start_date": start_date, "end_date": end_date}

        return {"ts": str(now).replace(" ", "_")}

    interval = get_interval()

    # (참고) 아래에서 "cmds" 파라미터를 지정하지 않으면 컨테이너의 ENTRYPOINT가 사용
    # (주의)
    #   - ENCTRYPOINT가 Shell (예: /bin/sh)에 의해 Invoke될 경우 "arguments" 파라미터가 효과가 있으려면
    #     ENTRYPOINT에서 "${0} ${@}"로 받아줘야 한다.
    #   - 예: ENTRYPOINT ["/bin/sh", "-c" , "exec java -XX:+HeapDumpOnOutOfMemoryError -Djava.security.egd=file:/dev/.urandom -Duser.timezone=Asia/Seoul -jar /spring-batch-lab.jar ${0} ${@}" ]
    podRun = KubernetesPodOperator(
        **sync_batch_default_args,
        arguments=[
            "--jobName=SyncEgiftCardOrderInfoJob",
            "--fileName=https://raw.githubusercontent.com/benas/spring-batch-lab/master/blog/spring-batch-kubernetes/data/sample1.csv",
            f"--ts={interval['ts']}"
        ],
        # env_vars={
        #     'SPRING_DATASOURCE_DRIVER-CLASS-NAME': 'com.mysql.cj.jdbc.Driver',
        #     'SPRING_DATASOURCE_URL': 'jdbc:mysql://mysql-cluster-ip-service/test',
        #     # TODO: From Secret.
        #     'SPRING_DATASOURCE_USERNAME': 'root',
        #     'SPRING_DATASOURCE_PASSWORD': 'root',
        #     'spring.batch.job.enabled': 'false'
        # },
        # # [2022-06-27] Environment Variable을 위해 ConfigMap 사용 가능
        # configmaps=[
        #     "spring-batch-lab-env"
        # ],
        labels={"foo": "bar"},
        name="mwaa-spring-batch-lab-args",
        task_id="mwaa-spring-batch-lab-task-args",
        get_logs=True,
        # dag=dag,
        is_delete_operator_pod=False,
        # config_file=kube_config_path,
        # in_cluster=False,
        # cluster_context='aws'
    )

    interval >> podRun

dag = sync_batch_simulator()
