0. Using ~/git/aws-samples/amazon-mwaa-automating-dag-deployment project.

0-1. Create S3
aws s3api create-bucket --bucket mwaa-cicd-bucket --create-bucket-
configuration LocationConstraint=ap-northeast-2
{
"Location": "http://mwaa-cicd-bucket.s3.amazonaws.com/"
}

0-2. Put bucket versioning
aws s3api put-bucket-versioning --bucket mwaa-cicd-bucket --versioning-configuration Status=Enabled

0-3. Block public access.
aws s3api put-public-access-block --bucket mwaa-cicd-bucket --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"


1. Create CodeStar connection to GitHub repository mwaa-code-repo.
>> aws codestar-connections create-connection -provider-type GitHub --connection-name mwaa-code-repo-connection

{
    "ConnectionArn": "arn:aws:codestar-connections:ap-northeast-2:301391518739:connection/8f6b0354-3669-4848-82b4-d7b9a4672fb7"
}

2. Create a pipeline with CloudFormation.
aws cloudformation create-stack --stack-name mwaa-cicd  --template-body file://infra/pipeline.yaml  --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM --parameters ParameterKey=CodeRepoName,ParameterValue=mwaa-code-repo ParameterKey=MWAASourceBucket,ParameterValue=mwaa-code-repo-bucket ParameterKey=GitHubAccountName,ParameterValue=shkim4u ParameterKey=CodeStarConnectionArn,ParameterValue=arn:aws:codestar-connections:ap-northeast-2:301391518739:connection/8f6b0354-3669-4848-82b4-d7b9a4672fb7 ParameterKey=PYCONSTRAINTS,ParameterValue=https://raw.githubusercontent.com/apache/airflow/constraints-2.0.2/constraints-3.7.txt


---
# 선행 작업
1. mwaa-local ECR 구성

# Tweaking이 필요한 부분
1. GibHub -> BitBucket
2. 기존에 존재하는 MWAA 환경 Referencing
3. requirements.txt 파일 조정
4. Plugins: 현재는 사용하지 않지만
5. Variable Not Found 에러 해결: 해결 -> Environment
