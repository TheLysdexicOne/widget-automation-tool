from tkinter import Tk, Button, Frame, messagebox
import json
import mouse_control
import game_logic

class MinigameMenu:
    def __init__(self, master):
        self.master = master
        self.master.title("Minigame Selection Menu")
        self.frame = Frame(self.master)
        self.frame.pack()

        self.load_minigames()

        self.buttons = {}
        for minigame in self.minigames:
            self.buttons[minigame] = Button(self.frame, text=minigame, command=lambda mg=minigame: self.start_minigame(mg))
            self.buttons[minigame].pack(pady=5)

        self.escape_button = Button(self.frame, text="Escape", command=self.exit_menu)
        self.escape_button.pack(pady=20)

    def load_minigames(self):
        with open('config/minigames.json') as f:
            self.minigames = json.load(f)

    def start_minigame(self, minigame):
        try:
            action = self.minigames[minigame]['action']
            # Here you would call the function to start the minigame using mouse_control
            mouse_control.perform_action(action)
            messagebox.showinfo("Minigame Started", f"Starting {minigame}...")
        except KeyError:
            messagebox.showerror("Error", "Minigame action not found.")

    def exit_menu(self):
        self.master.quit()

if __name__ == "__main__":
    root = Tk()
    menu = MinigameMenu(root)
    root.mainloop()