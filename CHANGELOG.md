## Changelog:


0.7.1

- keymap: added 'B' to valid an onion peel transform

0.7.0

- UI: add draw handler with screen framing and helper text displayed
- meta: removing stable beta warning

0.6.9

- fix: prevent edit of a hided peel

0.6.8

- feat: Center pivot when moving out of peg (dev branch merged)
- code: changelog file

0.6.7

- fixes

0.6.6

- feat-wip: peel editing set origin to geometry
    - easier rotation and scale
    - break the re-edit process, need a fix

0.6.5

- fix: crash on edit > scrub > undo. assigning an empty gp data and deleting old ones early in the update seem to prevent unreferenced pointer.
- ux: prevent custom transform if onion peel is disabled
- ux: authorize mouse scroll in custom transform
- code: cleaning and removed unused file

0.6.4

- fix: errors with on save transfo save
- rollback to previous refresh method: (crash still occur on edit + ctrl+Z)

0.6.3

- fix: Add clean at update start, fix a crash (editing stroke > change frame > using ctrl-Z)
- fix: problem when saving with custom transfo
- code: removed useless eval for custom transform matrix apply

0.6.1

- feat: shift+X to flip top bottom in custom transformation

0.6.0

- pref: added addon preferences
    - ui: Depth offset properties is now in addon preferences
    - feat: Default onion peel color can be set at file opening if toggled on in preferences

- feat: Button to toggle the whole x-ray on or off (both object and peels)
- feat: Tell if a peel is empty when trying to transform (out of the keyframe range so not displayed)
- fix: unlock middle-mouse during transform modal


0.5.4

- feat: Modal during peel transform to prevent user from making mistake

0.5.3

- feat: added option to re-edit the custom transformation
- fix: don't erase peel tranform on save (super quick value store/restore)


0.5.2

- feat: add keytype filtering
- feat: onion is deleted on save
    - current limitation: for now this cancel custom peel transformations of all objects

- change : All peel go in from by default to be always visible (still, not synced with main object)
- fix: add undo steps when going back from/reseting custom transform
- fix: GP sometimes not showing up


0.5.1

- fix: a little bug in the matrix
- tried to add a custom "Origin to Geometry" offset on custom tranform but rotation breaks

0.5.0

- method change:
    - instead of copying the data (linked or not) create new data per peel and copy over only needed frame (lighter and more reliable)
    - use plain object and tweak layer settings directely instead of the time/tint/opacity modifiers
    - works in edit mode refresh (was problematic with previous version)
    - first completely usable version in any mode (edit and sculpt) 
- fix: now scale according to offset when peel going further away from camera
- fix: consider othor mode

0.4.7

- fix: layer order dependent onion display in world space (now consider only closest frame)
- fix: onion delete bug

0.4.6

- add properties to adjust distance (fix opacity)

0.4.5

- Big change: Try a version using data-copy to allow permanent drawing of onion skin
    - Still very fast to compute, but this double the object size in blend ince datablock is duplicated
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