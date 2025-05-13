### Install dependencies
```
pip install -r requirements.txt
```



### Crash handling
Both Master and Minion are using sqlite db to keep track of certain information.

Master has scheduled tasks to
- monitor minions health and status