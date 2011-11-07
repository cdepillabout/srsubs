#!/usr/bin/python2
import pysrt


#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
from PyQt4 import QtCore, QtGui
from IPython import embed
import sys, os, atexit

my_array = [['00','01','02'],
            ['10','11','12'],
            ['20','21','22']]

def main():
    subs = pysrt.SubRipFile.open('./Real_Clothes_ep09_(1280x720_DivX6).jp.srt')
    app = QtGui.QApplication(sys.argv)
    w = SubTitleSelector(subs)
    w.show()
    sys.exit(app.exec_())

class MPlayerWidget(QtGui.QWidget):

    """
    CMD = "mplayer -slave -quiet -noconsolecontrols -nomouseinput -vo %(VO)s -ao %(AO)s -wid %(WID)s %(FILENAME)r"

    CFG = dict(
        AO = "alsa",
        VO = "xv" #VO = "x11"
    )
    """
    CMD = "mplayer -x %(WIDTH)s -y %(HEIGHT)s -nosub -noautosub -slave -really-quiet -noconsolecontrols -nomouseinput -vo %(VO)s -wid %(WID)s -ss %(STARTHOURS)s:%(STARTMINS)s:%(STARTSECS)s.%(STARTMILLIS)s -endpos %(ENDHOURS)s:%(ENDMINS)s:%(ENDSECS)s.%(ENDMILLIS)s %(FILENAME)r"

    CFG = dict(
        VO = "x11", #VO = "x11",
        WIDTH = 400,
        HEIGHT = 250,
        STARTHOURS = 0,
        STARTMINS = 0,
        STARTSECS = 0,
        STARTMILLIS = 0,
        ENDHOURS = 999999,
        ENDMINS = 0,
        ENDSECS = 0,
        ENDMILLIS = 0,
    )

    #-endpos <[[hh:]mm:]ss[.ms]|size[b|kb|mb]> (also see -ss and -sb)
    #-ss 


    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.parent = parent
        self.process = None
        self.layout = QtGui.QVBoxLayout(self)

        self.view = QtGui.QLabel(self)
        self.view.setMinimumSize(self.CFG["WIDTH"], self.CFG["HEIGHT"])
        self.layout.addWidget(self.view)

    def start(self, filename, start, length):
        self.pause_flag = False
        self.fullscreen_flag = False
        self.show()
        #self.view.setText("Loading %s..." % filename)
        #QtGui.qApp.processEvents()

        self.CFG["STARTHOURS"] = start.hours
        self.CFG["STARTMINS"] = start.minutes
        self.CFG["STARTSECS"] = start.seconds
        self.CFG["STARTMILLIS"] = start.milliseconds

        self.CFG["ENDHOURS"] = length.hours
        self.CFG["ENDMINS"] = length.minutes
        self.CFG["ENDSECS"] = length.seconds
        self.CFG["ENDMILLIS"] = length.milliseconds

        self.CFG["WID"] = self.view.winId()
        #self.CFG["WID"] = self.parent.winId()
        self.CFG["FILENAME"] = filename
        print("cmd: %s" % (self.CMD % self.CFG))
        self.process = os.popen(self.CMD % self.CFG, "w", 1)

        atexit.register(self.exit)

    def play(self, filename, start, length):
        if self.process:
            self("quit")
            self.process.close()

        self.start(filename, start, length)

    def exit(self):
        if self.process:
            self("pause")
            self("quit 0")
            self.process.close()
            self.process = None
        self.close()

    def __call__(self, cmd):
        if self.process:
            print "*", cmd
            self.process.write("\n%s\n" % cmd)

    def __del__(self):
        self.exit()

    def load(self, url):
        self.CFG["FILENAME"] = url
        self("loadfile %s" % url)


class SubTitleSelector(QtGui.QWidget):
    def __init__(self, subs):
        super(SubTitleSelector, self).__init__()
        self.resize(850, 450)
        self.centerOnScreen()
        self.setWindowTitle('Subtitle Selector')

        self.subs = subs

        self.filename = sys.argv[1]

        # table
        self.tablemodel = SubsTableModel(subs, self)
        self.tableview = QtGui.QTableView()
        self.tableview.setModel(self.tablemodel)
        QtCore.QObject.connect(self.tableview,
                QtCore.SIGNAL("clicked(const QModelIndex&)"), self.tablemodel.play_video)


        # mplayer
        self.mplayerview = MPlayerWidget(self)
        #mplayerview.play(sys.argv[1])

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.tableview)
        layout.addWidget(self.mplayerview)
        self.setLayout(layout)

    def play_video(self, start, length):
        self.mplayerview.play(self.filename, start, length)

    def centerOnScreen (self):
        "Centers the window on the screen the current mouse is on."

        # loop through the screens, trying to figure out
        # what screen the mouse is in
        desktop = QtGui.QDesktopWidget()
        mousepos = QtGui.QCursor().pos()
        mousescreen = 0
        for i in range(desktop.screenCount()):
            screensize = desktop.availableGeometry(i)
            if screensize.contains(mousepos):
                mousescreen = i
                break

        resolution = QtGui.QDesktopWidget().screenGeometry(mousescreen)

        half_width = (resolution.width() / 2) - (self.frameSize().width() / 2)
        half_height = (resolution.height() / 2) - (self.frameSize().height() / 2)
        self.move(resolution.left() + half_width, resolution.top() + half_height)

class SubsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, datain, parent=None):
        super(SubsTableModel, self).__init__(parent)
        self.arraydata = datain
        self.parent = parent

        self.TIME_START_COLUMN = 0
        self.TIME_END_COLUMN = 1
        self.SUB_COLUMN = 2

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if index.column() == self.SUB_COLUMN:
            return self.arraydata[index.row()].text
        elif index.column() == self.TIME_START_COLUMN:
            time = self.arraydata[index.row()].start
            startstr = "%02d:%02d:%02d,%03d" % \
                    (time.hours, time.minutes, time.seconds, time.milliseconds)
            return startstr
        elif index.column() == self.TIME_END_COLUMN:
            time = self.arraydata[index.row()].end
            endtime = "%02d:%02d:%02d,%03d" % \
                    (time.hours, time.minutes, time.seconds, time.milliseconds)
            return endtime
        else:
            sys.stderr.write("ERROR! None of the other columns matched!")
            sys.exit(1)

    def play_video(self, index):
        row = index.row()
        item = self.arraydata[row]
        starttime = item.start
        endtime = item.end

        self.parent.play_video(starttime, endtime - starttime)


if __name__ == "__main__":
    main()
