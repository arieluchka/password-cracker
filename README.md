# Password Cracker Service

## How to Run

There are two ways to run the system:

### Using Docker

#### Minion Setup

Run couple minions:
```
docker run -d -e API_PORT=8000 --rm --network host arieluchka/minion-cracker
```

<br>

```
docker run -d -e API_PORT=8001 --rm --network host arieluchka/minion-cracker
```

<br>

(The minion also has a db for some crash recovery functionality, you can make it persistant)

```
docker run -d -e API_PORT=8001 -v "minion-db1:/app/minion" --rm --network host arieluchka/minion-cracker
```

<br>
<br>


#### Master Setup

```
docker run -it --rm --network host arieluchka/master-cracker
```

For data persistence (and crash recovery), you can mount a volume for the master database:
```
docker run -it --rm --network host -v master-db:/app/master arieluchka/master-cracker
```

<br>
<br>

### Running Directly

#### Prerequisites

1. Python 3.10 or later
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

#### Running Minion

```
python /minion/MinionCracker.py
```

#### Running Master

1. Start the master server:
   ```
   python /master/MasterCracker.py
   ```

2. In a separate terminal, run the CLI tool:
   ```
   python -m master.cli
   ```

   **OR**

   You can use the swagger http://localhost:5000/docs

If you have import error, try adding the folder path of the project to the `PYTHONPATH` environment variable.

on windows you can do:
```
$Env:PYTHONPATH="C:\PATH_TO\password-cracker";python .\minion\MinionCracker.py
```
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>

#### Todos
- make every configuration support env vars and cli arguments
- seperate master and minion files, so in the docker image it will have only the necessary ones.
- handle cases where minion is wasting too much time on a task
  - (combine it with the logic of performance monitoring and crack progress?)

- add benchmark function to minion, that will be executed by master, to get minions stats and best settings to run cracking in parallel (low the risk of progress loss for slow minions).

- add option for minions to add themselves to the master (need masters ip?)

- add visualization/metrics of minions hw utilization
- implement graceful shutdown
