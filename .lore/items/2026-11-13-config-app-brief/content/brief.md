let's move firmware-approaches into it's own custom-firmware thread.  for the moment we will accept using the factory firmware led modes and continue with the app creation.  tie or drop the rgb feedback stitches as required.


i now want to look at flesh out a configuration app.  keys and encoder presses can be set to one of the following: 

## LAYER SELECT (ie bank)
  - set layer (n)
  - inc layer
  - dec layer

Any press set to change layer becomes global (ie it does not change when the layer changes)


## EVENT
  - layer (n or global)
  - MIDI channel
  one of the following: 
    - MIDI momentary or latch
    - CC momentary (low and high value with easing)
    - CC set value
    - CC inc or dec with easing


The edit page should have a layer selection tab or drop down so layers can be edited and viewed as a whole.

we also want to select the rgb mode from the factory firmware. and have an orientation selector.

we can use the glra-studio as a starting point.  references are things like Novation's configuration software or any other popular MIDI hardware configuration tools.

let's refactor the loom to build this.  osc and midi feedback can be moved to a back-log thread and can be set to wait on custom-firmware.  




flesh the loom out so that an opus agent can work through it autonomously, acting as an orchestrator (workflow example in the qtable repo peer to this repo)
