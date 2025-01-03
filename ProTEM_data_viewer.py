import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from matplotlib.figure import Figure

import ntpath
try:
    from Tkinter import *
    import ttk
    from tkFileDialog import askopenfilename, asksaveasfilename
    import tkMessageBox
except ImportError:
    from tkinter import *
    from tkinter import ttk
    from tkinter.filedialog import askopenfilename, asksaveasfilename
    from tkinter import messagebox as tkMessageBox


root=Tk()

global Stations, lineNum, fileList
global app, Recs
Stations = []
Recs = []
AvgStat = []
AvgRecs = []
fileList = []


class Window(Frame):
  def __init__(self, parent):
        parent.geometry("1200x500+0+0")
        parent.resizable(0, 0)

        Frame.__init__(self, parent)
        self.parent = parent

        self.initUI()

  def initUI(self):
        self.parent.title("ProTEM Data Viewer")
        self.style = ttk.Style()
        self.style.theme_use("default")

# Top Menu
        menubar = Menu(root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Import Gx7",
                             command=lambda: self.readGx7())
        filemenu.add_command(label="Load State",
                             command=lambda: self.loadState())
        filemenu.add_command(label="Save State",
                             command=lambda: self.saveState())
        filemenu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        mathmenu = Menu(menubar, tearoff=0)
        mathmenu.add_command(label='Average Selection',
                             command=lambda: self.averageSelection())
        menubar.add_cascade(label="Math", menu=mathmenu)

        exportmenu = Menu(menubar, tearoff=0)
        exportmenu.add_command(label='Export Selection',
                               command=lambda: self.writeData())
        menubar.add_cascade(label="Export", menu=exportmenu)

        root.config(menu=menubar)

# Tree
        self.treeFrame = Frame(self, background='white', relief=RAISED)
        self.treeFrame.grid(column=0, row=0, sticky=N+S+E+W)

        self.tree = ttk.Treeview(self.treeFrame)
        self.tree["columns"] = ("one", "two")
        self.tree.column("one", width=50)
        self.tree.column("two", width=50)
        self.tree.heading("one", text="Freq")
        self.tree.heading("two", text="Gain")
        self.tree.grid(column=0, row=0, sticky='ns')
        self.treeFrame.grid_columnconfigure(0, weight=1)
        self.treeFrame.grid_rowconfigure(0, weight=1)

        self.tree.bind('<BackSpace>', deleteItem)

# Info Frame
        self.infoFrame = Frame(self)
        self.infoFrame.grid(column=1, row=0, sticky=N+S+E+W)

        self.plotFrame = Frame(self)
        self.plotFrame.grid(column=2, row=0, sticky=N+S+E+W)

# Info Frame

        linelbl = Label(self.infoFrame, text="Line #")
        linelbl.grid(row=2, column=0)

        self.lineEntry = Entry(self.infoFrame)
        self.lineEntry.grid(row=3, column=0)

        stationlbl = Label(self.infoFrame, text="Station #")
        stationlbl.grid(row=2, column=1)

        self.stationEntry = Entry(self.infoFrame)
        self.stationEntry.grid(row=3, column=1)

        currentlbl = Label(self.infoFrame, text="Current (A)")
        currentlbl.grid(row=4, column=0)

        self.currentEntry = Entry(self.infoFrame)
        self.currentEntry.grid(row=5, column=0)

        tolbl = Label(self.infoFrame, text="T/O Time")
        tolbl.grid(row=4, column=1)

        self.toEntry = Entry(self.infoFrame)
        self.toEntry.grid(row=5, column=1)

        txSidelbl = Label(self.infoFrame, text="Tx Side Lengths (m)")
        txSidelbl.grid(row=6, column=0)

        self.txSideEntry = Entry(self.infoFrame)
        self.txSideEntry.grid(row=7, column=0)

        rxArealbl = Label(self.infoFrame, text="Rx Area")
        rxArealbl.grid(row=6, column=1)

        self.rxAreaEntry = Entry(self.infoFrame)
        self.rxAreaEntry.grid(row=7, column=1)

        self.updatebtn = Button(self.infoFrame, text="Update Info",
                                comman=lambda: self.saveInfo())
        self.updatebtn.grid(row=10, column=1)
        self.updatebtn.config(state='disabled')

# a tk.DrawingArea
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.a = self.fig.add_subplot(111)
        self.a.plot(0, 0)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plotFrame)
        plot_widget = self.canvas.get_tk_widget()

        toolbar = NavigationToolbar2Tk(self.canvas, self.plotFrame)
        toolbar.update()

        self.canvas._tkcanvas.pack(fill=BOTH, expand=1)

        self.pack(fill=BOTH, expand=1)

  def CloseWindow(self):
        root.quit()
        root.destroy()

  def updateInfo(self):
        foc = self.tree.focus()
        if(len(foc) < 1):
            return
        if(foc[0] == '*'):
            i = Recs.index(foc[1:])
            s = Stations[i]
        elif(foc[0] == '$'):
            i = AvgRecs.index(foc[1:])
            s = AvgStat[i]
        else:
            s = Stations[0]

        self.lineEntry.delete(0, END)
        self.lineEntry.insert(0, str(s.lineNumber))

        self.stationEntry.delete(0, END)
        self.stationEntry.insert(0, str(s.stationNumber))

        self.currentEntry.delete(0, END)
        self.currentEntry.insert(0, str(s.current))

        self.toEntry.delete(0, END)
        self.toEntry.insert(0, str(s.toTime))

        self.txSideEntry.delete(0, END)
        self.txSideEntry.insert(0, str(s.txSides[0])+","+str(s.txSides[1]))

        self.rxAreaEntry.delete(0, END)
        self.rxAreaEntry.insert(0, str(s.rxArea))

  def plotData(self):
        select = self.tree.selection()

        self.fig.clear()
        self.a = self.fig.add_subplot(111)
        for foc in select:
            if(foc[0] == '*'):
                i = Recs.index(foc[1:])
                s = Stations[i]
                self.a.plot(s.plusTimes, s.plusData, 'b+', ms=10)
                self.a.plot(s.minsTimes, s.minsData, 'r_', ms=10)
                ax = self.canvas.figure.axes[0]
                ax.set_yscale('log')
                ax.set_xscale('log')

            if(foc[0] == '$'):
                i = AvgRecs.index(foc[1:])
                s = AvgStat[i]
                ax = self.canvas.figure.axes[0]
                ax.set_yscale('log')
                ax.set_xscale('log')
                xs = np.hstack((s.plusTimes, s.minsTimes))
                ys = np.hstack((s.plusData, s.minsData))
                inds = np.argsort(xs)
                xs = xs[inds]
                ys = ys[inds]

                verr = s.stds
                verr2 = np.array(verr)
                verr2[verr >= ys] = ys[verr >= ys]*.999

                ax.errorbar(xs, ys, yerr=[verr2, verr])
            self.canvas.draw()

  def buildTree(self):
        self.tree.delete(*self.tree.get_children())
        for s in Stations:
            fileID = s.fileName
            lineID = fileID+s.lineNumber
            stationID = lineID+s.stationNumber
            recordID = "*"+s.record+fileID
            if fileID not in self.tree.get_children():
                self.tree.insert("", "end", iid=fileID, text=s.fileName)

            if lineID not in self.tree.get_children(s.fileName):
                self.tree.insert(s.fileName, "end", iid=lineID,
                                 text="Line "+s.lineNumber)

            if stationID not in self.tree.get_children(lineID):
                self.tree.insert(lineID, "end", iid=stationID,
                                 text=s.stationNumber)

            self.tree.insert(stationID,"end",iid=recordID,
                             text="Record "+s.record,
                             values=(s.freq,str(s.gain)))

        if(len(AvgStat)>0):
            self.tree.insert("","end",iid='AVGS',text='Averaged values')
            for s in AvgStat:
                fileID="AVGS"
                lineID=fileID+s.lineNumber
                stationID=lineID+s.stationNumber
                recordID="$"+s.record
                if not fileID in self.tree.get_children():
                  self.tree.insert("","end",iid=fileID,text=s.fileName)

                if not lineID in self.tree.get_children(s.fileName):
                  self.tree.insert(s.fileName,"end",iid=lineID,
                    text="Line "+s.lineNumber)

                if not stationID in self.tree.get_children(lineID):
                  self.tree.insert(lineID,"end",iid=stationID,
                    text=s.stationNumber)

                self.tree.insert(stationID,"end",iid=recordID,
                    text=s.record,values=(s.freq,str(s.gain)))

  def moveRecordInTree(self,s,recordID):
    fileID = s.fileName
    lineID = fileID+s.lineNumber
    stationID = lineID+s.stationNumber

    if not lineID in self.tree.get_children(fileID):
      self.tree.insert(fileID,"end",iid=lineID,text="Line "+s.lineNumber)
    if not stationID in self.tree.get_children(lineID):
      self.tree.insert(lineID,"end",iid=stationID,text=s.stationNumber)

    siblings = self.tree.get_children(stationID)

    i=0
    while(siblings[i]<recordID and i<len(siblings)):
      i+=1

    if(i==len(siblings)):
      self.tree.move(recordID,stationID,"end")
    else:
      self.tree.move(recordID,stationID,self.tree.index(siblings[i]))

  def averageSelection(self):
    global AvgStat,AvgRecs
    t=Toplevel(self)
    t.wm_title("Average Records")
    t.geometry("350x300+5+5")
    t.resizable(0,0)


    select=self.tree.selection()
    if(len(select)==0):
      l = Label(t,text="Nothing Selected")
      l.grid(column=0,row=0)
    else:
      fileID1=self.tree.parent(
          self.tree.parent(
            self.tree.parent(select[0])))
      fileID2=self.tree.parent(
          self.tree.parent(
            self.tree.parent(select[-1])))

      l = Label(t,text="Selection: "+select[0][1:-len(fileID1)]+
          "-"+select[-1][1:-len(fileID2)])
      l.grid(column=0,row=0)

    linelbl = Label(t,text="Line #")
    linelbl.grid(row=2, column=0)
    lineEntry = Entry(t)
    lineEntry.grid(row=3,column=0)
    lineEntry.insert(0, self.lineEntry.get())

    stationlbl = Label(t,text="Station #")
    stationlbl.grid(row=2, column=1)
    stationEntry = Entry(t)
    stationEntry.grid(row=3,column=1)
    stationEntry.insert(0, self.stationEntry.get())

    currentlbl = Label(t,text="Current (A)")
    currentlbl.grid(row=4, column=0)
    currentEntry = Entry(t)
    currentEntry.grid(row=5,column=0)
    currentEntry.insert(0, self.currentEntry.get())

    tolbl = Label(t, text="T/O Time")
    tolbl.grid(row=4, column=1)
    toEntry = Entry(t)
    toEntry.grid(row=5,column=1)
    toEntry.insert(0, self.toEntry.get())

    txSidelbl = Label(t, text="Tx Side Lengths (m)")
    txSidelbl.grid(row=6,column=0)
    txSideEntry = Entry(t)
    txSideEntry.grid(row=7,column=0)
    txSideEntry.insert(0, self.txSideEntry.get())

    rxArealbl = Label(t, text="Rx Area")
    rxArealbl.grid(row=6,column=1)
    rxAreaEntry = Entry(t)
    rxAreaEntry.grid(row=7, column=1)
    rxAreaEntry.insert(0, self.rxAreaEntry.get())

    reclbl = Label(t,text="Record Label")
    reclbl.grid(row=9,column=0)
    recEntry = Entry(t)
    recEntry.grid(row=10,column=0)
    recEntry.insert(0,"Average "+str(len(AvgStat)+1))


    def goAverage():
      fileName="AVGS"
      current=float(currentEntry.get())
      toTime=float(toEntry.get())
      txSidesTemp= self.txSideEntry.get().split(",")
      txSides = [float(txSidesTemp[0]),float(txSidesTemp[1])]
      rxArea = float(rxAreaEntry.get())


      lineN = lineEntry.get()
      stationN = stationEntry.get()
      record = recEntry.get()

      iRec=Recs.index(select[0][1:])
      si = Stations[iRec]
      dat = si.data

      txType=si.txType
      ref = si.ref
      freq = si.freq
      gain = 0.0
      primary = si.primary
      first_gate = si.times[0]

      for i in range(1,len(select)):
        foc=select[i]
        iRec=Recs.index(foc[1:])
        si=Stations[iRec]

        dat = np.vstack((dat,si.data))

      means=sum(dat)/len(select)
      stds =np.sqrt(sum((dat-means)*(dat-means))/len(select))

      s = TEMStation(fileName,current,toTime,
            txSides,rxArea,txType)
      s.setData(gain,lineN,stationN,freq,ref,record,primary,means,
          first_gate=first_gate,rec_voltage=False)
      s.setSTD(stds,rec_voltage=False)
      AvgStat.append(s)
      AvgRecs.append(record)

      fileID="AVGS"
      lineID=fileID+s.lineNumber
      stationID=lineID+s.stationNumber
      recordID="$"+s.record
      if not fileID in self.tree.get_children():
        self.tree.insert("","end",iid=fileID,text="Averages")

      if not lineID in self.tree.get_children(s.fileName):
        self.tree.insert(s.fileName,"end",iid=lineID,
            text="Line "+s.lineNumber)

      if not stationID in self.tree.get_children(lineID):
        self.tree.insert(lineID,"end",iid=stationID,
            text=s.stationNumber)

      self.tree.insert(stationID,"end",iid=recordID,
        text=s.record,values=(s.freq,str(s.gain)))

      t.destroy()


    avgButton = Button(t,text="Average Values",command = goAverage)
    avgButton.grid(row=10,column=1)


  def saveInfo(self):
    select=self.tree.selection()
    for foc in select:
      if(foc[0]=='*'):
        i = Recs.index(foc[1:])
        s = Stations[i]
      elif(foc[0]=='&'):
        i = AvgRecs.index(foc[1:])
        s = AvgStat[i]
      s.lineNumber=self.lineEntry.get()
      s.stationNumber = self.stationEntry.get()
      s.current = float(self.currentEntry.get())
      s.toTime = float(self.toEntry.get())
      txSides= self.txSideEntry.get().split(",")
      s.txSides=[float(txSides[0]), float(txSides[1])]
      s.rxArea= float(self.rxAreaEntry.get())
      s.updateRecV()
      self.moveRecordInTree(s,foc)
    self.updateInfo()

  def writeData(self):
    print("here")
    fname = asksaveasfilename(parent=root)
    if fname:
      print("Writing Out")
    else:
      print("No save file selected")
      return


    f = open(fname,'w')
    select=self.tree.selection()
    for foc in select:
      if(foc[0]=='*' or foc[0]=='$'):
        if(foc[0]=='*'):
          iRec = Recs.index(foc[1:])
          s=Stations[iRec]
        else:
          iRec = AvgRecs.index(foc[1:])
          s=AvgStat[iRec]

        f.write("Record:\t"+s.record+"\n")
        f.write("Line:\t"+s.lineNumber+"\tStation:\t"+s.stationNumber+
            "\tGain:\t"+str(s.gain)+"\n")
        f.write("Frequency:\t"+s.freq+"\tTO Time:\t"+str(s.toTime)+
            "\tTx Current:\t"+str(s.current)+"\n")
        f.write("Rx Area:\t"+str(s.rxArea)+"\tTx Sides:\t"+
            str(s.txSides[0])+","+str(s.txSides[1])+"\n")
        f.write("\n")

        f.write("Gate #\tTime(us)\tRecieved Voltage(nv/m^2/A)")
        if(foc[0]=='$'):
          f.write("\tstd")
        f.write("\n")

        for i in range(len(s.data)):
          f.write(str(i+1)+"\t"+str(s.times[i])+"\t"+str(s.data[i]))
          if(foc[0]=='$'):
            f.write("\t"+str(s.stds[i]))
          f.write("\n")

    f.close()


  def readGx7(self):
    global Stations,Recs
    fname = askopenfilename(defaultextension='.Gx7',parent=root)
    if fname:
      print("reading in Gx7 file: "+fname)
    else:
      print("no file selected")
      return
    f=open(fname)
    fileList.append(fname)
    fileName=ntpath.basename(fname)
    content = f.read().splitlines()
    f.close()
    nlines=len(content)

    cycle_next = False
    for i in range(2,nlines,2):
      if cycle_next:
        cycle_next=False
        continue

      splits = content[i].split()
      if len(splits)==3:
        print("Comment Line Found")
      elif len(splits)==9:
        if splits[3]=="HDR":
          dat=content[i+1].split()
          date = dat[0]
          current = float(dat[4])
          toTime = float(dat[5])
          txSides=[float(dat[6]),float(dat[7])]
          rxArea=float(dat[10])
          txType = "EM"+dat[11]
        elif splits[3]=="OPR":
          station = TEMStation(fileName,current,toTime,
            txSides,rxArea,txType)
          lineN = splits[1]
          stationN = splits[2]
          ref = splits[4]
          freq = splits[5]
          gain = float(splits[6][0])
          record = str(int(splits[8][1:]))
          dat = content[i+1]
          primary = float(dat[0:8])

          if(len(dat.split())==15): #30 gate file
            splits2 = content[i+2].split()
            freq = splits2[5]
            record = record+'+'+str(int(splits2[8][1:]))

            dat2 = content[i+3]
            primary = float(dat[0:8])
            data = np.zeros(30)
            for i in range(10):
              data[i] = float(dat[8*(i+1):8*(i+2)])
            for i in range(20):
              data[10+i] = float(dat2[8*(i+1):8*(i+2)])
            cycle_next = True
            first_gate = float(dat[8*22:8*23])*1000

          else: #20 gate file
            data = np.zeros(20)
            for i in range(20):
              data[i] = float(dat[8*(i+1):8*(i+2)])
            first_gate = float(dat[8*22:8*23])*1000

          Recs.append(record+fileName)
          station.setData(gain,lineN,stationN,freq,ref,record,primary,data,first_gate)
          Stations.append(station)

    self.buildTree()
    self.updatebtn.config(state='normal')

  def saveState(self):
    pass

  def loadState(self):
    pass

  def askDeleteItem(self):
    select = self.tree.selection()
    if tkMessageBox.askokcancel("Remove Selection", "Do you want to delete the selected item[s]?"):
      for foc in select:
        self.tree.delete(foc)

#####END OF CLASS
u20Centers=np.array([6.813,8.688,11.13,14.19,18.07,23.06,29.44,
      37.56,47.94,61.13,77.94,99.38,126.7,166.4,206,262.8,
      335.2,427.7,545.6,695.9])
v20Centers=np.array([35.25,42.75,52.5,64.75,80.25,100.25,125.75,158.25,
      199.75,252.5,319.75,405.5,514.75,654.25,832.25,1059.5,1349.5,
      1719,2190.5,2792])
H20Centers=np.array([88.125,106.875,131.25,161.875,200.625,250.625,
      314.375,395.625,499.375,631.25,799.375,1013.75,1286.875,
      1635.625,2080.625,2648.125,3372.5,4296.875,5475.5,6978.5])
H30Centers=np.array([6.8,9.11,12,15.9,20.8,27,34.8,44.4,56.3,70.3,85.9,
      104.7,129.1,159.7,198.4,248.6,312.3,393.5,497.1,629,797.3,
      1012,1285,1634,2079,2645,3370,4295,5473,6978])
M30Centers=np.array([36,45.25,57,72.25,92,117,148,186.5,234,290,352.5,427.5,
      525,647.5,802.5,1002.5,1257.5,1582.5,1997.5,2525,3197.5,4055,
      5147.5,6542.5,8322.5,10592.5,13490,17187.5,21902.5,27915])
L30Centers=np.array([90,113.125,142.5,180.625,230,292.5,370,466.25,585,
      725,881.25,1068.75,1312.5,1618.75,2006.25,2506.25,3143.75,3956.5,
      4994,6312.5,7995,10139,12869,16355,20805,26481.5,33731.5,42975,
      54755,69780])

class TEMStation(object):
  def __init__(self,fileName,current,toTime,txSides,rxArea,txType):
    self.fileName=fileName
    self.current = current
    self.toTime = toTime
    self.txSides = txSides
    self.rxArea = rxArea
    self.txType = txType

  def setData(self,gain,lineNumber,stationNumber,freq,ref,record,primary,dat,
      first_gate=0.0, rec_voltage=True):
    self.gain = gain
    self.lineNumber = lineNumber
    self.stationNumber = stationNumber
    self.freq = freq
    self.ref = ref
    self.record = record
    self.primary = primary
    self.nGates = len(dat)

    if(self.nGates==20):
      if(self.freq=='u'):
        self.times=u20Centers*1
      elif(self.freq=='v'):
        self.times=v20Centers*1
      elif(self.freq=='H'):
        self.times=H20Centers*1
      elif(self.freq=='M'):
        self.times=v20Centers*10
      elif(self.freq=='L'):
        self.times=H20Centers*10
      elif(self.freq=='K'):
        self.times=v20Centers*100
      elif(self.freq=='J'):
        self.times=H20Centers*100
    else:
      if(self.freq=='H'):
        self.times=H30Centers*1
      elif(self.freq=='M'):
        self.times=M30Centers*1
      elif(self.freq=='L'):
        self.times=L30Centers*1
      elif(self.freq=='K'):
        self.times=M30Centers*10
      elif(self.freq=='J'):
        self.times=L30Centers*10

    shift = first_gate-self.times[0]
    self.times += shift

    if(rec_voltage):
      self.Pdata = dat
      self.updateRecV()
    else:
      self.data = dat
      self.update_plus_minus()

  def update_plus_minus(self):
    self.plusData=[]
    self.plusTimes=[]
    self.minsData=[]
    self.minsTimes=[]
    for i in range(self.nGates):
      if(self.data[i]>0):
        self.plusData.append(self.data[i])
        self.plusTimes.append(self.times[i])
      elif(self.data[i]<0):
        self.minsData.append(-self.data[i])
        self.minsTimes.append(self.times[i])


  def updateRecV(self):
    self.data=self.protemVToRecV(self.Pdata)
    try:
      self.stds=self.protemVToRecV(self.Pstds)
    except:
      pass
    self.update_plus_minus()

  def protemVToRecV(self,Pdata):
    data = Pdata/(np.power(2, self.gain)*self.current*self.rxArea)*19.2*1000
    if(self.txType=='EM47'):
      data = data/51.2 #Gain of preAmp
      pass
    return data

  def recVToRhoA(self,data):
    pass

  def setSTD(self,stds,rec_voltage=True):
    if(rec_voltage):
      self.Pstds = stds
      self.stds = self.protemVToRecV(stds)
    else:
      self.stds = stds

  def getData(self):
    return self.data


def main():
    global app
    app = Window(root)
    root.bind('<<TreeviewSelect>>',TreeSelect)
    root.protocol('WM_DELETE_WINDOW', windowClose)  # root is your root window

    root.lift()
    while True:
        try:
            root.mainloop()
            break
        except UnicodeDecodeError:
            pass

def TreeSelect(event):
  foc=app.tree.focus()
  if(foc[0]=='*' or foc[0]=='$'):
    app.plotData()
    app.updateInfo()

def deleteItem(event):
  app.askDeleteItem()

def windowClose():
    root.quit()
    root.destroy()

if __name__ == '__main__':
  main()
