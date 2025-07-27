# General Information

- Use PyAutoGui for most inputs
- Cell = Grid cell (96, 64) for example
- Most cells given will be a point within a larger button

## Buttons

### Button States

- Default = the color in which the button is when it's just sitting there waiting to be pressed
- Focus = the color when the mouse is hovering over the button
- Inactive = The color when the user cannot interact with the button, whether from recent use or it isn't unlocked from incomplete steps

### Red Button

- Default: #c72315
- Focus: #fb2412
- Inactive: #391714

### Blue Button

- Default: #1557c7
- Focus: #1268fb
- Inactive: #142239

### Green Button

- Default: #11a228
- Focus: #0fcc2d
- Inactive: #102e16

### Yellow Button

- Default: #f29700
- Focus: #c67d00
- Inactive: #3c2708

# Tier 1

## Iron Mine

4 red buttons to be pressed when active

```
miners:
  miner1 = (32,33)
  miner2 = (33,99)
  miner3 = (155,24)
  miner4 = (158,98)
```

**Loop**:

```
while {args}:
  for miner in miners:
    if miner active
      CLICK miner
  sleep: 0.1s
```

## Iron Smelter

Click red Load button until full, then click red Smelt button

```
timer = true
load = (104,32)
smelt = (122,98)
```

**Loop**

```
while {running}:
  if load_button active
    click load_button
    sleep 50ms
    if load_button active
      if smelt_button active
        click smelt_button
        wait 50ms
        if smelt_button active
          print "Button behavior suggests storage is full. Stopping."
          break
      else
        print "Likely on wrong frame. Stopping."
        break
    else
      sleep 100
```

## Widget Factory

Singular blue button to be continually pressed

```
create = (94,68)
```

**Loop**

```
if create not blue
  break
if create not blue.inactive
  left click create
sleep: 0.5s
```
