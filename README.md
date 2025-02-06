# fastapi-batch-inference-test


### run fastapi

```bash
poetry run fastapi dev fastapi_batch_inference_test/main.py
```


### run locust

```bash
poetry run locust -f load_test/locustfile.py --host http://localhost:8000
```