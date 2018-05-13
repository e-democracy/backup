[![CircleCI](https://circleci.com/gh/e-democracy/backup/tree/master.svg?style=svg)](https://circleci.com/gh/e-democracy/backup/tree/master)

E-Democarcy Backup Script
=========================

Grabs lists of group members and messages from E-Democracy via it's APIs and saves them to a SQLite Database.

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

# Configuration

## Script

Copy `config/script.conf.example` to `config/script.conf` and edit as needed.

## Logging

Copy `config/logging.conf.example` to `config/logging.conf` and edit as needed.

# Database

## Run Migrations

On the test DB: `yoyo apply`

On the prod DB: `yoyo apply --database sqlite:///db/prod.sqlite`

## New Migration

```
yoyo new -m "purpose of migration"
```

# Test It

```
nosetests
```

# Run It

```
EDEM_ENV=production python script.py
```

If the `EDEM_ENV` environment variable is not specified, `test` will be used as the environment.

You will be prompted to select a command to run:

* 1 - Download the current membership of every group, and the profile of every member. Any existing group membership or profile data will be overwritten.
* 2 - Download all message IDs for messages posted in a specific month. This uses group information from command 1.
* 3 - Download all message IDs for all messages ever posted. This uses group information from command 1.
* 4 - Download the mblox bodies of any saved message ID that does not currently have a saved body. This command uses information from commands 2 or 3.
      This command can be interrupted; subsequent runs of this command will continue on from where previous runs left off.
