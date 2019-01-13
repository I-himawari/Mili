import yaml
import importlib
import argparse
import subprocess
from flask import Flask, render_template, request, redirect, url_for, Response
import copy

parser = argparse.ArgumentParser(description='')

parser.add_argument('--note', '-n', type=str, default='example.yml', help='')
parser.add_argument('--name', '-a', type=str, help='')
parser.add_argument('--server', '-s', type=int)


class Mili(object):
    
    def __init__(self, args):

        self.args = args
        self.load_note()

        if self.args.server:
            self.server()
        else:
            self.cli()

    def load_note(self):
        with open(self.args.note, "r+") as f:
            self.note = yaml.load(f)

    def server(self):
        app = Flask(__name__)
                
        @app.route('/')
        def index():
            self.load_note()
            flask_note = copy.deepcopy(self.note)
            for i, v in enumerate(flask_note):
                if "python" in v and "args" in v:
                    flask_note[i]["args"] = self.create_args_list(v["args"])
            return render_template('index.html', note=flask_note)

        @app.route('/function/<int:func_number>')
        def call_script(func_number):
            print("func_number")
            print(self.note[func_number-1])
            return Response("{'a':'b'}", status=201, mimetype='application/json')

        app.debug = True # デバッグモード有効化
        app.run(host='0.0.0.0') # どこからでもアクセス可能に

    # コマンドラインから呼ばれた時、一括実行する。
    def cli(self):
        self.called_class_list = list()
        if self.args.name:
            self.note = [v for v in self.note if v["name"] == self.args.name]

        for d in self.note:
            self.call_method(d)

    # メソッド（noteの1つ区切りのもの）が呼ばれた時に動かす。
    def call_method(self, d):
        print(d["name"])
        if "python" in d:
            m = importlib.import_module(d['python']) 
            if "class" in d:
                if d["class"] not in self.called_class_list:
                    self.called_class_list.append(d["class"])
                    args = self.delete_desc(d['class_args'])
                    eval("_%s = %s" % (d['class'], d["class"]))(**args)

                if "function" in d:
                    method_name = "_%s.m.%s" % (d["class"], d["function"])
            
            else:
                method_name = "m.%s" % d["function"]

            if "function" in d:
                args = self.delete_desc(d['args'])
                eval(method_name)(**args)

        elif "bash" in d:
            subprocess.call(d['bash'], shell=True)
    
    # 変数引数内の_desc_（説明用引数）を削除したものを返す。
    def delete_desc(self, args):
        r = dict()
        for k, v in args.items():
            if k.find("_desc_") != 0:
                r[k] = v
            
        return r

    # 変数リストを作成する。
    # args_name, args_param, args_desc
    def create_args_list(self, args):
        args_list = list()
        for v in self.delete_desc(args).items():
            args_args = list()
            args_args.append(v[0])
            args_args.append(v[1])
            # _desc_が文字列に含まれている条件として、文字列長が6以上と定義。次に一致チェックを行っている。
            # 書式固定故に、文字列より特定のものだけ抽出するのに正規表現使わなくても良さそうなので、ごりごり。
            desc = [w for w in args.items() 
                    if len(w[0]) >= 6 and w[0][6:len(w[0])] == v[0] and w[0].find("_desc_") == 0]  
            if len(desc) != 0:
                args_args.append(desc[0][1])
            else:
                args_args.append(None)
        
            args_list.append(args_args)

        return args_list

def main():
    Mili(parser.parse_args())