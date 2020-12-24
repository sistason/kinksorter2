# Kinksorter 2

Now comes with a webinterface, which is WIP.

## State

Parts of the webinterface work to be able to build your TargetDirectory from multiple Directories.

Main Workflow:
1. Use `python3 manage.py kink_besteffortsync <from_dir> <to_dir>` to recognize and merge directories together
2. Manually recognize the remaining files in <from_dir> and rename them with a shoot_id.
3. Make repeated runs of (1) or use `python3 manage.py kink_setmovie <path> <shootid>`

Adapt the `src/kinksorter_app/management/commands/kink_besteffortsync.py` to your liking.

Currently, recognizes kink(dot)com-movies by:

- shootid-in-filename
- metadata (set once around 2009 and additionally by kinksorter for easy re-recognition)
- OpenCV in two stages,
  - "check the last 3secs for the _shootid-page_" and if that does not work:
  - "check every 3 seconds in the whole file for the _shootid-page_" (takes excessively more time).
  
With the shootid, the files get sorted into site-subdirectories using a format_string for filenames.
Also, metadata is added to be able to create playlists or copy/link together other structures using
tags, performers or any data.

## Todos

- Webinterface to do that well
- Docker for dependency compartmentalization

(depends on personal user stories)