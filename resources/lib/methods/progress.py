# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import xbmc
import xbmcgui
from jurialmunkey.parser import boolean


class ProgressDialogRunner:
    dialog_class = xbmcgui.DialogProgress

    def __init__(self, heading, message, polling, message_info, progress_info, timeout, max_value):
        self.dialog = self.dialog_class()
        self.heading = heading
        self.message = message
        self.polling = float(polling)
        self.remaining = int(timeout)
        self.maximum = int(max_value)
        self.message_info = message_info
        self.progress_info = progress_info
        self.value = 0

    @property
    def percent(self):
        return self.get_percent()

    def get_percent(self):
        return int(self.value / self.maximum * 100)

    def update(self):
        self.value += 1
        self.remaining -= 1
        if self.progress_info:
            self.value = int(xbmc.getInfoLabel(self.progress_info) or 0)
        if self.message_info:
            self.message = str(xbmc.getInfoLabel(self.message_info) or '')
        self.dialog.update(self.percent, message=self.message)

    def run(self):
        monitor = xbmc.Monitor()
        self.dialog.create(self.heading, self.message)
        try:
            while self.value < self.maximum and self.remaining > 0 and not monitor.abortRequested():
                self.update()
                monitor.waitForAbort(self.polling)
        finally:
            self.dialog.close()


class BackgroundProgressDialogRunner(ProgressDialogRunner):
    dialog_class = xbmcgui.DialogProgressBG


def run_progressdialog(
    run_progressdialog,
    background=False,
    heading='',
    message='',
    polling='0.1',
    message_info='',
    progress_info='',
    timeout='200',
    max_value='100',
    **kwargs,
):
    dialog_class = BackgroundProgressDialogRunner if boolean(background) else ProgressDialogRunner
    dialog_class(heading, message, polling, message_info, progress_info, timeout, max_value).run()
