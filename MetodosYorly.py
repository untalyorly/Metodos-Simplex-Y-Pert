import sys, re, os, string, re
from PyQt5.QtWidgets import *
from PyQt5 import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
import numpy as np
from datetime import date, datetime, timedelta

#from src.Perl import Perl
from src.view.principal import Ui_Principal
from src.view.fecha import Ui_Dialog
from src.view.ventana2 import Ui_ventana2

try:
    from pandas import DataFrame
    pandas_av = True
except ImportError:
    pandas_av = False
    pass

class MainWindow(QMainWindow):
    # Constructor
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_Principal()
        self.ui.setupUi(self)
        self.perl = Perl(self.ui)
  
        # Eventos
        self.ui.actionSimplex.triggered.connect(self.showSimplexUI)
        self.ui.actionPerl.triggered.connect(self.showPerlUI)

    # Método: Muestra la interfaz del método simplex  
    def showSimplexUI(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageSimplex)
        self.perl = Simplex(self.ui)
    
    # Método: Muestra la interfaz del modelo de redes
    def showPerlUI(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.pagePerl)
        self.perl = Perl(self.ui)
        
######
######
##          PERL
       
class Perl(QMainWindow):

    #Método constructor de la clase
    def __init__(self, ui):
         super(Perl, self).__init__()
         self.ui = ui
 
         self.ui.btnGenera.clicked.connect(self.genera)
         self.ui.btnNuevo.clicked.connect(self.limpia)
         self.ui.btnCalcular.clicked.connect(self.calculo)
         self.ui.btnCalcular.setEnabled(False)

         # Atributos
         self.fechInicio = ""
         #+establecer el ancho de columnas
         for indice, ancho in enumerate((60, 100, 80, 30, 30, 30), start=0):
             self.ui.tabla.setColumnWidth(indice, ancho)
         
         for indice, ancho in enumerate((35, 35, 30, 30, 30, 30, 30,30, 125,110,120,100), start=0):
             self.ui.tablaView.setColumnWidth(indice, ancho)
         #self.ui.tablaView.horizontalHeader(columns)
         self.ui.tablaView.setEditTriggers(QAbstractItemView.NoEditTriggers)
    
    #generamos la tabla 
    def genera(self):
        self.ui.btnCalcular.setEnabled(True)
        self.variables = self.ui.canVariable.value()
        #establecer el alto de filas
        self.ui.tabla.verticalHeader().setDefaultSectionSize(20)
        self.ui.tabla.verticalHeader().setVisible(False)
        self.ui.tablaView.verticalHeader().setDefaultSectionSize(20)
        self.ui.tablaView.verticalHeader().setVisible(False)
        
        self.Actividades = []
        
        #poner las letras del abecedario
        if(self.variables > 16):
            QMessageBox.information(None, ('Error'), ('El maximo de las variables es de 16'))
        else:
            self.ui.tabla.setRowCount(self.variables)
            self.ui.tablaView.setRowCount(self.variables)
            self.abec = list(map(chr, range(65, 91)))
            for i in range(self.variables):
                self.Actividades.append(self.abec[i])
                celda = QTableWidgetItem(self.abec[i])
                celda.setTextAlignment(Qt.AlignHCenter)
                self.ui.tabla.setItem(i, 0, celda)
                self.ui.tabla.setItem(i,2, QTableWidgetItem(" "))
                self.ui.tabla.setItem(i,1, QTableWidgetItem(" "))
            
            
        ##
    def calculo(self):
        try:
            self.Predecesores = []
        
            """pOR EL MOMENTO"""
            # Bucle: Obtiene los valores de la columna Predecesora
            for f in range(self.variables):
                valor = self.ui.tabla.item(f,2).text()
                self.Predecesores.append(valor)
                regex = re.search(r" |^[A-Z]{1}$|^[A-Z]{1}(,[A-Z]{1}){1,10}$", valor)
                if(regex == None):
                    raise Exception('Verifique que los predecesores sean correctos.\nEj: "A"  |  "A,B" .')

                prede = regex.group()
                listPrede = prede.split(sep=",")
                for value in range(len(listPrede)):
                    if(listPrede[value] != " " and not(listPrede[value] in self.Actividades)):
                        raise Exception(f'El predecesor "{listPrede[value]}" no corresponde a ninguna actividad existente')

                for j in range(3):
                    if self.ui.tabla.item(f,j+3) == None:
                        raise Exception('Revisar si falta un valor.\nEn: To, Tn, Tp')
          
            #abrimos ventana para la fecha
            self.dialog = Dialog()
            self.dialog.show()
            self.DijOij = self.calculaDijOij(self.variables)
            self.calculaTiempos(self.variables)
            self.dialog.ui.btnFecha.clicked.connect(self.fechaobten)
            
            
        except Exception as err:
            
            QMessageBox.information(None, ('Error'), str(err))

   
    # Método: Calcula el valor de Dij y Oij
    def calculaDijOij(self, filas):
        try:
            dij = []
            oij = []
            for f in range(filas):
                valores = []
                for c in range(3):
                    valor = int(self.ui.tabla.item(f,c+3).text())
                    valores.append(valor)
                
                valorDij = (valores[0] + (4 * valores[1]) + valores[2]) / 6
                valorDij = round(valorDij)
                dij.append(valorDij)
                
                valorOij = pow(((valores[2] - valores[0]) / 6), 2)
                valorOij = round(valorOij, 2)
                oij.append(valorOij)
                
                # Inserta los valores Dij en la tabla
                celdaDij = QTableWidgetItem(str(valorDij))
                celdaDij.setTextAlignment(Qt.AlignCenter)
                self.ui.tablaView.setItem(f, 0, celdaDij)
                
                # Inserta los valores Oij en la tabla
                celdaOij = QTableWidgetItem(str(valorOij))
                celdaOij.setTextAlignment(Qt.AlignCenter)
                self.ui.tablaView.setItem(f, 1, celdaOij)
                
            return dij, oij
        except Exception as err:
            QMessageBox.information(None, ('Error'), str(err))
    
    # Méctodo: Calcula los tiempo
    def calculaTiempos(self, filas):
        # Calcula e inserta los valores de Ti0 y Tj0
        self.Ti0 = []
        self.Tj0 = []
        self.Ti1 = []
        self.Tj1 = []
        for f in range(filas):
            validarPrece = []
            valorPrece = self.ui.tabla.item(f,2).text()
            
            if(valorPrece == " "):
                celdaTi0 = QTableWidgetItem(str(0))
                celdaTi0.setTextAlignment(Qt.AlignCenter)
                self.ui.tablaView.setItem(f, 2, celdaTi0)
                self.Ti0.append(0)
                
                celdaTj0 = QTableWidgetItem(str(self.DijOij[0][f]))
                celdaTj0.setTextAlignment(Qt.AlignCenter)
                self.ui.tablaView.setItem(f, 4, celdaTj0)
                self.Tj0.append(self.DijOij[0][f])
                
            else:
                listPrede = valorPrece.split(sep=",")
                for value in range(len(listPrede)):
                    indexFilaTc = self.Actividades.index(listPrede[value])
                    valorPreceTc = int(self.ui.tablaView.item(indexFilaTc,4).text())
                    validarPrece.append(valorPreceTc)
                
                valorMax = max(validarPrece)
                celdaTi0 = QTableWidgetItem(str(valorMax))
                celdaTi0.setTextAlignment(Qt.AlignCenter)
                self.ui.tablaView.setItem(f, 2, celdaTi0)
                self.Ti0.append(valorMax)
                
                celdaTj0 = QTableWidgetItem(str(valorMax + self.DijOij[0][f]))
                celdaTj0.setTextAlignment(Qt.AlignCenter)
                self.ui.tablaView.setItem(f, 4, celdaTj0)
                self.Tj0.append(valorMax + self.DijOij[0][f])
                
         # Calcula e inserta los valores de Ti1 y Tj1
        lastFilaAct = len(self.Actividades)-1
        validarLastAct = []
        for i in range(lastFilaAct, -1, -1):
            validarPreceLast = []
            valorPreceLast = self.ui.tabla.item(i,2).text()
            if(len(self.Actividades) == i+1):
                vMax = max(self.Tj0)
                celdaTj1 = QTableWidgetItem(str(vMax))
                celdaTj1.setTextAlignment(Qt.AlignCenter)
                self.ui.tablaView.setItem(i, 5, celdaTj1)
                self.Tj1.append(vMax)
                
                celdaTi1 = QTableWidgetItem(str(vMax - self.DijOij[0][i]))
                celdaTi1.setTextAlignment(Qt.AlignCenter)
                self.ui.tablaView.setItem(i, 3, celdaTi1)
                self.Ti1.append(vMax - self.DijOij[0][i])
                
                listPredeLast = valorPreceLast.split(sep=",")
                validarLastAct.append(listPredeLast)
            else:
                listPredeLast = valorPreceLast.split(sep=",")
                validarLastAct.append(listPredeLast)
                indexFilaLast = []
                for value in range(len(validarLastAct)):
                    if(self.Actividades[i] in validarLastAct[value]):
                        predecesor = ",".join(validarLastAct[value])
                        index = [indice for indice in range(len(self.Predecesores)) if self.Predecesores[indice] == predecesor]
                        
                        for ind in index:
                            if(not(ind in indexFilaLast)):
                                indexFilaLast.append(ind)
                
                if(len(indexFilaLast) == 0):
                    valorTj0 = int(self.ui.tablaView.item(i+1, 5).text())
                    celdaTj1 = QTableWidgetItem(str(valorTj0))
                    celdaTj1.setTextAlignment(Qt.AlignCenter)
                    self.ui.tablaView.setItem(i, 5, celdaTj1)
                    self.Tj1.append(valorTj0)
                    
                    celdaTi1 = QTableWidgetItem(str(valorTj0 - self.DijOij[0][i]))
                    celdaTi1.setTextAlignment(Qt.AlignCenter)
                    self.ui.tablaView.setItem(i, 3, celdaTi1)
                    self.Ti1.append(valorTj0 - self.DijOij[0][i])
                else:
                    valorPreceMin = []
                    for valor in indexFilaLast:
                        valorTj0 = int(self.ui.tablaView.item(valor,3).text())
                        valorPreceMin.append(valorTj0)
                    
                    valorMin = min(valorPreceMin)
                    celdaTj1 = QTableWidgetItem(str(valorMin))
                    celdaTj1.setTextAlignment(Qt.AlignCenter)
                    self.ui.tablaView.setItem(i, 5, celdaTj1)
                    self.Tj1.append(valorMin)
                    
                    celdaTi1 = QTableWidgetItem(str(valorMin - self.DijOij[0][i]))
                    celdaTi1.setTextAlignment(Qt.AlignCenter)
                    self.ui.tablaView.setItem(i, 3, celdaTi1)
                    self.Ti1.append(valorMin - self.DijOij[0][i])
                    
        # Ejecutamos el método para hallar las holguras
        self.calcularMtMl(filas)
    
    # Método: Genera los valores de los Margenes Totales y Libres
    def calcularMtMl(self, filas):
        self.MTij = []
        self.MLij = []
        tj1 = list(reversed(self.Tj1))
        ti0 = self.Ti0
        tj0 = self.Tj0
        dij = self.DijOij[0]
        
        for f in range(filas):
            mtij = (tj1[f] - ti0[f] - dij[f])
            celdaMTij = QTableWidgetItem(str(mtij))
            celdaMTij.setTextAlignment(Qt.AlignCenter)
            self.ui.tablaView.setItem(f, 6, celdaMTij)
            self.MTij.append(mtij)
            
            mlij = (tj0[f] - ti0[f] - dij[f])
            celdaMLij = QTableWidgetItem(str(mlij))
            celdaMLij.setTextAlignment(Qt.AlignCenter)
            self.ui.tablaView.setItem(f, 7, celdaMLij)
            self.MLij.append(mlij)
        

    # Método: Obtine los días no laborables
    def getDiasNoLab(self):
        self.diasNoLab = []
        
        if(self.dialog.ui.boxLunes.isChecked()):
            dia = "Monday"
            self.diasNoLab.append(dia)
            
        if(self.dialog.ui.boxMartes.isChecked()):
            dia = "Tuesday"
            self.diasNoLab.append(dia)
            
        if(self.dialog.ui.boxMiercoles.isChecked()):
            dia = "Wednesday"
            self.diasNoLab.append(dia)
            
        if(self.dialog.ui.boxJueves.isChecked()):
            dia = "Thursday"
            self.diasNoLab.append(dia)
            
        if(self.dialog.ui.boxViernes.isChecked()):
            dia = "Friday"
            self.diasNoLab.append(dia)
            
        if(self.dialog.ui.boxSabado.isChecked()):
            dia = "Saturday"
            self.diasNoLab.append(dia)
            
        if(self.dialog.ui.BoxDomingo.isChecked()):
            dia = "Sunday"
            self.diasNoLab.append(dia)
       
     # fehc
    def fechaobten(self):
        self.fechInicio = self.dialog.ui.Date.selectedDate().toPyDate()
        self.getDiasNoLab()
        self.generateDate(self.variables)

    #callcular lad fechas
    def calcuFecha(self, tiempo):
        self.fechaLab = self.fechInicio
        i = 0
        while(i < tiempo):
            if(i == 0):
                dia = self.fechInicio + timedelta(days=i)
            else:
                self.fechaLab = self.fechaLab + timedelta(days=1)
                diaActual = self.fechaLab.strftime("%A")
                if(diaActual in self.diasNoLab):
                    i -= 1
            i += 1

        return self.fechaLab
            
        
    # Método: Calcula e inserta las fechas
    def generateDate(self, filas):
        
        self.Ti1 = list(reversed(self.Ti1))
        self.Tj1 = list(reversed(self.Tj1))
        for f in range(filas):
            
            ti0 = self.Ti0[f]
            ti1 = self.Ti1[f]
            tj0 = self.Tj0[f]
            tj1 = self.Tj1[f]

            # Fecha Inicio Temprano
            fi0 = self.calcuFecha(ti0)
            diaStr = QTableWidgetItem(fi0.strftime("%d/%m/%Y"))
            diaStr.setTextAlignment(Qt.AlignCenter)
            self.ui.tablaView.setItem(f,8,diaStr)
            
            # Fecha Inicio Tardio
            fi1 = self.calcuFecha(ti1)
            diaStr = QTableWidgetItem(fi1.strftime("%d/%m/%Y"))
            diaStr.setTextAlignment(Qt.AlignCenter)
            self.ui.tablaView.setItem(f,9,diaStr)
            
            # Fecha Fin Temprano
            fj0 = self.calcuFecha(tj0)
            diaStr = QTableWidgetItem(fj0.strftime("%d/%m/%Y"))
            diaStr.setTextAlignment(Qt.AlignCenter)
            self.ui.tablaView.setItem(f,10,diaStr)
            
            # Fecha Fin Tardio
            fj1 = self.calcuFecha(tj1)
            diaStr = QTableWidgetItem(fj1.strftime("%d/%m/%Y"))
            diaStr.setTextAlignment(Qt.AlignCenter)
            self.ui.tablaView.setItem(f,11,diaStr)
            
        # Búcle: colorea las actividades críticas
        rutaCritica = [index for index in range(len(self.MTij)) if self.MTij[index] == 0]
        
        for ruta in rutaCritica:
            for g in range(6):
                self.ui.tabla.item(ruta,g).setBackground(QtGui.QColor(255, 60, 60))
            for k in range(12):
                self.ui.tablaView.item(ruta,k).setBackground(QtGui.QColor(255, 60, 60))
            
    

    #limpiar la tabla
    def limpia(self):
        self.ui.btnCalcular.setEnabled(False)
        self.ui.tabla.clearContents()
        self.ui.tabla.setRowCount(0)
        self.ui.tablaView.clearContents()
        self.ui.tablaView.setRowCount(0)

class Dialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(Dialog, self).__init__(*args, **kwargs)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)  
        self.setWindowTitle("Fecha")
        self.ui.btnFecha.clicked.connect(self.close)


######
######
###         SIMPLEX

class Simplex(QMainWindow):
    #Método constructor de la clase
    def __init__(self, ui):
        super(Simplex, self).__init__()
        self.ui = ui
        self.ui.btnResultado.clicked.connect(self.resultado)
        self.ui.btnGenerar.clicked.connect(self.genera2)
        self.ui.btnNuevo_2.clicked.connect(self.limpia)
        
        
    def resultado(self):
        c=[]
        A=[]
        b=[]
        un = [] 
        self.coluResu= 3
        rowResu= 4
        for i in range(self.ui.tablaVaria.columnCount()):
            x = self.ui.tablaVaria.item(0, i).text()
            c.append(0 - float(x))
            self.coluResu+=1
        for i in range(self.ui.tablaRestri.rowCount()):
            A.append([])
            un.append(0)
            self.coluResu+=1
            rowResu+=1
            for j in range(self.ui.canVariable_2.value()):
                x = self.ui.tablaRestri.item(i, j).text()
                A[i].append(float(x))
               


        for i in range(self.ui.tablaIgual.rowCount()):
            x=self.ui.tablaIgual.item(i, 0).text()
            b.append(float(x))

        # agregamos la matriz de identidad
        iden = np.identity(self.ui.canRestri.value())
        for i in range(self.ui.canRestri.value()):
            for j in range(self.ui.canRestri.value()):
                A[i] += [iden[i][j]]
        c += un

        final_cols = [row[:] + [x] for row, x in zip(A, b)]
        final_cols.append([ci for ci in c] + [0])
        final_rows=[]
        for i in range(len(final_cols[0])):
            final_rows.append([])
            for j in range(len(final_cols)):
                final_rows[i].append(final_cols[j][i])
        #
        const_names = ['X' + str(i) for i in range(1, self.ui.canVariable_2.value() + 1)]

        solutions=[]
        i = len(const_names) + 1
        while len(const_names) < len(final_cols[0]) - 1:
            const_names.append('X' + str(i))
            solutions.append('X' + str(i))
            i += 1
        solutions.append('  Z  ')
        const_names.append('Bi')
        #Enviamos a la funcion Maximizar
       # self.maximization(final_cols, final_rows, const_names, solutions)
        self.ventana2 = Ventana2(final_cols, final_rows, const_names, solutions, self)
        self.ventana2.show()
        # for i in range(c):

    def genera2(self):
        varia= self.ui.canVariable_2.value()
        restri = self.ui.canRestri.value()
        print(varia)
        self.ui.tablaVaria.setColumnCount(varia)
        self.ui.tablaVaria.verticalHeader().setVisible(False)
        

        self.ui.tablaRestri.setColumnCount(varia+1)
        self.ui.tablaRestri.setRowCount(restri)
        self.ui.tablaRestri.verticalHeader().setVisible(False)
        
        self.ui.tablaIgual.setColumnCount(1)
        self.ui.tablaIgual.setRowCount(restri)
        self.ui.tablaIgual.verticalHeader().setVisible(False)
        n= [] 
        for i in range(varia):
            n.append('X{}'.format(i+1))
        n.append('igual')
        self.ui.tablaVaria.setHorizontalHeaderLabels(n)
        self.ui.tablaRestri.setHorizontalHeaderLabels(n)
        self.ui.tablaIgual.setHorizontalHeaderLabels(('Igual',''))
        col = varia
        for i in range(self.ui.tablaRestri.rowCount()):
            self.ui.combo = QComboBox()
            self.ui.combo.setStyleSheet('background-color: #E1E1E1; color:#000')
            self.ui.combo.addItems(['<=','>='])
            self.ui.tablaRestri.setCellWidget(i,col,self.ui.combo)
        
    def limpia(self):
        self.ui.canVariable_2.clear()
        self.ui.canRestri.clear()
        self.ui.tablaVaria.clearContents()
        self.ui.tablaVaria.setRowCount(0)
        self.ui.tablaVaria.setColumnCount(0)
        self.ui.tablaRestri.clearContents()
        self.ui.tablaRestri.setRowCount(0)
        self.ui.tablaRestri.setColumnCount(0)
        self.ui.tablaIgual.clearContents()
        self.ui.tablaIgual.setRowCount(0)
        self.ui.tablaIgual.setColumnCount(0)
 
class Ventana2(QtWidgets.QMainWindow):
    #Método constructor de la clase
    def __init__(self, final_cols, final_rows, const_names, solutions, parent=None):

        #Iniciar el objeto QMainWindow
        super(Ventana2, self).__init__()
        #Cargar la configuración del archivo .ui en el objeto
        self.ui = Ui_ventana2()
        self.ui.setupUi(self)  
        self.setWindowTitle("Resultado")
        #self.ui.textTabla.setAlignment(QtCore.Qt.AlignCenter)
        self.parent = parent
        self.final_cols = final_cols
        self.final_rows = final_rows
        self.const_names = const_names
        self.solutions = solutions
        self.maximization()
        

    def maximization(self):
        decimals=3
        row_app = []
        last_col = self.final_cols[-1]
        min_last_row = min(last_col)
        min_manager = 1
        self.ui.textTabla.append("TABLA 1")
        try:
            final_pd = DataFrame(np.array(self.final_cols), columns=self.const_names, index=self.solutions)
            
            self.ui.textTabla.append(final_pd.to_html(classes='col_space:10 '))
        except:
           
            self.ui.textTabla.append('   '+str(self.const_names))
            i = 0
            for cols in self.final_cols:
                
                self.ui.textTabla.append(str(self.solutions[i])+ str(cols))
                i += 1
        count = 2
        pivot_element = 2
        while min_last_row < 0 < pivot_element != 1 and min_manager == 1 and count < 6:
            
            self.ui.textTabla.append("*********************************************************")
            last_col = self.final_cols[-1]
            last_row = self.final_rows[-1]
            min_last_row = min(last_col)
            index_of_min = last_col.index(min_last_row)
            pivot_row = self.final_rows[index_of_min]
            index_pivot_row = self.final_rows.index(pivot_row)
            row_div_val = []
            i = 0
            for _ in last_row[:-1]:
                try:
                    val = float(last_row[i] / pivot_row[i])
                    if val <= 0:
                        val = 10000000000
                    else:
                        val = val
                    row_div_val.append(val)
                except ZeroDivisionError:
                    val = 10000000000
                    row_div_val.append(val)
                i += 1
            min_div_val = min(row_div_val)
            index_min_div_val = row_div_val.index(min_div_val)
            pivot_element = pivot_row[index_min_div_val]
            pivot_col = self.final_cols[index_min_div_val]
            index_pivot_col = self.final_cols.index(pivot_col)
            row_app[:] = []
            for col in self.final_cols:
                if col is not pivot_col and col is not self.final_cols[-1]:
                    form = col[index_of_min] / pivot_element
                    final_val = np.array(pivot_col) * form
                    new_col = (np.round((np.array(col) - final_val), decimals)).tolist()
                    self.final_cols[self.final_cols.index(col)] = new_col

                elif col is pivot_col:
                    new_col = (np.round((np.array(col) / pivot_element), decimals)).tolist()
                    self.final_cols[self.final_cols.index(col)] = new_col
                else:
                    form = abs(col[index_of_min]) / pivot_element
                    final_val = np.array(pivot_col) * form
                    new_col = (np.round((np.array(col) + final_val), decimals)).tolist()
                    self.final_cols[self.final_cols.index(col)] = new_col
            self.final_rows[:] = []
            re_final_rows = np.array(self.final_cols).T.tolist()
            self.final_rows = self.final_rows + re_final_rows

            if min(row_div_val) != 10000000000:
                min_manager = 1
            else:
                min_manager = 0
            
            self.ui.textTabla.append('elemento pivote: %s' % pivot_element)
            
            self.ui.textTabla.append('columna de pivote: '+str(pivot_row))
            
            self.ui.textTabla.append('fila de pivote: '+str(pivot_col))
           
            self.ui.textTabla.append("\n")
            self.solutions[index_pivot_col] = self.const_names[index_pivot_row]

            self.ui.textTabla.append("TABLA %d" % count)
            try:
                final_pd = DataFrame(np.array(self.final_cols), columns=self.const_names, index=self.solutions)
                
                
                self.ui.textTabla.append(final_pd.to_html())
            except:
                
                self.ui.textTabla.append("TABLA %d" % count)
                
                self.ui.textTabla.append('   '+str(self.const_names))
                i = 0
                for cols in self.final_cols:
                    print(self.solutions[i], cols)
                    self.ui.textTabla.append(str(self.solutions[i])+str(cols))
                    i += 1
            count += 1
            last_col = self.final_cols[-1]
            last_row = self.final_rows[-1]
            min_last_row = min(last_col)
            index_of_min = last_col.index(min_last_row)
            pivot_row = self.final_rows[index_of_min]
            row_div_val = []
            i = 0
            for _ in last_row[:-1]:
                try:
                    val = float(last_row[i] / pivot_row[i])
                    if val <= 0:
                        val = 10000000000
                    else:
                        val = val
                    row_div_val.append(val)
                except ZeroDivisionError:
                    val = 10000000000
                    row_div_val.append(val)
                i += 1
            min_div_val = min(row_div_val)
            index_min_div_val = row_div_val.index(min_div_val)
            pivot_element = pivot_row[index_min_div_val]
            if pivot_element < 0:
                
                self.ui.textTabla.append('No Solución')
        self.ui.textTabla.append("\n")
        self.ui.textTabla.append('La solución óptima es Z = '+str(self.final_cols[len(self.solutions)-1][len(self.const_names)-1]))
        self.ui.textTabla.append("\n")
    




# Inicia la aplicación
if __name__ == '__main__':    
    app = QApplication([])
    mi_App = MainWindow()
    mi_App.show()
    sys.exit(app.exec_())