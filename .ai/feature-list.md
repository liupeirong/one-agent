# one-agent feature list

> Note: Work with the user to record features in the features field of this TypeScript interface:
enum status_legend {
    not_started, // Work has not begun
    in_progress, // The feature is the current active task
    blocked, // Work cannot continue until a documented blocker is resolved
    passing // Required verification has passed and evidence is recorded
},
interface feature_list {
    last_updated: string, // YYYY-MM-DD HH-mm
    id: string; // ex. "db-integration-001",
    priority: number; // 1, 2, 3 - from high to low
    area: string; // ex. "llm integration", "memory management"
    title: string;
    user_visible_behavior: string; // what can the user do?
    status: status_legend;
    verification: string[]; // what needs to be true to call the feature complete
    evidence: string[]; // what's validated
    notes: string; // anything to note about this feature
}[]

```json
```
