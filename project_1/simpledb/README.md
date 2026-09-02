# SimpleDB Scripts

One-off scripts used during development to double check that classification
results were correctly stored in a SimpleDB domain (`<ASU_ID>-simpleDB`).
Not part of the request-serving path.

- **`simpleDB_init.py`** — reads a CSV of `Image,Results` rows and verifies
  each one is present and matches in the SimpleDB domain (the code that
  originally wrote the attributes is left commented out).
- **`simpleDB_delete.py`** — deletes the SimpleDB domain if it exists.

Both scripts use the default boto3 credential chain — configure credentials
via `aws configure` or environment variables before running them. Neither
file contains any embedded credentials.

```bash
pip install boto3 pandas
python simpleDB_init.py
python simpleDB_delete.py
```
