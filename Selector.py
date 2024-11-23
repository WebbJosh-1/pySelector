from PyQt6.QtWidgets import QLabel,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QComboBox,QMainWindow,QPushButton,QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import datetime
import yaml
import csv
import sys, os

class LabelledComboBox(QWidget):   #combines a label and combobox
    def __init__(self, cfg, label,Parts):
        QWidget.__init__(self)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.cfg=cfg
        self.Parts=Parts
        self.RunTimeMin=0
        
        self.label = QLabel()
        self.label.setText(label)
        #self.label.setFixedWidth(200)
        font=QFont()
        font.setBold(True)
        self.label.setFont(font)
        layout.addWidget(self.label)
        
        self.combo= QComboBox(self)
        #self.combo.setFixedWidth(200)
        self.combo.addItems(cfg['Options'])
        self.combo.currentTextChanged.connect(self.update_runtime)
        layout.addWidget(self.combo)
        

        self.RuntimeLabel= QLabel()
        self.update_runtime()
        #self.label.setFixedWidth(200)
        #self.label.setFont(QFont("Arial"))
        layout.addWidget(self.RuntimeLabel)  

        layout.addStretch()     

    def update_runtime(self):
        self.RunTimeMin=self.Parts[self.combo.currentText()]['Runtime']
        self.RuntimeLabel.setText('Runtime: '+str(min_to_hhmm(self.RunTimeMin)))

def get_path_from_exe(relative_path):
    if getattr(sys, 'frozen', False):
        # If the script is frozen (packaged by PyInstaller)
        base_path= os.path.dirname(sys.executable)
    else:
        # If the script is running as a normal Python script
        base_path= os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)   

def min_to_hhmm(min):
    hours = min // 60
    minutes = min % 60
    return f"{hours:02}:{minutes:02}"

class MainWindow(QMainWindow):
    def __init__(self,*args, **kwargs):
        super(MainWindow,self).__init__(*args, **kwargs)
        self.cfg=self.cfg_load()
        self.timer = QTimer()
        self.timer.start(1000)
        self.ui_setup()
        self.csv_load()

        self.totalruntime=0

     
    def ui_setup(self): #sets up UI objects
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowStaysOnTopHint ) #Sets windows option : hides all then adds title bar
        self.setWindowTitle(self.cfg['GUI']['Title'])  #Sets Window Title
        centralWidget=QWidget()
        self.setCentralWidget(centralWidget) 

        #Sets vlayout as main window widget
        vlayout=QVBoxLayout()
        centralWidget.setLayout(vlayout)
        
        #Create Grid widget for selectors
        grid = QGridLayout()
        
        #Create selector widgets and add to grid
        self.selectors=[]
        for key,data in self.cfg['Selectors'].items():  #for every selector defined in cfg add lablledcombo
            cb = LabelledComboBox(data, key, self.cfg['Parts'])  
            grid.addWidget(cb, data['RowLoc'],data['ColumnLoc'])
            self.selectors.append(cb)
        vlayout.addLayout(grid) #Add grid to vlayout

        #Layout Bottom Items
        hlayout=QHBoxLayout()

        #Save Push Button
        button = QPushButton("Save && Close")  
        button.pressed.connect(self.csv_save) #Connect button to Save method
        button.setFixedSize(120, 40)
        hlayout.addWidget(button) # add button to vlayout


        vlayout2=QVBoxLayout()
        self.TotalRuntime= QLabel()
        self.timer.timeout.connect(self.update_total_runtime)
        vlayout2.addWidget(self.TotalRuntime)

        self.EstCompletion= QLabel()
        self.timer.timeout.connect(self.update_est_completion)
        vlayout2.addWidget(self.EstCompletion)

        hlayout.addLayout(vlayout2)
        hlayout.addStretch()

        vlayout.addLayout(hlayout)

    #loads config data from yaml
    def cfg_load(self): 
        file='config.yml'
        path=get_path_from_exe(file)
        try:
            with open(path, 'rb') as f:
                self.cfg=((yaml.safe_load(f))) 
            return self.cfg
        except:
            raise TypeError("Cant find config file at: ",os.path.abspath(file))
        
    #sves selections to csv
    def csv_save(self):
        file='output.csv'
        path=get_path_from_exe(file)
        with open(path,'w',newline='') as f:
            csvFile = csv.writer(f)
            for selector in self.selectors:
                csvFile.writerow( (selector.label.text(),selector.combo.currentText()))
        app.quit() #Quit after save

    #loads selections from csv
    def csv_load(self):
        try:
            file='output.csv'
            path=get_path_from_exe(file)
            with open(path, mode ='r')as f:
                csvFile = csv.reader(f)

                #Create dict from csv
                csvDict={}
                for lines in csvFile: 
                    csvDict[lines[0]]=lines[1]

                #Set selector options from csv
                for selector in self.selectors:
                    if selector.label.text() in csvDict.keys(): #Check if selector widget matches any name from the csv
                        if csvDict[selector.label.text()] in [selector.combo.itemText(i) for i in range(selector.combo.count())]: #confirm csv option is a valid option for selector
                            selector.combo.setCurrentText(csvDict[selector.label.text()])  #set selector option to csv option
        except:
            pass     



    def update_total_runtime(self):
        self.totalruntime=0
        for selector in self.selectors:
            self.totalruntime+=selector.RunTimeMin
        self.TotalRuntime.setText('Total Runtime (HH:MM): '+min_to_hhmm(self.totalruntime))

    def update_est_completion(self):
        finish = datetime.datetime.now()+datetime.timedelta(minutes=self.totalruntime)
        self.EstCompletion.setText('Est. Completion: '+str(finish.strftime("%a %I:%M %p")))
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())