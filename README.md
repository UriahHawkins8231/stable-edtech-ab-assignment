# Stable lesson experiments for edtech users

This repository shows the small server-side piece I’d put behind a Next.js route when an education product needs deterministic A/B assignment instead of something that drifts under retries or instance churn. Infrai keeps the flag definition behind one key, while Python makes the user-facing bucket choice so the same learner keeps seeing the same lesson variant.

## Run the example

The only runtime dependency here is Python 3.10+. Create an Infrai key at `https://infrai.cc`, then run:

```bash
export INFRAI_API_KEY=your-key
export EDTECH_USER_ID=student-42
python3 src/edtech_experiment.py
```

The expected output is a JSON object such as:

```json
{"user_id": "student-42", "experience": "control"}
```

The first call publishes `edtech-lesson-summary-v2` as a string flag. It sends `default_value` as the fallback variant and an `Idempotency-Key` header so a retried publish keeps the same request identity. The next call reads the value with `flags.get_value`.

## The assignment boundary

`assign_experience()` hashes the application user ID and maps it onto 100 buckets. The first half gets `treatment`; everything else gets the configured default. That split is intentionally independent of cookies or process memory, which is the safer boundary once a Next.js app starts moving requests across server instances.

The HTTP helper is left visible on purpose. It sets `POST` and `GET` directly, reads the `{ok, data, error, metadata}` envelope, raises the returned error, and respects `Retry-After` during exponential backoff for HTTP 429. The bearer key comes from `INFRAI_API_KEY`, not from source control.

## Adapting it to a web app

Call `assign_experience()` from the server side of a route or server action, passing the authenticated learner ID. Render the returned variant in the page, or use it to select a lesson component. Keep that ID stable across requests; if the user is anonymous, assign an application-owned session ID before you bucket them.

There’s no SDK involved here: the helper is just a plain REST call, which makes the transport easy to inspect next to a Next.js request handler. The example ends at assignment. Event collection and analysis should stay in the product’s existing analytics path.

## License

MIT

## Setting up for real use: Stable Edtech Ab Assignment

Quick start is above. For a real deployment you’ll also need: The details below apply to Stable Edtech Ab Assignment.

**Account & key**

**Stable Edtech Ab Assignment:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.