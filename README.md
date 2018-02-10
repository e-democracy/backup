E-Democarcy Backup Script
=========================

Grabs lists of group members and messages from E-Democracy via it's APIs and saves them as CSVs.

# Dependencies

## System Dependencies

### Python

Make sure you have Python 3 on your computer. The following two commands should work:

```
python --version
pip --version
```

### virtualenv and virtualenvwrapper

```
pip install virtualenv
pip install virtualenvwrapper
mkvirtualenv --python=/usr/bin/python3 backup
```


## Repo

```
git clone git@github.com:e-democracy/backup.git
cd backup 
virtualenv backup 
```

## Python Dependencies

```
pip install -r requirements.txt
```

# Run It

```
python backup.py
```
