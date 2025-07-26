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
for miner in miners:
  if miner not red
    break
  if miner not red.inactive - left click miner
sleep: 0.1s
```

## Iron Smelter

Click red Load button until full, then click red Smelt button

```
load = (104,32)
smelt = (122,98)
```

**Loop**

```
if load not red
  break
if load not red.inactive
  left click load
  wait 50ms
  if load not red.inactive - if smelt not red - break - click smelt - wait until smelt not red.inactive
sleep: 0s
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
