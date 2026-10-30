# API and Integrations

## API keys
Create API keys in Settings > Developer > API keys. Keys are shown only once, so store them securely. Send the key in the Authorization header as a Bearer token. Revoke a leaked key immediately from the same page.

## Rate limits
The Free plan allows 60 requests per minute. Pro allows 600 requests per minute. Business allows 3000 requests per minute. When you exceed the limit the API returns HTTP 429 with a Retry-After header. Use exponential backoff when retrying.

## Webhooks
Configure webhooks in Settings > Developer > Webhooks. We send a POST request with a JSON body and an X-Acme-Signature header signed with HMAC SHA256. Failed deliveries are retried up to 5 times over 24 hours.

## Integrations
Native integrations include Slack, GitHub, Jira, and Zapier. Connect them in Settings > Integrations. The Slack integration posts project activity to a channel of your choice.
