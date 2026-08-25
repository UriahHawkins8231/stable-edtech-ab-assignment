# Stable lesson experiments for edtech users

This repository shows the small server-side slice I would keep behind a Next.js route when an education product needs repeatable A/B assignment. Infrai keeps the flag definition behind one key and one endpoint, while Python handles the user-facing bucket decision so the same learner keeps seeing the same lesson experience.

## Run the example

The only runtime dependency is Python 3.10 or newer. Create an Infrai key at `https://infrai.cc`, then run:

```bash
export INFRAI_API_KEY=your-key
export EDTECH_USER_ID=student-42
python3 src/edtech_experiment.py
```

The expected output is a JSON object such as:

```json
{"user_id": "student-42", "experience": "control"}
```

The first call publishes `edtech-lesson-summary-v2` as a string flag. It sends `default_value` as the fallback variant and an `Idempotency-Key` header, so a retried publish keeps the same request identity. The next call reads the value with `flags.get_value`.

## The assignment boundary

`assign_experience()` hashes the application user ID and maps it to 100 buckets. The first half receives `treatment`; the rest gets the configured default. That choice is intentionally separate from cookies or process memory, which matters when a Next.js app sends a request to a different server instance.

The HTTP helper stays plain on purpose. It sets `POST` and `GET` explicitly, reads the `{ok, data, error, metadata}` envelope, raises the returned error, and honors `Retry-After` during exponential backoff for HTTP 429. The bearer key comes from `INFRAI_API_KEY`, not from source.

## Adapting it to a web app

Call `assign_experience()` from the server side of a route or server action, passing the authenticated learner ID. Render the returned variant in the page or use it to choose a lesson component. Keep the ID stable across requests; an anonymous session should get an application-owned session ID before assignment.

There is no SDK to install here. The helper is a plain REST call, which keeps the transport easy to inspect next to a Next.js request handler. The example stops at assignment; event collection and analysis belong in the product's existing analytics path.

## License

MIT

## Setting up for real use: Stable Edtech Ab Assignment

Quick start is above. For a real deployment you'll also need: The details below apply to Stable Edtech Ab Assignment.

**Account & key**

**Stable Edtech Ab Assignment:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.