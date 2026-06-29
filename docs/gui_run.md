# Running Escape FID From The Thalamus GUI

## 1. Launch Thalamus

From Terminal:

```bash
cd /Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape
./run_escape.sh
```

This opens two main windows:

- `Task Controller`: the experimenter/control window.
- Subject/stimulus window: the display where the participant sees the task.

The launcher uses Python pipeline mode (`-y`) because the local Thalamus source
checkout does not include the compiled `thalamus/native` executable.

## 2. Create A Task Cluster

In the `Task Controller` window:

1. Open `File`.
2. Click `Create Task Cluster`.
3. In the new cluster tab, set `Name` to `Escape`.
4. Set `Weight` to `1`.

## 3. Add The Escape Task

Inside the `Escape` task cluster tab:

1. Click `Add Task`.
2. Set `Task Name` to `Escape FID`.
3. Open the `Task Type` dropdown.
4. Select `Escape FID (Predator)`.
5. Set `Goal` to a small pilot value, such as `5` or `10`.

The task-specific configuration panel appears below. For a first run, leave the
defaults unchanged.

## 4. Enqueue The Task

Use either path:

- Click `Enqueue Task` on the `Escape FID` task row.
- Or click `Enqueue Task Cluster` on the cluster row.

You should see an item appear in the right-side `Queue` panel.

## 5. Optional: Add Recording

For a visual-only dry run, skip this step.

Escape always writes local per-session data under:

```text
/Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape/data/<SESSION_ID>/
```

Use `STORAGE2` only when you also want a Thalamus `.tha` recording.

For recording:

1. In the Thalamus pipeline window, click `Add` to create a node.
2. Change the node type to `STORAGE2`.
3. Set `Output File` to an absolute path, for example:

   ```text
   /Users/kamrenkhan/Desktop/Research/RESTORE/Project/escape/Pilot Data/session01
   ```

4. In the `STORAGE2` node widget, add the task controller node as a source.
5. Enable `Text`; enable `Time Series` only if needed.
6. Set `Running` only after the output path and source are configured.

The escape task writes JSON records to the text stream:

- `escape_trial_start`
- `escape_reward`
- `escape_attack`
- `escape_frame`
- `escape_trial`

## 6. Start The Run

In the `Task Controller` window:

1. Open `File`.
2. Click `Start/Stop`.
3. Click inside the subject/stimulus window so it has keyboard focus.
4. Use the arrow keys:
   - Hold left arrow to move toward the predator and collect dots.
   - Hold right arrow to retreat to the safe zone.

When the queued goal reaches zero, the task stops scheduling new trials.

## 7. Stop Or Reset

- To pause or stop execution: `File` -> `Start/Stop`.
- To abort the current trial: `File` -> `Cancel Current Task`.
- To remove queued runs: select items in the `Queue` panel and click `Delete Selected`.

## Common Issues

### `No such file or directory: .../thalamus/native`

Use `./run_escape.sh`, not the manual command without `-y`. The helper defaults
to Python pipeline mode.

### `Address already in use`

Another Thalamus process is still using ports `50050` or `50051`. Close the old
Thalamus windows or restart Terminal.

### Arrow Keys Do Nothing

Click once inside the subject/stimulus window before pressing the arrow keys.
The keyboard events go to whichever window has focus.

### Queue Is Empty Or Stops Immediately

Make sure the task `Goal` is greater than zero before clicking `Enqueue Task` or
`Enqueue Task Cluster`.
