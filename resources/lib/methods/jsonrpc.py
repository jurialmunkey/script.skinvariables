# -*- coding: utf-8 -*-
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
from xbmcgui import Dialog
from jurialmunkey.ftools import cached_property
from jurialmunkey.futils import FileUtils as BaseFileUtils, validify_filename
from jurialmunkey.jsnrpc import get_jsonrpc as request_jsonrpc


class FileUtils(BaseFileUtils):
    addondata = 'special://profile/addon_data/script.skinvariables/'


class JSONRPCRequest:
    def __init__(self, method, params):
        self.method = method
        self.params = params
        self.result = self.get_result()

    def get_result(self):
        return request_jsonrpc(self.method, self.params)

    @cached_property
    def filename(self):
        return self.get_filename()

    def get_filename(self):
        params = '_'.join(f'{key}-{value}' for key, value in self.params.items())
        return validify_filename(f'{self.method}_{params}.json')

    @cached_property
    def record(self):
        return self.get_record()

    def get_record(self):
        return {'method': self.method, 'params': self.params, 'result': self.result}

    def show(self):
        Dialog().textviewer(f'GET {self.method}', f'PARAMS\n{self.params}\n\nRESULT\n{self.result}')

    def save(self):
        FileUtils().dumps_to_file(self.record, 'log_request', self.filename)


def get_jsonrpc(get_jsonrpc, textviewer=False, filewrite=True, **kwargs):
    request = JSONRPCRequest(get_jsonrpc, kwargs)
    if textviewer:
        request.show()
    if filewrite:
        request.save()
