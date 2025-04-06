# Testing the Implementation
## Pytest
Framework used in order to execute tests on:
- peaq/agung
- public/private using rpc/wss endpoints

### CMDs
see how many tests will execute:
```
pytest --collect-only -q
```
test with print statements
```
pytest -s
```
test with verbose logging
```
pytest -v
```
very verbose with detailed summary (recommended)
```
pytest -vv -r a
```

log results
```
pytest -vv -r a > pytest.log
```

Only run DID tests:
```
pytest -m did -vv
```