# ab - Apache HTTP server benchmarking tool

### Example:
```
ab -n 1000 -c 500 -t 600 "http://127.0.0.1:9001/ratelimit?max_limit=20&key=gcp&interval=100" > load_test_results.txt
```

### Custom load test:
```
python loadtest.py > custom_load_test_results.txt
```
