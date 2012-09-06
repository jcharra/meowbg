
import wx
from meowbg.gui.mainview_glade import MainFrame

app = wx.PySimpleApp(0)
wx.InitAllImageHandlers()
frame_1 = MainFrame(None, -1, "")
app.SetTopWindow(frame_1)
frame_1.Show()
app.MainLoop()