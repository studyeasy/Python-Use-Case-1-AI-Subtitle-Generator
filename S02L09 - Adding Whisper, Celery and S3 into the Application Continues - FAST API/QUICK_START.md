# Student Quick Start - Cognito Setup

This project uses only AWS Cognito for authentication. You need one Cognito
User Pool and one app client with a client secret.

## 1. Create a Cognito User Pool

In AWS Console:

1. Open **Amazon Cognito**.
2. Create a **User pool**.
3. Use **Email** as the sign-in option.
4. Keep required attributes simple: only **email**.
5. Create the pool.

Copy these values from the User Pool page:

```env
AWS_REGION=eu-west-2
COGNITO_USER_POOL_ID=eu-west-2_xxxxxxxxx
```

Use your own AWS region and pool id.

## 2. Create an App Client

Inside the User Pool:

1. Go to **App integration**.
2. Create an **App client**.
3. Choose **Traditional web application** or another confidential/server app type.
4. Name it `subly-app`.
5. Make sure the client has a **client secret**.
6. Enable `ALLOW_USER_PASSWORD_AUTH`.
7. Create the client.

Copy the app client id and client secret:

```env
COGNITO_APP_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
COGNITO_APP_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 3. Create `.env`

Copy `sample.env` to `.env` in the project root, then fill in your values:

```env
AWS_REGION=eu-west-2
COGNITO_USER_POOL_ID=eu-west-2_xxxxxxxxx
COGNITO_APP_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
COGNITO_APP_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Those are the only `.env` values needed for the starter app.

## 4. AWS Credentials For Local Development

The backend needs permission to call Cognito. The simplest local option is AWS
CLI:

```bash
aws configure
```

Enter:

```text
AWS Access Key ID
AWS Secret Access Key
Default region
```

Use the same region as your Cognito User Pool.

You do not need to place AWS access keys in `.env` if `aws configure` is set up.

## 5. Run The App

```bash
docker compose up --build
```

Open:

```text
http://localhost:3000
```
