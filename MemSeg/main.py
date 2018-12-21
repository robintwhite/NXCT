# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSlot, pyqtSignal
import traceback, sys
import os
import gui
from skimage.external import tifffile
import numpy as np
import MemSeg


class ImageError(Exception):
    """ Raised when no image is specified """
    pass

class NoFileError(Exception):
    """ Raised when image can't be found """
    pass

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int, str)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here;
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


#All functions defined in App class
class MemSegApp(QtWidgets.QDialog, gui.Ui_Dialog):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)
        self.setupUi(self)

        #Initialize click objects
        self.Start.clicked.connect(self.run_worker)
        self.Cancel.clicked.connect(self.quitClicked)
        self.Help.clicked.connect(self.HelpApp) #See code below for popup
        self.Input_dir.clicked.connect(self.openFileNameDialog) #See code below for popup
        self.progressBar.setValue(0)
        self.An_check.stateChanged.connect(self.state_changed_boundary)
        self.Cat_check.stateChanged.connect(self.state_changed_boundary)
        self.DynSlcRng.setEnabled(False)
        self.Num_steps.setEnabled(False)
        self.FullDynSlc_Check.stateChanged.connect(self.state_changed_dynslc)
        self.Mask_check.stateChanged.connect(self.state_changed_mask)

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        self.counter = 0

    def state_changed_boundary(self):
        if self.An_check.isChecked() and self.Cat_check.isChecked():
            self.GS_in.setEnabled(True)
            self.Slc_loc.setEnabled(True)
            self.Mask_check.setEnabled(True)
            self.FullDynSlc_Check.setEnabled(True)
            if self.FullDynSlc_Check.isChecked():
                self.DynSlcRng.setEnabled(True)
                self.Num_steps.setEnabled(True)
            else:
                self.DynSlcRng.setEnabled(False)
                self.Num_steps.setEnabled(False)
        else:
            self.GS_in.setEnabled(False)
            self.Slc_loc.setEnabled(False)
            self.Mask_check.setEnabled(False)
            self.FullDynSlc_Check.setEnabled(False)
            self.DynSlcRng.setEnabled(False)
            self.Num_steps.setEnabled(False)

    def state_changed_mask(self):
        if not self.Mask_check.isChecked():
            self.GS_in.setEnabled(False)
            self.Slc_loc.setEnabled(False)
        else:
            self.GS_in.setEnabled(True)
            self.Slc_loc.setEnabled(True)

    def state_changed_dynslc(self):
        if not self.FullDynSlc_Check.isChecked():
            self.DynSlcRng.setEnabled(False)
            self.Num_steps.setEnabled(False)
        else:
            self.DynSlcRng.setEnabled(True)
            self.Num_steps.setEnabled(True)

    def run_worker(self):
        # Pass the function to execute
        worker = Worker(self.GetMem) # Any other args, kwargs are passed to the run function
        # Execute
        self.threadpool.start(worker)
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)

    def progress_fn(self, n, s):
        print("%d%% done" % n)
        self.progressBar.setValue(n)
        if s != '':
            self.Out.addItem("{0}".format(s))

    def print_output(self, s):
        print(s)

    def thread_complete(self):
        print("THREAD COMPLETE!")

    def GetMem(self, progress_callback):
        self.Start.setEnabled(False)
        progress_callback.emit(0, 'Running...')
        self.MPL_.canvas.fig.clf()

        #Analysis to be run when start analysis button pressed
        input_dir = self.Dir_input.text()
        im_list = []
        boundary_list = []
        elect_list = []
        filter_size = self.Filter_size.value()
        slc_loc = self.Slc_loc.value()
        option = self.Mask_check.isChecked()
        dyn_slc_full_option = self.FullDynSlc_Check.isChecked()

        try:
            if self.An_check.isChecked() or self.Cat_check.isChecked():
                if self.An_check.isChecked():
                    im_list.append('CathodeRemoved.tif')
                    elect_list.append('anode')
                    if self.An_T.isChecked():
                        boundary_list.append('bottom')
                    else:
                        boundary_list.append('top')

                if self.Cat_check.isChecked():
                    im_list.append('AnodeRemoved.tif')
                    elect_list.append('cathode')
                    if self.Cat_T.isChecked():
                        boundary_list.append('bottom')
                    else:
                        boundary_list.append('top')
            else:
                raise ImageError

        except ImageError:
            progress_callback.emit(0, 'Please select at least one electrode boundary')
            self.Start.setEnabled(True)
            return 'Error'


        boundaries = MemSeg.GetBoundary(progress_callback, input_dir, im_list, elect_list, boundary_list, filter_size)

        progress_callback.emit(30, '')

        for boundary in boundaries:
            tifffile.imsave(os.path.join(input_dir,'interp_'+boundary+'_boundary.tif'), boundaries[boundary])


        try:
            if len(boundary_list) == 2 and boundaries:
                mem_mask, slc_mask = MemSeg.BoundaryFill(progress_callback, elect_list, boundary_list, boundaries, slc_loc)

                if len(mem_mask)!= 0:
                    sum_vec = np.sum(mem_mask/255, axis=0, dtype = int)
                    tifffile.imsave(os.path.join(input_dir,'Membrane_fill.tif'), mem_mask)
                    tifffile.imsave(os.path.join(input_dir,'Mem_PixelThickness.tif'), sum_vec)

                    mean_T = np.mean(sum_vec)
                    std_T = np.std(sum_vec)
                    self.Out.addItem("{}{:0.2f}".format("Mean thickness (pix): ", mean_T))
                    self.Out.addItem("{}{:0.2f}".format("Standard dev. (pix): ", std_T))

                    self.MPL_.canvas.ax = self.MPL_.canvas.fig.add_subplot(111)
                    im = self.MPL_.canvas.ax.imshow(sum_vec)
                    self.MPL_.canvas.ax.set_title('Pixel Thickness')
                    self.MPL_.canvas.fig.colorbar(im, ax=self.MPL_.canvas.ax)
                    self.MPL_.canvas.ax.set_axis_off()
                    self.MPL_.canvas.fig.tight_layout()
                    self.MPL_.canvas.draw()

                    gs_im = []
                    gs_im_name = self.GS_in.text()

                    if option:
                        try:
                            gs_im = tifffile.imread(os.path.join(input_dir,gs_im_name))
                            gs_mask, gs_slc_mask = MemSeg.MaskMem(progress_callback, mem_mask, slc_mask, input_dir, gs_im)
                            gs_slc_im = np.sum(gs_slc_mask, axis=0, dtype = np.uint16)
                            tifffile.imsave(os.path.join(input_dir,'MembraneMask.tif'), gs_mask.astype(np.uint16))
                            tifffile.imsave(os.path.join(input_dir,'MembraneDynamicSlc{:.4}.tif'.format(str(slc_loc).replace('.', 'p'))), gs_slc_im)
                            gs_mask = None
                            gs_slc_im = None
                        except (FileNotFoundError):
                            progress_callback.emit(0, 'No greyscale image found in directory')

                    if dyn_slc_full_option:
                        slc_range = self.DynSlcRng.text()
                        dyn_range = [float(x.strip()) for x in slc_range.split(',')]
                        dyn_name = slc_range.replace(',', '')
                        dyn_name = dyn_name.replace('.','')
                        dyn_name = dyn_name.replace(' ','')
                        num_steps = self.Num_steps.value()

                        if len(gs_im)==0:
                            gs_im = tifffile.imread(os.path.join(input_dir,gs_im_name))
                            full_dyn_slc = MemSeg.DynamicSlice(progress_callback, elect_list, boundary_list, boundaries, gs_im, sum_vec, num_steps, dyn_range)
                            tifffile.imsave(os.path.join(input_dir,'MembraneDynSlc_{}.tif'.format(dyn_name)), full_dyn_slc.astype(np.uint16))
                        else:
                            try:
                                full_dyn_slc = MemSeg.DynamicSlice(progress_callback, elect_list, boundary_list, boundaries, gs_im, sum_vec, num_steps, dyn_range)
                                tifffile.imsave(os.path.join(input_dir,'MembraneDynSlc_{}.tif'.format(dyn_name)), full_dyn_slc.astype(np.uint16))
                            except (FileNotFoundError):
                                progress_callback.emit(0, 'No greyscale image found in directory')

                    progress_callback.emit(100, 'Done.')

                    self.Start.setEnabled(True)
                    return 'Done.'

                else:
                    progress_callback.emit(0, 'Error when filling boundary')
                    self.Start.setEnabled(True)
                    raise NoFileError
                    return 'Error'

            elif boundaries:
                progress_callback.emit(100, 'Done')
                self.Start.setEnabled(True)
                return 'Done.'

            else:
                raise NoFileError

        except NoFileError:
            progress_callback.emit(0, 'Please input a valid image')
            self.Start.setEnabled(True)
            return 'Error'


    def HelpApp(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setWindowTitle(self.tr("Help"))
        msgBox.setText("<br>"+
                       "<b>{0}</b><br><br>".format('MemSeg') +
                       "{0}<br>{1}<br><br>".format('Given segmented electrodes, obtain boundary and fill','to isolate membrane from image stack')+
                       "{0}<br>".format('For full tutorial please see <a href="https://github.com/robintwhite/NXCT/tree/master/MemSeg">MemSeg</a> docs')+

                       "&copy;2018 Robin White<br><br>")
        msgBox.setInformativeText("Still a work in progress")

        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)

        msgBox.exec_()

    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName = QtWidgets.QFileDialog.getExistingDirectory(self,"Select input directory")
        if fileName:
            self.Dir_input.setText(fileName)
            for file in os.listdir(fileName):
                if file.endswith("GS.tif"):
                    self.GS_in.setText(file)
        return fileName

    def quitClicked(self):
        sys.exit()


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = MemSegApp()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
