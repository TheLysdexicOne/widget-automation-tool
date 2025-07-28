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
  miner1 = (32,33, red)
  miner2 = (33,99, red)
  miner3 = (155,24, red)
  miner4 = (158,98, red)
```

**Loop**:

```py
while {args}:
  for miner in miners:
    if miner is ACTIVE
      click(miner)
      sleep 100ms
      if miner is ACTIVE
        failed +=1
  # Storage Full Behavior
  if failed >= 4:
    break
  sleep 100ms
```

## Iron Smelter

Click red Load button until full, then click red Smelt button

```
timer = true
load = (104,32, red)
smelt = (122,98, red)
```

**Loop**

```py
while {args}:
  if load is ACTIVE
    click(load)
    sleep 50ms
    if load_button is INACTIVE
      while load_button is INACTIVE
        sleep 100ms
    else
        click(smelt)
        sleep 50ms
        if smelt_button is ACTIVE
          break
```

## Widget Factory

Singular blue button to be continually pressed

```
create = (94,68, blue)
```

**Loop**

```py
if create is ACTIVE
  click(create)
sleep 50ms
```

86, 79
88, 79

# Tier 2

## Sand Pit

Click button while active

```
excavate = (144, 44, red)
```

**Loop**

```py
if excavate is active
  click excavate
  sleep 50ms
  # Storage Full Behavior
  if excavate is active
    break
```
