# Progress Log

> Append session logs conforming to this TypeScript schema:
interface session_log {
    datetime: string; // session start datetime YYYY-MM-DD HH-mm
    current_feature: string; // which feature is worked on in this session?
    what_was_done: string[]; // what's implemented, tested, bugs fixed etc
    decision: string[]; // what decisions were made, changed
    issues: string[]; // what issues were encountered, what's their status now
    benchmark_results?: Record<string, string>; // performance benchmark numbers if any, ex. {Query_What_is_the_architecture: "~250ms with 2 citations"}
    next_step: string;
}[]

```json
```
