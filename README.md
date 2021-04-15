# GP Onion Peel

Blender grease pencil addon to add a custom onion skinning

/!\ Beta version

**[Download latest](https://github.com/Pullusb/GP_onion_peel/archive/main.zip)**

<!-- ### [Demo Youtube]() -->

---  

## Description

Generate onion skin as individual `.peel` objects in a `.onion_peels` subcollection.
Those objects are used as onion skinning and can be manipulated to check objects
### Where ?

`Sidebar` > `Gpencil` Tab > `Onion Peel` Panel

---

<!--
## TODO:
- refresh choices (now refresh only current):
    - Add choice to refresh all
- chose with key placement to use (closest to current frame ? active layer ? both ?)

Bonus:
- Filter by key type (EZ... I think)
- Direct frame offset mode (instead of key offset), might not be usefull at all...

-->

## Changelog:

0.4.5

- Test change: Try a version using data-copy to allow permanent drawing of onion skin
- code: cleanup

0.4.4

- fix: Problems with matrix position

0.4.3

- fix: corrected the update methods
    - check layer frames and store in a separate loop
    - loop only once in onion peels

- fix: bad matrix offset

0.4.2

- fix: Hide other onion than active object
- feat: before/after color are now properties and refresh dynamically
- pref: Worldspace off by defaut

0.4.1

- feat: added flix X/Y with native transform ops in peel transform mode 

0.4.0

- feat: world mode support
    - using frame set, can be long on big scene
    - added option to use only local space

- feat: avoid overlap
    - Objects are placed superslighly behind main one according to active camera
    - note: maybe add the same when in free_navigation viewport later.

- feat: custom transform with differential position store on object prop
    - select the peel in object mode directly to transform
    - added a flip X button 

- UI and bug-fixes


0.3.3

- Better property organisation (Tx to Christophe Seux)

0.3.1

- code: cleanup
- interface for peel custom transform (wip)

0.3.0

- first basic working version with local transform only

0.2.0

- changed UI system
- renamed 'Onion peel' to avoid confusion with andarta Onion skin addon (almost became Shallot skin)

0.1.0:

- initial commit