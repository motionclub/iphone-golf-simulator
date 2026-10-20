# Task 28 rollback inventory

Production runtime code was never modified by this task. HeroTennisDriver.cs, TennisActor.cs and TennisServeRoutine.cs are original task-start backups. The runtime candidate exists only in CandidateClone and as a rejected review patch.

The only new production files are Unity/Assets/Editor/ServeWalkFilm.cs and its Unity-generated .meta. Their .ABSENT markers record that they did not exist before the task. Removing just these two new files rolls back this task's production change.

This repository has concurrent unrelated changes. Compare any file with its backup before restoring it; do not overwrite newer work from another task.

Before and candidate clones retain the protected assets used for the films. Analysis/tool revision backups and the initial reproduction report are also preserved here. No commit was made.
