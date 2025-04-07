# peaq-sdk

Python implementation of peaq functions. Offers the following capabilities:

- DID creation
- peaq Storage utilization
- RBAC capabilities
<!-- - UMT calls -->



# Development
## Create virtual env
Unix/macOS
```
python3 -m venv working_env
source working_env/bin/activate
```
leave with cmd: `deactivate`

## Install requirements
```
pip install -r requirements.txt
```

## Build package
To build the package you can execute the cmd:
```
python -m build
```
This will create a .zip local instance of the package in the `dist/` directory

# Using the sdk
Link the reference to documentation

## You clearly document how the SDK handles private keys.
Be Sure to Explain:
- Private key is only ever used to create an account or keypair and it is never sent/logged. 
    - Code is open sourced so customers can guarantee this fact. 
- All signing happens locally.
- Never share the key with anyone.
- Projects need to guarantee their local environments of the sdk are safe-guarded


## NOTES
- user needs to make sure the address who constructed the tx is the same one that sends it