info = {
    "id": "4.3",
    "name": "Plastic Extractor",
    "item": "Plastic",
    "automation": {"can_automate": 1, "programmed": 1},
    "buttons": {"extract": [-612, 648, "red"], "pressurize": [-601, 937, "blue"]},
    "interactions": {"box": [-922, 595]},
    "colors": {
        "empty_color": [17, 11, 37],
        "fill_color1": [72, 237, 56],
        "fill_color2": [23, 97, 19],
        "fill_color3": [45, 175, 37],
    },
}


extract = self.create_button("extract")
pressurize = self.create_button("pressurize")

self.x = self.frame_data["interactions"]["box"]
colors = self.frame_data["colors"]

self.pixel_top_xy = grid_to_screen_coords(*self.grid_top)
fail = 0
while self.should_continue:
    if time.time() - start_time > self.max_run_time:
        break

    pixel_color = pyautogui.pixel(self.pixel_top_xy[0], self.pixel_top_xy[1])
    if pixel_color != self.fill_color:
        for _ in range(7):
            pressurize.click()
    elif pixel_color == self.fill_color:
        extract.click()
        self.sleep(0.1)
        if extract.active():
            fail += 1
        while extract.inactive():
            if not self.sleep(1):
                break
    if fail > 3:
        self.log_storage_error()
    if not self.sleep(0.05):
        break
