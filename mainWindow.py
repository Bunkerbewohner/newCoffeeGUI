import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import ImageTk, Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from simpleHash import passHash
from adminWindow import AdminWindow
import fileManager
import delUserWindow
import keyboard
import numPad
import plotter
#TODO: add possibility for usb media backup

########################################################
# Layout and functions for the main window
#
# Coordinates calls to the other modules
########################################################

class MainWindow(tk.Frame):

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master=master
        self.newVal = None
        self.newUser = ""
        self.adminPass = ""
        self.selectedUser=""
        self.memberDict={}
        self.milkDict={}
        self.backupCounter = 0

        self.init_window()

    def init_window(self):
        self.master.title("Main Window")
        screenWidth = self.master.winfo_screenwidth()
        screenHeight = self.master.winfo_screenheight()
        self.master.geometry("{0}x{1}".format(screenWidth, screenHeight))

        canvasWidth = 900
        stdHeight = 60
        stdWidth = 200
        stdFont = "TkDefaultFont"
        userFont = 24
        btnFont = 20

        fileManager.checkConfig()
        self.coffeePrice, self.milkPrice, self.adminHash, isDefault = fileManager.readConfig()
        if isinstance(self.coffeePrice, str):
            self.coffeePrice = int(self.coffeePrice)
        if isinstance(self.milkPrice, str):
            self.milkPrice = int(self.milkPrice)
        if isinstance(self.adminHash, str):
            self.adminHash = int(self.adminHash)

        def addName():
            dialog = keyboard.KeyboardGUI(self, app, "user")
            root.wait_window(dialog)
            if len(self.newUser) > 0:
                updateList(self, self.newUser)
            self.newUser = ""
            fileManager.backup(self.memberDict, self.milkDict)

        def addAmount():
            dialog = numPad.NumPad(self, app, "user")
            root.wait_window(dialog)
            if self.newVal != None:
                updateLabel(self, self.newVal, self.selectedUser)
            self.newVal=None
            self.selectedUser=""
            fileManager.backup(self.memberDict, self.milkDict)

        def drawPlot():
            plotterObject.update_values()
            coffees = plotterObject.coffees
            hours = plotterObject.hours
            plotFigure = plotter.makePlot(coffees, hours)
            barChartCanvas = FigureCanvasTkAgg(plotFigure, master=root)
            barChartCanvas.draw()
            barChartCanvas.get_tk_widget().place(height=figHeightPx, width=figWidthPx, anchor='se', relx=1.0, rely=0.8)

        def getFigWidth():
            figWidthPx = round((screenWidth-canvasWidth)*0.8, 0)
            mmPerPx = self.master.winfo_screenmmwidth()/screenWidth
            inPer_mm = 0.039
            figWidthInches = round(figWidthPx*mmPerPx*inPer_mm, 1)
            return figWidthInches

        def getCanvasX():
            return round((screenWidth-canvasWidth)*0.1, 0)

        def initScrollableCanvas():
            container = ttk.Frame(root)
            canvas = tk.Canvas(container)
            scrollbar = ttk.Scrollbar(container, orient="vertical", command = canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            scrollable_frame.bind(
            "<Configure>",
             lambda e: canvas.configure(
             scrollregion=canvas.bbox("all")))

            canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left",fill="both", expand="True")
            scrollbar.pack(side="right", fill="y")
            upperCorner = getCanvasX()
            container.place(relheight=0.85, width=canvasWidth, anchor="nw", x=upperCorner, y=10)
            return canvas, scrollable_frame, scrollbar

        def initAnimation():
            animationFrames = [tk.PhotoImage(file='coffeeAnimation2.gif', format='gif -index {0}'.format(i)) for i in range(4)]
            animationLabel = tk.Label(root)
            animationLabel.place(height=250, width=200, anchor='ne', relx=1.0, rely=0)
            return animationFrames, animationLabel

        def openAdminWindow():
            isAdmin = checkAdminPassword()
            #isAdmin=True #for testing
            if isAdmin:
                dialog = AdminWindow(self, app)
                root.wait_window(dialog)
                if self.adminPass != "":
                    self.adminHash = passHash(self.adminPass)
                    self.adminPass =""
                fileManager.updateConfig(coffeePrice = self.coffeePrice, milkPrice=self.milkPrice, adminPass=self.adminHash)
            else:
                tk.messagebox.showinfo("Info", "Incorrect password")

        def checkAdminPassword():
            dialog = keyboard.KeyboardGUI(self, app, "admin")
            root.wait_window(dialog)
            isAdmin = (passHash(self.adminPass) == self.adminHash)
            self.adminPass = ""
            return isAdmin

        def buyCoffee(name):
            balance = self.memberDict.get(name)
            milk = self.milkDict.get(name)
            if balance != None:
                balance=balance-self.coffeePrice-self.milkPrice*milk
                self.memberDict[name]=balance
                getattr(self, 'balance_{0}'.format(name)).configure(text='{:.2f}'.format(balance/100))
            self.backupCounter = (self.backupCounter +1)%15
            if self.backupCounter == 0:
                fileManager.backup(self.memberDict, self.milkDict)
            drawPlot()

        def updateMilk(name):
            milkVal = self.milkDict[name]
            newVal = (milkVal+1)%2
            self.milkDict[name]=newVal

        def makeNameLabel(name):
            nameLabel=tk.Label(root, text="")
            nameLabel.configure(text="{0}".format(name), font=(stdFont, userFont))
            return nameLabel

        def makeBalanceLabel(name):
            balanceLabel = tk.Label(root, text="")
            balanceLabel.configure(text='{:.2f}'.format(self.memberDict[name]/100))
            balanceLabel.configure(font=(stdFont, userFont))
            setattr(self, 'balance_{0}'.format(name), balanceLabel)
            return balanceLabel

        def makeMilkCheck(name):
            milkCheck = tk.Checkbutton(root, text="with milk", command=lambda milkName = name: updateMilk(milkName))
            if self.milkDict[name] == 1:
                milkCheck.toggle()
            milkCheck.configure(font=(stdFont, btnFont))
            return milkCheck

        def makeBuyBtn(name):
            buy_btn = tk.Button(root, text="Buy a coffee", command = lambda nameVal = name: buyCoffee(nameVal))
            buy_btn.configure(font=(stdFont, btnFont))
            return buy_btn

        def updateList(self, newName):
            if newName != None:
                self.memberDict[str(newName)]=0
                self.milkDict[str(newName)] = 0
            orderedList=sorted(self.memberDict)
            yOffset=0
            button_x = 600
            canvas.delete("all")
            canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
            for name in orderedList:
                nameLabel = makeNameLabel(name)
                nameLabel_window = canvas.create_window((0, yOffset), anchor="nw", window=nameLabel)
                balanceLabel = makeBalanceLabel(name)
                balance_window = canvas.create_window((2*stdWidth, yOffset), anchor="nw", window=balanceLabel)
                milkCheck = makeMilkCheck(name)
                milkCheck_window = canvas.create_window((button_x, yOffset), anchor="nw", window=milkCheck)
                buy_btn = makeBuyBtn(name)
                buy_btn_window = canvas.create_window((button_x, yOffset+stdHeight), anchor="nw", window=buy_btn)
                if yOffset !=0:
                    lineY = yOffset - 10
                    canvas.create_line(0, lineY, 800, lineY, fill="blue")
                yOffset+=2*stdHeight
            canvas.configure(yscrollcommand=scrollbar.set)

        def updateLabel(self, amount, name):
            balance = self.memberDict.get(name)
            if balance != None:
                balance += amount
                self.memberDict[name] = balance
                getattr(self, 'balance_{0}'.format(name)).configure(text='{:.2f}'.format(balance/100))

        def removeUser():
            if len(self.memberDict) == 0:
                msg = "No users to remove!"
                tk.messagebox.showinfo("Error!", msg)
            else:
                dialog = delUserWindow.DelUserWindow(self, app)
                root.wait_window(dialog)
                if len(self.selectedUser) != 0:
                    del self.memberDict[self.selectedUser]
                    updateList(self, None)
                    self.selectedUser=""

        def animate(index):
            index = index%4
            frame = animationFrames[index]
            animationLabel.configure(image=frame)
            root.after(200, animate, index+1)

        def export():
            fileManager.export(self.memberDict, self.milkDict)
            root.destroy()

        figWidth = getFigWidth()
        figHeight = round(figWidth/1.6, 1)
        self.plotFigure = Figure(figsize=(figWidth,figHeight))
        plotterObject = plotter.Plotter()
        coffees = plotterObject.coffees
        hours = plotterObject.hours
        plotFigure = plotter.makePlot(coffees, hours)
        barChartCanvas = FigureCanvasTkAgg(plotFigure, master=root)
        barChartCanvas.draw()
        figWidthPx = round((screenWidth-canvasWidth)*0.8, 1)
        figHeightPx = round((figWidthPx/1.6), 1)
        barChartCanvas.get_tk_widget().place(height=figHeightPx, width=figWidthPx, anchor='se', relx=1.0, rely=0.8)


        canvas, scrollable_frame, scrollbar = initScrollableCanvas()
        animationFrames, animationLabel = initAnimation()

        nameBtn = tk.Button(root, text="Add User", command=addName)
        nameBtn.configure(font=(stdFont, btnFont))
        nameBtn.place(height=stdHeight, width=stdWidth, anchor="sw", x=10, rely=0.98)

        removeBtn = tk.Button(root, text="Remove User", command=removeUser)
        removeBtn.configure(font=(stdFont, btnFont))
        removeBtn.place(height=stdHeight, width=stdWidth, anchor="sw", x=stdWidth+40, rely=0.98)

        paymentBtn = tk.Button(root, text="Make Payment", command=addAmount)
        paymentBtn.configure(font=(stdFont, btnFont))
        paymentBtn.place(height=stdHeight, width=stdWidth+20, anchor = "sw", x=2*stdWidth+70, rely=0.98)

        adminBtn = tk.Button(root, text="Admin...", command=openAdminWindow)
        adminBtn.configure(font=(stdFont, btnFont))
        adminBtn.place(height=stdHeight, width=stdWidth, anchor="se", relx=0.98, rely =0.98 )

        try:
            self.memberDict, self.milkDict = fileManager.openList()
            updateList(self, None)
        except IOError as e:
            tk.messagebox.showinfo("Warning", "Did not find list to read from")
            self.memberDict = {}
            self.milkDict= {}

        if isDefault:
            msg = "Welcome to the coffee list! You are currently using the default admin password 'coffeeTime!'. \nYou can change the password in the 'Admin' dialog."
            tk.messagebox.showinfo("Info", msg)

        root.after(200, animate, 0)
        root.protocol("WM_DELETE_WINDOW", export)


if __name__ == '__main__':
    root = tk.Tk()
    app = MainWindow(master=root)
    root.mainloop()
