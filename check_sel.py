#!/usr/bin/python3
import pytest

def main():
    pytest.main()

if __name__ == "__main__":
    main()

#docker exec -it $(docker ps -q -n=1) bash
#/etc/unlock_keyring.sh
#python -m keyring set https://upload.pypi.org/legacy/ alex-ber
#python setup.py clean sdist upload