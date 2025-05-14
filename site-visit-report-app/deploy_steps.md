# Production Deployment Steps

## Preparation

1. Update your code from the repository:
   ```bash
   git pull origin main
   ```

2. Install required tools:
   ```bash
   pip install awscli awsebcli boto3
   npm install -g netlify-cli # or vercel
   ```

## Step 1: Prepare Backend

1. Run the AWS modification script to adapt the backend:
   ```bash
   cd site-visit-report-app/backend
   python modify_app_for_aws.py
   ```

2. Configure environment variables:
   ```bash
   cd site-visit-report-app
   nano backend/.env.production
   ```
   
   Set the following:
   - ANTHROPIC_API_KEY
   - AWS credentials
   - S3_BUCKET
   - PINECONE settings
   - ALLOWED_ORIGINS (frontend URL)

## Step 2: Deploy Backend to AWS

1. Initialize Elastic Beanstalk:
   ```bash
   cd site-visit-report-app
   eb init
   ```
   
   - Choose your region
   - Name your application (e.g., site-visit-report)
   - Select Python platform (3.9)

2. Create environment and deploy:
   ```bash
   eb create site-visit-report-env
   ```

3. Set environment variables:
   ```bash
   eb setenv $(cat backend/.env.production)
   ```

4. Get your backend URL:
   ```bash
   eb status
   ```
   
   Copy the CNAME (e.g., site-visit-report-env.eba-abcdef.us-west-2.elasticbeanstalk.com)

## Step 3: Deploy Frontend

1. Update frontend configuration with backend URL:
   ```bash
   cd site-visit-report-app
   nano frontend/.env.production
   ```
   
   Set:
   ```
   REACT_APP_BACKEND_URL=https://your-elastic-beanstalk-url.elasticbeanstalk.com
   ```

2. Build the frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. Deploy to S3:
   ```bash
   aws s3 mb s3://your-site-visit-report-app
   aws s3 website s3://your-site-visit-report-app --index-document index.html --error-document index.html
   
   # Update bucket policy
   nano ../s3_policy.json
   # Replace YOUR-BUCKET-NAME with your actual bucket name
   
   aws s3api put-bucket-policy --bucket your-site-visit-report-app --policy file://../s3_policy.json
   aws s3 sync build/ s3://your-site-visit-report-app --acl public-read
   ```

4. Get the S3 website URL:
   ```
   http://your-site-visit-report-app.s3-website-us-west-2.amazonaws.com
   ```

## Step 4: Set Up CloudFront (Optional)

1. In AWS Console, create a CloudFront distribution
2. Set origin to your S3 website URL
3. Configure HTTPS and cache behavior
4. Create the distribution
5. Use the CloudFront URL for access

## Step 5: Test and Monitor

1. Test the application by accessing the frontend URL
2. Monitor backend logs:
   ```bash
   eb logs
   ```

3. Set up CloudWatch alarms in AWS Console

## Step 6: Configure Monitoring Alarms (Optional)

1. In AWS Console, go to CloudWatch
2. Create alarms for:
   - CPU usage
   - Error rates
   - Memory usage
   - Response times

## Maintenance

- Update backend code:
  ```bash
  cd site-visit-report-app
  git pull
  eb deploy
  ```

- Update frontend:
  ```bash
  cd site-visit-report-app/frontend
  git pull
  npm run build
  aws s3 sync build/ s3://your-site-visit-report-app --acl public-read
  ``` 