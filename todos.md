### Important
- re schedule job of UnAvailable minion
 - crash recovery
   - will go over all job assignments with Status InProgress, and do /status/{hash_value}/{start_range}/{end_range} to all those minions

- handle cases where minion is wasting too much time on a task
  - (combine it with the logic of performance monitoring and crack progress?)

- create explanations of how i achived every request from assignment (restful comms/crash handling/workload division with one hash)




### Others
 
- add command arguments

**MasterCracker**:
...

**MinionCracker**:
- API_PORT
- MASTER_IP
- MASTER_PORT
- max workers (if not set, will use maximum available)


- ADD LOGS

- Add debug mode cli argument to print logs to stdout?

- use psutil to track minion utilization and report it?


### Pretty touches
- seperate master and minion files, so in the docker image it will have only the necessary ones.



## Bonus todo
- add benchmark function to minion, that will be executed by master, to get minions stats and best settings to run cracking in parallel.
- add visualization/metrics of minions hw utilization
- add option for minions to add themselves to the master
- add get endpoint for minions to report any found hashes and passwords (if there are more masters/master is purged)
- dynamically support different hash algorithms
- verify input hashes are md5 [option](https://github.com/psypanda/hashID)
- Get minions CPU/memory, to choose better ranges.

