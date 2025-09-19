# README.md

## `output_fields`

- **Definition:**
  The complete list of fields that are *allowed* to appear in the final output for each entity.
- **Role:**
  - Acts as an **allowlist**: only fields in this list will be included in the output entities.
  - If a field is not in `output_fields`, it will be dropped from the output, even if it exists in the data.
- **Analogy:**
  Think of `output_fields` as the columns you want to see in a spreadsheet export.
- **Example:**
  If `output_fields` includes `device_id`, `area_id`, and `tier`, then only those (and other listed fields) will be present in the output.
  If an entity has a field like `foo_bar` that is not in `output_fields`, it will be removed.

---

## `required_keys`

- **Definition:**
  The subset of `output_fields` that are **mandatory** for every entity.
- **Role:**
  - Used for **validation**: after minimization, every entity must have all `required_keys` present (and not null/empty).
  - If any required key is missing from an entity, the pipeline will fail with an error.
- **Analogy:**
  Think of `required_keys` as the columns that must be filled in for every row in your spreadsheet.
- **Example:**
  If `required_keys` includes `device_id`, then every entity in the output must have a non-null `device_id`.
  If an entity is missing `device_id`, the pipeline will raise an error and stop.

---

## How They Work Together

- **`output_fields`** controls what *can* be present in the output.
- **`required_keys`** controls what *must* be present in the output.

### Example

Suppose you have:

```yaml
output_fields:
  - entity_id
  - area_id
  - device_id
  - tier
  - foo_bar

required_keys:
  - entity_id
  - area_id
  - device_id
```

- The output will only ever include the fields listed in `output_fields`.
- Every entity **must** have `entity_id`, `area_id`, and `device_id` (or the pipeline fails).
- `foo_bar` is allowed in the output, but not required—if it’s missing, that’s fine.

---

**Summary Table:**

| Field         | In output_fields | In required_keys | Result in output?         | Validation?         |
|---------------|-----------------|------------------|---------------------------|---------------------|
| entity_id     | Yes             | Yes              | Always present            | Must be present     |
| area_id       | Yes             | Yes              | Always present            | Must be present     |
| device_id     | Yes             | Yes              | Always present            | Must be present     |
| foo_bar       | Yes             | No               | Present if available      | Not required        |
| bar_baz       | No              | No               | Never present (dropped)   | Not required        |

---

**In short:**

- `output_fields` = "What fields are allowed in the output?"
- `required_keys` = "Which of those fields are absolutely required for every entity?"
