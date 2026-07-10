# Security

Never commit OpenAI or BeliefBench service credentials. Set `OPENAI_API_KEY`,
`BELIEFBENCH_SERVICE_TOKEN`, and `BELIEFBENCH_API_URL` in the environment.

The SDK sends secrets only to the configured HTTPS BeliefBench URL. It does not
write them to configuration or result archives. Verify the service hostname
before submitting a job. Report suspected credential exposure privately to the
repository owner and rotate the affected key immediately.
